import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
API_URL = os.getenv("SEND_EMAIL_API_URL", "http://localhost:6000/send_email")
SUPPORT_MAIL = os.getenv("SUPPORT_MAIL", "support@digiad.ai")
TEMPLATE_CREDITS_EXPIRING_SOON = os.getenv("TEMPLATE_CREDITS_EXPIRING_SOON", "EXPIRY_REMINDER_24H.hbs")
TEMPLATE_1DAY_BEFORE_EXPIRY    = os.getenv("TEMPLATE_1DAY_BEFORE_EXPIRY", "EXPIRY_REMINDER_1H.hbs")
TEMPLATE_CREDITS_EXPIRED       = os.getenv("TEMPLATE_CREDITS_EXPIRED", "EXPIRED_NOTIFICATION.hbs")

email_type = "pre_expiry_mail_1"    
subject = "Your DigiAd credits are expiring soon!"

def send_test_template_email(email, name, hours_to_expiry_str):
    context = {
        "FirstName": name,
        'expiryTimeframe': hours_to_expiry_str,
        "supportMail": SUPPORT_MAIL,
        "renewLink": os.getenv("RENEW_LINK", "https://digiad.ai/renew"),
        "pricingLink": os.getenv("PRICING_LINK", "https://digiad.ai/pricing"),
        "unsubscribeLink": f"{os.getenv('UNSUBSCRIBE_LINK_BASE', 'https://digiad.ai/unsubscribe?email=')}{email}",
    }
    payload = {
        "to": email,
        "from": SUPPORT_MAIL,
        "subject": subject,
        "template": TEMPLATE_CREDITS_EXPIRING_SOON,
        "email_type": email_type,
        "email_id": email,
        "context": context,
    }


    try:
        response = requests.post(API_URL, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", response.json())
    except Exception as e:
        print("Request failed:", e)
        
if __name__ == "__main__":
    test_email = "patidarnikita183@gmail.com"
    # test_email = "nikita.patidar@xaltanalytics.com"
    
    test_name = "Nikita"
    hours_to_expiry = "48 hours"
    send_test_template_email(test_email, test_name, hours_to_expiry)