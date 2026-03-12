from dotenv import load_dotenv
import os
 
load_dotenv()
 
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "any_secret_key")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")  # Use your specific tenant ID, not 'common'
    PORT = int(os.getenv("PORT", 5000))
   
    # For application permissions, use tenant-specific authority
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
   
    # Application permissions scope
    APP_SCOPES = ["https://graph.microsoft.com/.default"]
   
    # Domain email addresses
    SALES_EMAIL = "support@digiad.ai"
    SUPPORT_EMAIL = "sales@digiad.ai"
 
    def __init__(self):
        # Initialize token storage as instance variables
        self._app_access_token = None
        self._app_expires_at = None
 
    @property
    def APP_ACCESS_TOKEN(self):
        return self._app_access_token
 
    @APP_ACCESS_TOKEN.setter
    def APP_ACCESS_TOKEN(self, value):
        self._app_access_token = value
 
    @property
    def APP_EXPIRES_AT(self):
        return self._app_expires_at
 
    @APP_EXPIRES_AT.setter
    def APP_EXPIRES_AT(self, value):
        self._app_expires_at = value