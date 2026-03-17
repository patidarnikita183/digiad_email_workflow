import time
import os
from datetime import datetime

# Use common pooled DB connection
from database.db import get_db_connection
from error_handling.logging_utils import get_logger

# Dynamic interval (minutes)
CRON_INTERVAL = int(os.getenv("CRON_INTERVAL_MINUTES", 20))

logger = get_logger("cron_to_fetch_data")

def run_queries(conn):

    queries = [

        # Insert users into email_status
        """
        INSERT INTO email_status (user_id, current_stage, email_id, created_at, updated_at)
        SELECT 
            u.user_id,
            'send_activate',
            u.email,
            NOW(),
            NOW()
        FROM users u
        LEFT JOIN email_status es
            ON es.user_id = u.user_id
        WHERE es.user_id IS NULL
        AND u.deleted_at IS NULL
        AND u.email IS NOT NULL;
        """,
        # delete any email_status for users that are deleted
       
        """
        DELETE FROM email_status es
        USING users u
        WHERE es.user_id = u.user_id
        AND u.deleted_at IS NOT NULL;
        """
        
        
        # set default status 
        # Update subscription id
        #    Case 1 — Fill subscription id if NULL
        # If email_status.user_subscription_id is NULL, insert the active subscription.

        """UPDATE email_status es
        SET user_subscription_id = s.user_subscription_id
        FROM user_subscriptions s
        WHERE es.user_id = s.user_id
        AND es.user_subscription_id IS NULL
        AND s.status = 'active'
        AND s.deleted_at IS NULL; """
        
        
        
        # Case 2 — User bought a new subscription
        # If the user checked out again and a new subscription id is created, update it.
        
        """UPDATE email_status es
        SET 
            user_subscription_id = s.user_subscription_id,
            updated_at = NOW()
        FROM (
            SELECT DISTINCT ON (user_id)
                user_id,
                user_subscription_id
            FROM user_subscriptions
            WHERE status = 'active'
            AND deleted_at IS NULL
            ORDER BY user_id, created_at DESC
        ) s
        WHERE es.user_id = s.user_id
        AND es.user_subscription_id <> s.user_subscription_id;"""
        
        # Case 3 — User cancelled autopay (expiry workflow)
        # If the subscription is active but cancel_at is NOT NULL, it means:
        # """
        # UPDATE email_status es
        # SET 
        #     auto_pay = false,
        #     updated_at = NOW()
        # FROM user_subscriptions s
        # WHERE es.user_subscription_id = s.user_subscription_id
        # AND s.cancel_at IS NOT NULL;
        # """
        # case 3 - 
        # set auto status false if user is having free subscription or canceled subscription
        """UPDATE email_status es
        SET 
            auto_status = false,
            updated_at = NOW()
        FROM user_subscriptions s
        WHERE es.user_subscription_id = s.user_subscription_id
        AND (
                (s."razorSubscription_id" = 'trial-free-plan' OR s."paypalSubscription_id" = 'paypal-free-plan')
                OR s.user_cancel_at IS NOT NULL
            );"""
        
        # Update credit id
        """
        UPDATE email_status es
        SET user_credits_id = fc.user_credits_id
        FROM user_feature_credits fc
        WHERE es.user_id = fc.user_id
        AND es.user_subscription_id = fc.user_subscription_id
        AND (
            es.user_credits_id IS NULL
            OR es.user_credits_id <> fc.user_credits_id
        );
        """,


    
    ]

    cursor = conn.cursor()

    try:
        for idx, q in enumerate(queries, start=1):
            try:
                cursor.execute(q)
            except Exception:
                logger.exception("Query #%s failed. Aborting this cron cycle.", idx)
                raise

        conn.commit()
        logger.info("Email status cron executed successfully.")
    finally:
        try:
            cursor.close()
        except Exception:
            logger.exception("Failed closing DB cursor.")


def main():

    while True:
        start_ts = time.time()
        logger.info("Cron cycle started. interval_minutes=%s", CRON_INTERVAL)
        conn = None
        try:
            conn = get_db_connection()
            run_queries(conn)
        except Exception as e:
            logger.exception("Cron cycle failed.")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                logger.exception("Failed closing DB connection.")

        elapsed = time.time() - start_ts
        logger.info("Cron cycle finished. elapsed_seconds=%.3f", elapsed)
        logger.info("Sleeping for %s minutes.", CRON_INTERVAL)

        time.sleep(CRON_INTERVAL * 60)


if __name__ == "__main__":
    main()