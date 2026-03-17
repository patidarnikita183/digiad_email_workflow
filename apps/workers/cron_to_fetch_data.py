import time
import os
import psycopg2
from datetime import datetime

# Dynamic interval (minutes)
CRON_INTERVAL = int(os.getenv("CRON_INTERVAL_MINUTES", 20))

DB_CONFIG = {
    "host": "localhost",
    "database": "your_db",
    "user": "your_user",
    "password": "your_password",
    "port": 5432
}


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

    for q in queries:
        cursor.execute(q)

    conn.commit()
    cursor.close()

    print(f"[{datetime.utcnow()}] Email status cron executed")


def main():

    while True:

        try:
            conn = psycopg2.connect(**DB_CONFIG)

            run_queries(conn)

            conn.close()

        except Exception as e:
            print("Cron error:", e)

        print(f"Sleeping for {CRON_INTERVAL} minutes...\n")

        time.sleep(CRON_INTERVAL * 60)


if __name__ == "__main__":
    main()