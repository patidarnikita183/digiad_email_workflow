"""
expiry_worker.py

Handles the FINAL EXPIRY flow for users (Isolated Lifecycle Engine).

State Machine Sequence (expiry_sequence_step):
  0 → Nothing sent
  1 → Pre-expiry mail 1 sent
  2 → Pre-expiry mail 2 sent
  3 → Expired mail sent (final)

Timing from .env:
  PRE_EXPIRY_MAIL_1_MINUTES
  PRE_EXPIRY_MAIL_2_MINUTES
  EXPIRY_CHECK_WINDOW_MINUTES
  EXPIRY_MIN_GAP_MINUTES
"""

import os
import sys
import time
import requests
import psycopg2

# Add parent directory to sys.path so 'builders' module can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
from workers.base_worker import get_db_connection, run_with_pool, run_cycle_with_timeout, post_with_retry

load_dotenv()

EMAIL_STATUS_TABLE         = os.getenv("EMAIL_STATUS_TABLE", "email_status_demo")
USERS_TABLE                = os.getenv("USERS_TABLE", "users_demo")
USER_SUBSCRIPTIONS_TABLE   = os.getenv("USER_SUBSCRIPTIONS_TABLE", "user_subscriptions1_demo")

# Timing (minutes)
PRE_EXPIRY_MAIL_1_MINUTES = int(os.getenv("PRE_EXPIRY_MAIL_1_MINUTES", "1440")) # prod Default: 1 day = 1440
PRE_EXPIRY_MAIL_2_MINUTES = int(os.getenv("PRE_EXPIRY_MAIL_2_MINUTES", "120"))  # prod Default: 2 hours = 120
EXPIRY_CHECK_WINDOW_MINUTES = int(os.getenv("EXPIRY_CHECK_WINDOW_MINUTES", 20))
EXPIRY_MIN_GAP_MINUTES = int(os.getenv("EXPIRY_MIN_GAP_MINUTES", "5"))

# Templates
TEMPLATE_CREDITS_EXPIRING_SOON = os.getenv("TEMPLATE_CREDITS_EXPIRING_SOON", "EXPIRY_REMINDER_24H.hbs")
TEMPLATE_1DAY_BEFORE_EXPIRY    = os.getenv("TEMPLATE_1DAY_BEFORE_EXPIRY", "EXPIRY_REMINDER_1H.hbs")
TEMPLATE_CREDITS_EXPIRED       = os.getenv("TEMPLATE_CREDITS_EXPIRED", "EXPIRED_NOTIFICATION.hbs")

SUPPORT_MAIL = os.getenv("SUPPORT_MAIL", "support@digiad.ai")
API_URL = os.getenv("SEND_EMAIL_API_URL", "http://localhost:5000/send_email")

import math

def format_expiry_time(total_seconds: float) -> str:
    total_seconds = int(total_seconds)

    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24

    if days >= 1:
        remaining_hours = hours % 24
        return f"{days} day{'s' if days > 1 else ''} {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"

    if hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''}"

    return f"{minutes} minute{'s' if minutes > 1 else ''}"

def send_email(user, template, email_type, subject, extra_context=None):
    email = user["email"]
    name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
    end_date = user["subscription_end_date"]
    expiry_date = end_date.strftime("%Y-%m-%d %H:%M") if end_date else "N/A"
    # in hours
    hours_to_expiry = (end_date - datetime.now()).total_seconds() / 3600 if end_date else None
    hours_to_expiry_str = format_expiry_time((end_date - datetime.now()).total_seconds()) if hours_to_expiry is not None else "N/A"
    context = {
        "FirstName": name,
        # 'expiryTimeframe': f"{expiry_date}",
        'expiryTimeframe': hours_to_expiry_str,
        "supportMail": SUPPORT_MAIL,
        "renewLink": os.getenv("RENEW_LINK", "https://digiad.ai/renew"),
        "pricingLink": os.getenv("PRICING_LINK", "https://digiad.ai/pricing"),
        "unsubscribeLink": f"{os.getenv('UNSUBSCRIBE_LINK_BASE', 'https://digiad.ai/unsubscribe?email=')}{email}",
    }
    if extra_context:
        context.update(extra_context)

    payload = {
        "to": email,
        "from": SUPPORT_MAIL,
        "subject": subject,
        "template": template,
        "email_type": email_type,
        "email_id": email,
        "context": context,
    }

    try:
        resp = post_with_retry(API_URL, payload)
        if resp.status_code == 200:
            print(f"  ✅ [{email_type}] → {email}")
            return True
        print(f"  ❌ [{email_type}] → {email}: {resp.text}")
        return False
    except Exception as e:
        print(f"  ❌ Request error [{email_type}] → {email}: {e}")
        return False


