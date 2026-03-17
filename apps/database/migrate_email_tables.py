import psycopg2
from dotenv import load_dotenv
import os
from database.db import get_db_config

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

load_dotenv()

DB_CONFIG = get_db_config()

USERS_TABLE = os.getenv("USERS_TABLE", "users_demo")
SUBSCRIPTIONS_TABLE = os.getenv("USER_SUBSCRIPTIONS_TABLE", "user_subscriptions1_demo")
FEATURE_CREDITS_TABLE = os.getenv("USER_FEATURE_CREDITS_TABLE", "user_feature_credits_demo")

EMAIL_STATUS_TABLE = os.getenv("EMAIL_STATUS_TABLE", "email_status")
EMAIL_HISTORY_TABLE = os.getenv("EMAIL_HISTORY_TABLE", "email_history")


# ---------------------------------------------------------------------
# ENUM CREATION
# ---------------------------------------------------------------------

ENUM_DEFINITIONS = {
    "email_type_enum": [
        "activation",
        "activation_reminder",
        "welcome",
        "login_reminder",
        "feature_highlights",
        "demo",
        "credits_expiring_soon",
        "pre_expiry",
        "expired",
        "buy_subscription",
    ],
    "email_status_stage_enum": [
        "send_activate",
        "welcome_sent",
        "feature_highlights_sent",
        "demo_sent",
        "partial_credits",
        "credits_check",
        "buy_sub_pending",
        "bonus_offer_sent",
        "expiry_flow",
        "expired_sent",
    ],
    "email_not_interested_reason_enum": [
        "unsubscribed",
        "expired_no_engagement",
        "manual_opt_out",
    ],
}


def create_enums(cursor):
    print("Ensuring Enums exist...")

    for enum_name, values in ENUM_DEFINITIONS.items():
        values_sql = ", ".join([f"'{v}'" for v in values])

        cursor.execute(
            f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                CREATE TYPE {enum_name} AS ENUM ({values_sql});
            END IF;
        END$$;
        """
        )

        print(f"   Checked enum {enum_name}")


# ---------------------------------------------------------------------
# TABLE CREATION
# ---------------------------------------------------------------------

def create_email_status_table(cursor):
    print(f"Ensuring {EMAIL_STATUS_TABLE} exists...")

    cursor.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {EMAIL_STATUS_TABLE} (
        email_status_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

        user_id UUID NOT NULL REFERENCES {USERS_TABLE}(user_id),
        user_subscription_id UUID NULL REFERENCES {SUBSCRIPTIONS_TABLE}(user_subscription_id),
        user_credits_id UUID NULL REFERENCES {FEATURE_CREDITS_TABLE}(user_credits_id),

        current_stage email_status_stage_enum NOT NULL DEFAULT 'send_activate',
        last_email_type email_type_enum NULL,

        activation_reminder_count INTEGER NOT NULL DEFAULT 0,
        login_reminder_count INTEGER NOT NULL DEFAULT 0,

        next_action_at TIMESTAMP NULL,
        last_email_sent_at TIMESTAMP NULL,
        email_id VARCHAR NULL,

        last_expiry_mail_sent_at TIMESTAMP NULL,
        last_expiry_mail_type VARCHAR NULL,
        expiry_sequence_step INTEGER NOT NULL DEFAULT 0,

        is_unsubscribed BOOLEAN NOT NULL DEFAULT FALSE,
        not_interested_reason email_not_interested_reason_enum NULL,
        end_date TIMESTAMP NULL,
        auto_status BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP NOT NULL DEFAULT now()
    );
    """
    )


def create_email_history_table(cursor):
    print(f"Ensuring {EMAIL_HISTORY_TABLE} exists...")

    cursor.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {EMAIL_HISTORY_TABLE} (
        email_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

        user_id UUID NOT NULL REFERENCES {USERS_TABLE}(user_id),
        email_type email_type_enum NOT NULL,

        email_subject VARCHAR,
        sent_at TIMESTAMP NOT NULL DEFAULT now(),

        sequence_number INTEGER NOT NULL DEFAULT 1,

        status VARCHAR DEFAULT 'sent',
        email_id VARCHAR NULL,
        metadata JSONB,

        created_at TIMESTAMP NOT NULL DEFAULT now()
    );
    """
    )


# ---------------------------------------------------------------------
# COLUMN SAFETY CHECKS
# ---------------------------------------------------------------------

EMAIL_STATUS_EXTRA_COLUMNS = {
    "deleted_at": "TIMESTAMP NULL",
    "login_type": "VARCHAR NULL",
    "end_date": "TIMESTAMP NULL",
    "auto_status": "BOOLEAN NOT NULL DEFAULT TRUE",
}

EMAIL_HISTORY_EXTRA_COLUMNS = {
    "activation_reminder_count": "INTEGER DEFAULT 0",
    "login_reminder_count": "INTEGER DEFAULT 0",
}


def ensure_columns(cursor, table_name, columns):
    print(f"Checking extra columns for {table_name}...")

    for column, definition in columns.items():
        cursor.execute(
            f"""
        ALTER TABLE {table_name}
        ADD COLUMN IF NOT EXISTS {column} {definition};
        """
        )

        print(f"   Checked column {column}")


# ---------------------------------------------------------------------
# MAIN MIGRATION
# ---------------------------------------------------------------------

def migrate():

    print("\nStarting Email Migration...\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:

        # 1️⃣ Ensure UUID extension
        print("Ensuring uuid extension exists...")
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        # 2️⃣ Create enums
        create_enums(cursor)

        # 3️⃣ Create tables
        create_email_status_table(cursor)
        create_email_history_table(cursor)

        # 4️⃣ Ensure additional columns
        ensure_columns(cursor, EMAIL_STATUS_TABLE, EMAIL_STATUS_EXTRA_COLUMNS)
        ensure_columns(cursor, EMAIL_HISTORY_TABLE, EMAIL_HISTORY_EXTRA_COLUMNS)

        conn.commit()

        print("\nMigration completed successfully!")

    except Exception as e:

        conn.rollback()
        print("\nMigration failed!")
        print(e)

    finally:

        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# RUN SCRIPT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    migrate()