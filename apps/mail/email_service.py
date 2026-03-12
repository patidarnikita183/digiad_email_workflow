# email_service.py
import json

import requests
from mail.authorization_service import DomainAuthService
from mail.config import Config
from utils.general_helper import logger

class DomainEmailService:
    def __init__(self):
        self.auth_service = DomainAuthService()
        self.config = Config()

    def send_email_from_user(self, from_email, to_email, subject, html_content, attachments=None):
        """
        Sends an email on behalf of a specific user via Microsoft Graph API.
 
        This function constructs the email payload and makes a POST request to the Microsoft Graph
        `/users/{user-id}/sendMail` endpoint, allowing the application to send an email using
        application permissions.
 
        Args:
            from_email (str): The email address of the sender (must exist in the domain).
            to_email (str): The recipient's email address.
            subject (str): The subject line of the email.
            html_content (str): The email body in HTML format.
 
        Returns:
            requests.Response: The HTTP response object from Microsoft Graph API,
            containing the status code and any returned data."""

        # Get valid app access token
        try:
            access_token = self.auth_service.get_valid_access_token()
            if not access_token:
                raise Exception("Failed to get valid access token")

            # Base email payload
            email_payload = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "HTML", "content": html_content},
                    "toRecipients": [{"emailAddress": {"address": to_email}}],
                },
                "saveToSentItems": "true"
            }

            # Handle attachments if provided
            if attachments:
                email_payload["message"]["attachments"] = []
                for attachment in attachments:
                    with open(attachment, "rb") as f:
                        content_bytes = f.read()
                    import base64
                    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

                    email_payload["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment.split("/")[-1],
                        "contentBytes": content_base64
                    })

            # Send email on behalf of the specific user
            graph_url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                graph_url, headers=headers, data=json.dumps(email_payload)
            )

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Mail error : {e}")
            raise Exception(f"Network error while sending email: {e}")
        except Exception as e:
            logger.error(f"Mail error : {e}")
            raise Exception(f"send_email_from_user failed: {e}")
                

    def get_user_mailbox_info(self, user_email):
        """Retrieves mailbox information for a specific user via Microsoft Graph API.
 
        This function sends a GET request to the Microsoft Graph `/users/{user_email}` 
        endpoint to fetch user profile and mailbox-related information such as user details and settings.
 
        Args:
            user_email (str): The email address of the user whose mailbox
                             information is being requested.
 
        Returns:
            requests.Response: The HTTP response object from Microsoft Graph API,
            containing the user's mailbox details or an error message.
            
        """
        try:
        
            access_token = self.auth_service.get_valid_access_token()
            if not access_token:
                raise Exception("Failed to get valid access token")

            graph_url = f"https://graph.microsoft.com/v1.0/users/{user_email}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(graph_url, headers=headers)
            return response
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Mail error : {e}")
            raise Exception(f"Network error while fetching mailbox info: {e}")

        except Exception as e:
            logger.error(f"Mail error : {e}")
            raise Exception(f"get_user_mailbox_info failed: {e}")