def advance_expiry_sequence(user_id, current_step, next_step, email_type, is_expired=False):
    """
    Atomically update the email_status table sequence step.
    Returns True if update succeeded, False if someone else modified it.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            now = datetime.now()
            
            # Atomic state update
            cur.execute(
                f"""
                UPDATE {EMAIL_STATUS_TABLE}
                SET expiry_sequence_step     = %s,
                    last_expiry_mail_type    = %s,
                    last_expiry_mail_sent_at = %s,
                    updated_at               = %s
                    {", is_unsubscribed = TRUE, not_interested_reason = 'expired_no_engagement'" if is_expired else ""}
                WHERE user_id = %s
                  AND expiry_sequence_step = %s
                """,
                (next_step, email_type, now, now, user_id, current_step),
            )
            rows_updated = cur.rowcount
            
            if is_expired and rows_updated:
                # Also mark subscription as expired
                cur.execute(
                    f"""
                    UPDATE {USER_SUBSCRIPTIONS_TABLE}
                    SET status = 'expired',
                        updated_at = %s
                    WHERE user_id = %s AND status = 'active'
                    """,
                    (now, user_id)
                )
            
            conn.commit()
            return rows_updated == 1
    except Exception as e:
        print(f"  ⚠️  DB advance sequence failed: {e}")
        return False
    finally:
        conn.close()


def process_single_user(user):
    user_id = user["user_id"]
    email = user["email"]
    sequence_step = user["expiry_sequence_step"]
    last_sent = user["last_expiry_mail_sent_at"]
    expiry_date = user["subscription_end_date"]
    
    now = datetime.now()
    if expiry_date and hasattr(expiry_date, "tzinfo") and expiry_date.tzinfo:
        expiry_date = expiry_date.replace(tzinfo=None)
    if last_sent and hasattr(last_sent, "tzinfo") and last_sent.tzinfo:
        last_sent = last_sent.replace(tzinfo=None)

    # Re-evaluate live DB state constraints per requirement #5
    if user["sub_status"] != 'active':
        return # Stop immediately if plan deactivated
    if user["is_unsubscribed"]:
        return # Stop immediately if user unsubscribed

    if expiry_date is None:
        return

    # Check minimum gap to prevent rapid re-sending
    if last_sent:
        minutes_since_last = (now - last_sent).total_seconds() / 60
        if minutes_since_last < EXPIRY_MIN_GAP_MINUTES:
            print(f"  ⏳ {email}: Waiting for min gap ({minutes_since_last:.1f}m < {EXPIRY_MIN_GAP_MINUTES}m)")
            return

    time_to_expiry = expiry_date - now
    threshold_mail1 = timedelta(minutes=PRE_EXPIRY_MAIL_1_MINUTES)
    threshold_mail2 = timedelta(minutes=PRE_EXPIRY_MAIL_2_MINUTES)

    # CASE A — Expired (Immediate kill switch, overrides sequence)
    if time_to_expiry.total_seconds() <= 0:
        if sequence_step < 3:
            if send_email(user, TEMPLATE_CREDITS_EXPIRED, "expired", "Your DigiAd credits and plan have expired"):
                advance_expiry_sequence(user_id, sequence_step, 3, "expired", is_expired=True)
                print(f"  🚀 {email}: Expired -> Sequence = 3")
        return

    # CASE B — Within PRE_MAIL_1 window, needs Mail 1
    if sequence_step == 0 and time_to_expiry <= threshold_mail1:
        if send_email(user, TEMPLATE_CREDITS_EXPIRING_SOON, "pre_expiry_mail_1",
                      "Your DigiAd credits are expiring soon!",
                      {"expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M")}):
            advance_expiry_sequence(user_id, 0, 1, "pre_expiry_mail_1")
            print(f"  🚀 {email}: Mail 1 -> Sequence = 1")
        return

    # CASE C — Within PRE_MAIL_2 window, needs Mail 2
    if sequence_step == 1 and time_to_expiry <= threshold_mail2:
        if send_email(user, TEMPLATE_1DAY_BEFORE_EXPIRY, "pre_expiry_mail_2", 
                      "Only a short time left – renew your DigiAd plan!",
                      {"expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M")}):
            advance_expiry_sequence(user_id, 1, 2, "pre_expiry_mail_2")
            print(f"  🚀 {email}: Mail 2 -> Sequence = 2")
        return


def process_expiry_flow():
    print(f"\n{'='*60}")
    print(f"Expiry Flow Worker (Isolated)  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Selection Criteria per requirement
            query = f"""
                SELECT
                    es.user_id, 
                    es.is_unsubscribed, 
                    es.expiry_sequence_step,
                    es.last_expiry_mail_sent_at,
                    u.email, 
                    u.first_name, 
                    u.last_name,
                    s.status AS sub_status,
                    s.end_date AS subscription_end_date
                FROM {EMAIL_STATUS_TABLE} es
                JOIN {USERS_TABLE} u
                    ON u.user_id = es.user_id
                JOIN {USER_SUBSCRIPTIONS_TABLE} s
                    ON s.user_id = es.user_id
                AND s.status = 'active'
                AND s.deleted_at IS NULL
                AND u.deleted_at IS NULL
                AND es.auto_status is False
                WHERE es.is_unsubscribed = FALSE
                AND u.deleted_at IS NULL
                AND s.end_date IS NOT NULL
                AND es.expiry_sequence_step < 3
                
                """
            cur.execute(query)
            candidates = cur.fetchall()

        # Handle renewal reset logic per Requirement 5
        to_process = []
        for c in candidates:
            # If end_date drifted entirely beyond the 3 day window, and sequence > 0, they renewed.
            end_date = c["subscription_end_date"]
            if hasattr(end_date, "tzinfo") and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)
            
            time_to_exp = end_date - datetime.now()
            
            # Reset sequence if user renewed
            if time_to_exp > timedelta(minutes=PRE_EXPIRY_MAIL_1_MINUTES) and c["expiry_sequence_step"] > 0:
                print(f"  🔄 {c['email']}: User renewed! Resetting sequence to 0.")
                reset_sequence(c["user_id"])
            # Only process users reasonably close to the first threshold to save CPU
            # Add a buffer so we pick them up exactly on time
            elif time_to_exp <= timedelta(minutes=PRE_EXPIRY_MAIL_1_MINUTES + 10):
                to_process.append(c)

        print(f"Found {len(to_process)} candidate(s) in delivery window.")

        run_with_pool(to_process, process_single_user)

    except Exception as e:
        print(f"Worker error: {e}")
    finally:
        conn.close()

def reset_sequence(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {EMAIL_STATUS_TABLE}
                SET expiry_sequence_step = 0,
                    last_expiry_mail_type = NULL,
                    last_expiry_mail_sent_at = NULL,
                    updated_at = %s
                WHERE user_id = %s
                """,
                (datetime.now(), user_id)
            )
            conn.commit()
    except Exception as e:
        print(f"Failed to reset sequence: {e}")
    finally:
        conn.close()

def run_worker():
    print("Expiry Flow Worker Started (Isolated Lifecycle Engine)")
    print(f"  Mail 1 threshold : {PRE_EXPIRY_MAIL_1_MINUTES}m (prod: 4320m)")
    print(f"  Mail 2 threshold : {PRE_EXPIRY_MAIL_2_MINUTES}m (prod: 1440m)")
    print(f"  Min gap          : {EXPIRY_MIN_GAP_MINUTES}m")
    print(f"  Check interval   : {EXPIRY_CHECK_WINDOW_MINUTES}m\n")

    while True:
        try:
            run_cycle_with_timeout(process_expiry_flow, "expiry_worker")
        except Exception as e:
            print(f"Main loop error: {e}")
        print(f"Sleeping {60}s...\n")
        time.sleep(60)

if __name__ == "__main__":
    run_worker()
