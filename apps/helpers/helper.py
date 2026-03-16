# app.py
from flask import Flask, request, jsonify, redirect
import uuid
from email_service import DomainEmailService
from config import Config
from datetime import datetime, timedelta
import os
import json
import threading
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = f"{uuid.uuid4()}"

email_service = DomainEmailService()
config = Config()

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

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "digiAd"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "12345"),
}

USERS_TABLE = os.getenv("USERS_TABLE", "users_demo")
USER_SUBSCRIPTIONS_TABLE = os.getenv("USER_SUBSCRIPTIONS_TABLE", "user_subscriptions1_demo")
USER_FEATURE_CREDITS_TABLE = os.getenv("USER_FEATURE_CREDITS_TABLE", "user_feature_credits_demo")
EMAIL_STATUS_TABLE = os.getenv("EMAIL_STATUS_TABLE", "email_status_demo")
EMAIL_HISTORY_TABLE = os.getenv("EMAIL_HISTORY_TABLE", "email_history_demo")




TEMPLATE_ACTIVATION = os.getenv("TEMPLATE_ACTIVATION", "activation_template")
TEMPLATE_WELCOME = os.getenv("TEMPLATE_WELCOME", "welcome_template")

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

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
                    activation_count = 0
                    login_count = 0

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

from pybars import Compiler
import threading

# pybars3 compiler is notoriously not thread-safe
_template_lock = threading.Lock()
_compiler = Compiler()

def render_hbs_template(template_name, context):
    """
    Renders a Handlebars (HBS) template with the given context.
    Ensures thread safety when compiling.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        TEMPLATE_DIR = os.path.join(BASE_DIR, "templates", "new_template")

        # Ensure .hbs extension
        if not template_name.endswith(".hbs"):
            template_name += ".hbs"

        template_path = os.path.join(TEMPLATE_DIR, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            source = f.read()

        with _template_lock:
            template = _compiler.compile(source)
            
        return template(context)
    
    except FileNotFoundError:
        raise Exception(f"Template {template_name} not found in templates directory")
    except Exception as e:
        raise Exception(f"Failed to render template {template_name}: {str(e)}")

import json # Ensure json is imported

@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        # Get request data
        data = request.get_json()
        
        # Basic required fields
        required_fields = ['from', 'to', 'subject']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Map 'from' parameter to actual email addresses
        from_type = data['from'].lower()
        if from_type == 'sales':
            from_email = config.SALES_EMAIL
        elif from_type == 'support':
            from_email = config.SUPPORT_EMAIL
        else:
            from_email = data['from']  # direct email

        to_email = data['to']
        subject = data['subject']
        template_name = data.get('template')

        # Determine email_type
        # Priority: 1. data['email_type'], 2. derived from template name
        email_type = data.get("email_type",None)
        
        if not email_type and template_name:
            if template_name == TEMPLATE_ACTIVATION:
                email_type = 'activation'
            elif template_name == TEMPLATE_WELCOME:
                email_type = 'welcome'
            # Add other mappings as needed
            elif 'activation_reminder' in template_name.lower():
                email_type = 'activation_reminder'
            elif 'activation' in template_name.lower():
                email_type = 'activation'
            elif 'welcome' in template_name.lower():
                email_type = 'welcome'

        # Optional: gap in minutes for next action (e.g. 20 min for reminder)
        # next_gap_minutes = data.get("next_gap_minutes")

        # Optional: email_id
        # email_id = data.get("email_id")

        # Handle email content: template OR html
        if 'template' in data:
            try:
                html = render_hbs_template(data['template'], data.get('context', {}))
            except Exception as e:
                 return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        elif 'html' in data:
            html = data['html']
        else:
            return jsonify({
                'status': 'error',
                'message': 'Either "template" or "html" must be provided.'
            }), 400

        # Send email
        response = email_service.send_email_from_user(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            html_content=html
        )

        # Handle response
        if response.status_code == 202:
            # Track email status
            if email_type:
                try:
                    conn = get_db_connection()
                    user = get_user_by_email(conn, to_email)
                    conn.close()

                    if user and user.get("user_id"):
                        track_email_event(
                            user_id=user["user_id"],
                            email_type=email_type,
                            template_name=template_name,
                            metadata={"subject": subject, "template": template_name},
                            email_id=to_email
                        )
                        # Append to worker test log for validation
                        append_worker_log({
                            "sent_at":      datetime.utcnow().isoformat(),
                            "email":        to_email,
                            "user_id":      str(user["user_id"]),
                            "email_type":   email_type,
                            "template":     template_name,
                        })
                except Exception as track_err:
                    print(f"Error tracking email: {track_err}")

            return jsonify({
                'status': 'success',
                'message': 'Email sent successfully',
                'from': from_email,
                'to': to_email,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send email',
                'details': response.text,
                'status_code': response.status_code
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

