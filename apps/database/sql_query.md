# user_email , checking the difference between now to end date in days
SELECT
    u.email AS user_email,
    s.end_date,
    (s.end_date - NOW()) AS difference_between
FROM public.user_subscriptions s
JOIN public.users u
    ON u.user_id = s.user_id
WHERE s.end_date IS NOT NULL
  AND s.deleted_at IS NULL
ORDER BY s.end_date;

# insert new user from users table to email_status table 

INSERT INTO email_status (user_id, current_stage,email_id, created_at, updated_at)
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


# delete all rows from any table 
TRUNCATE TABLE email_status CASCADE;


# update the value of subscription id if column is null in status table
UPDATE email_status es
SET user_subscription_id = s.user_subscription_id
FROM user_subscriptions s
WHERE es.user_id = s.user_id
AND es.user_subscription_id IS NULL
AND s.status = 'active'
AND s.deleted_at IS NULL;

# update the value of credit id if it is null in status table 
UPDATE email_status es
SET user_credits_id = fc.user_credits_id
FROM user_feature_credits fc
WHERE es.user_id = fc.user_id
  AND es.user_subscription_id = fc.user_subscription_id
  AND (
        es.user_credits_id IS NULL
        OR es.user_credits_id <> fc.user_credits_id
      )
  

# update the value of subscription id if user took new plan in status table
UPDATE email_status es
SET user_subscription_id = s.user_subscription_id
FROM user_subscriptions s
WHERE es.user_id = s.user_id
AND es.user_subscription_id IS NULL
AND s.status = 'active'
AND s.deleted_at IS NULL;\

# add column into existing table
ALTER TABLE email_status
ADD COLUMN end_date TIMESTAMP WITHOUT TIME ZONE;

# check time zone of any column
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'user_subscriptions'
AND column_name = 'end_date';



# update only end_date 
UPDATE email_status es
SET 
    end_date = s.end_date,
    last_expiry_mail_sent_at = NULL,
    last_expiry_mail_type = NULL,
    expiry_sequence_step = 0,
    current_stage = 'paid_welcome_sent',
    updated_at = NOW()
FROM user_subscriptions s
WHERE es.user_subscription_id = s.user_subscription_id
AND s.status = 'active'
AND s.deleted_at IS NULL
AND (
        es.end_date IS NULL
        OR es.end_date <> s.end_date
    );


# update subscription id and reset sequence flow 
UPDATE email_status es
SET 
    user_subscription_id = s.user_subscription_id,
    last_expiry_mail_sent_at = NULL,
    last_expiry_mail_type = NULL,
    expiry_sequence_step = 0,
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
AND (
        es.user_subscription_id IS NULL
        OR es.user_subscription_id <> s.user_subscription_id
    );