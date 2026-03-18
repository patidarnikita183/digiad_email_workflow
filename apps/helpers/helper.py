# app.py
 # registration-confirmation
        # nikitapatidar957@gmail.com
        # activate-user
        # patidarnikita183@gmail.com
# import uuid
from mail.email_service import DomainEmailService
# from config import Config
from datetime import datetime, timedelta
from datetime import datetime, timedelta
import os
import json
import threading
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from database.db import get_db_connection



email_service = DomainEmailService()
# config = Config()

from pybars import Compiler

# -------------------------------------------------------------------
# DB CONFIG / HELPERS
# -------------------------------------------------------------------

load_dotenv()

# ── Worker Test Logger ──────────────────────────────────────────────────────
_EMAIL_TEST_MODE = os.getenv("EMAIL_TEST_MODE", "false").lower() == "true"
_LOG_PATH = os.getenv("WORKER_TEST_LOG", "logs/worker_test_log.jsonl")
_log_lock = threading.Lock()

def append_worker_log(entry: dict):
    """Append one JSON line to the worker test log (thread-safe, no-op if test mode off)."""
    if not _EMAIL_TEST_MODE:
        return
    try:
        os.makedirs(os.path.dirname(os.path.abspath(_LOG_PATH)), exist_ok=True)
        with _log_lock:
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception as log_err:
        print(f"[worker_log] Failed to write log: {log_err}")

USERS_TABLE = os.getenv("USERS_TABLE", "users_demo")
USER_SUBSCRIPTIONS_TABLE = os.getenv("USER_SUBSCRIPTIONS_TABLE", "user_subscriptions1_demo")
USER_FEATURE_CREDITS_TABLE = os.getenv("USER_FEATURE_CREDITS_TABLE", "user_feature_credits_demo")
EMAIL_STATUS_TABLE = os.getenv("EMAIL_STATUS_TABLE", "email_status_demo")
EMAIL_HISTORY_TABLE = os.getenv("EMAIL_HISTORY_TABLE", "email_history_demo")
GLOBAL_EMAIL_API_HISTORY_TABLE = os.getenv(
    "GLOBAL_EMAIL_API_HISTORY_TABLE", "global_email_api_history"
)




TEMPLATE_ACTIVATION = os.getenv("TEMPLATE_ACTIVATION", "activate-user")
TEMPLATE_WELCOME = os.getenv("TEMPLATE_WELCOME", "registration-confirmation")

def get_user_by_email(conn, email):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Fetch user_id and subscription/credits info if available
        # We join to get the latest subscription/credits if needed, or just fetch user_id for now
        # simple fetch for user_id and email
        cursor.execute(
            f"SELECT user_id, email, status FROM {USERS_TABLE} WHERE email = %s LIMIT 1;",
            (email,),
        )
        return cursor.fetchone()

def derive_stage_from_email_type(email_type: str):
    et = (email_type or "").lower()
    if et == "activation":
        return "send_activate"
    if et == "activation_reminder":
        return "send_activate"
    if et == "welcome":
        return "welcome_sent"
    if et == "login_reminder":
        return "welcome_sent"
    
    return None

def track_email_event(user_id, email_type, template_name=None, metadata=None, email_id=None):
    """
    Updates email_status and inserts into email_history.
    """
    print("Tracking email event:", {
        "user_id": user_id,
        "email_type": email_type,
        "template_name": template_name,
        "metadata": metadata,
        "email_id": email_id
    })
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. Determine new stage
                new_stage = derive_stage_from_email_type(email_type)
                
                # 2. Update EMAIL_STATUS_TABLE
                cursor.execute(f"SELECT * FROM {EMAIL_STATUS_TABLE} WHERE user_id = %s LIMIT 1", (user_id,))
                existing_status = cursor.fetchone()
                
                now_ts = datetime.utcnow()
                
                if existing_status:
                    # Update
                    update_query = f"""
                        UPDATE {EMAIL_STATUS_TABLE}
                        SET 
                            last_email_type = %s,
                            last_email_sent_at = %s,
                            updated_at = %s,
                            email_id = %s
                    """
                    params = [email_type, now_ts, now_ts, email_id]
                    
                    if new_stage:
                        update_query += ", current_stage = %s"
                        params.append(new_stage)
                    
                    # Increment counters based on email_type
                    if email_type == 'activation_reminder':
                        update_query += ", activation_reminder_count = activation_reminder_count + 1"
                    elif email_type == 'login_reminder':
                        update_query += ", login_reminder_count = login_reminder_count + 1"

                    update_query += " WHERE user_id = %s RETURNING activation_reminder_count, login_reminder_count"
                    params.append(user_id)
                    
                    cursor.execute(update_query, tuple(params))
                    updated_row = cursor.fetchone()
                    
                    activation_count = updated_row.get('activation_reminder_count', 0) if updated_row else 0
                    login_count = updated_row.get('login_reminder_count', 0) if updated_row else 0
                else:
                    try:
                        print("enter into else part of track events")
                        # Insert
                        cursor.execute(
                            f"""
                            INSERT INTO {EMAIL_STATUS_TABLE} (
                                user_id, 
                                current_stage, 
                                last_email_type, 
                                last_email_sent_at, 
                                email_id,
                                created_at, 
                                updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                user_id, 
                                new_stage or 'send_activate', 
                                email_type, 
                                now_ts,
                                email_id,
                                now_ts, 
                                now_ts
                            )
                        )
                        print("cursor", cursor)
                        activation_count = 0
                        login_count = 0
                        print("table in {EMAIL_STATUS_TABLE} is updated for user_id:", user_id,EMAIL_STATUS_TABLE)
                        print("inserted into email_status for user_id:", user_id)
                    except Exception as insert_err:
                        print(f"Failed to insert into {EMAIL_STATUS_TABLE}: {insert_err}")
                        activation_count = 0
                        login_count = 0
                        print("error ",str(insert_err))

                # 3. Insert into EMAIL_HISTORY_TABLE
                cursor.execute(f"SELECT MAX(sequence_number) FROM {EMAIL_HISTORY_TABLE} WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()
                next_seq = (row['max'] or 0) + 1 if row else 1
                
                cursor.execute(
                    f"""
                    INSERT INTO {EMAIL_HISTORY_TABLE} (
                        user_id,
                        email_type,
                        sent_at,
                        sequence_number,
                        status,
                        email_id,
                        activation_reminder_count,
                        login_reminder_count,
                        metadata,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        email_type,
                        now_ts,
                        next_seq,
                        'sent',
                        email_id,
                        activation_count,
                        login_count,
                        json.dumps(metadata) if metadata else None,
                        now_ts
                    )
                )

    except Exception as e:
        print(f"Failed to track email event: {e}")
        # We do NOT raise here to avoid blocking the email sending response
    finally:
        conn.close()


def save_global_email_api_history(
    *,
    to_email: str,
    status: str,
    from_email: str | None = None,
    subject: str | None = None,
    template_name: str | None = None,
    email_type: str | None = None,
    provider_status_code: int | None = None,
    provider_response_text: str | None = None,
    error_message: str | None = None,
    user_id: str | None = None,
    request_payload: dict | None = None,
    metadata: dict | None = None,
):
    """
    Global history row for every /send-email API request.
    Best-effort: never raises to the caller.
    Returns global_history_id (uuid string) or None.
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {GLOBAL_EMAIL_API_HISTORY_TABLE} (
                        user_id,
                        from_email,
                        to_email,
                        subject,
                        template_name,
                        email_type,
                        status,
                        provider_status_code,
                        provider_response_text,
                        error_message,
                        request_payload,
                        metadata
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING global_history_id
                    """,
                    (
                        user_id,
                        from_email,
                        to_email,
                        subject,
                        template_name,
                        email_type,
                        status,
                        provider_status_code,
                        provider_response_text,
                        error_message,
                        json.dumps(request_payload) if request_payload else None,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                row = cursor.fetchone()
                return str(row["global_history_id"]) if row and row.get("global_history_id") else None
    except Exception as e:
        print(f"Failed to save global email history: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass
