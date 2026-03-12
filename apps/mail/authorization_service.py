# auth_service.py
import requests
from datetime import datetime, timedelta
from mail.config import Config
from utils.general_helper import logger

class DomainAuthService:
    def __init__(self):
        self.config = Config()
   
    def get_app_access_token(self):
        """Get application access token using client credentials flow"""
        token_url = f"{self.config.AUTHORITY}/oauth2/v2.0/token"
       
        data = {
            'client_id': self.config.CLIENT_ID,
            'client_secret': self.config.CLIENT_SECRET,
            'scope': ' '.join(self.config.APP_SCOPES),
            'grant_type': 'client_credentials'
        }
       
        response = requests.post(token_url, data=data)
       
        if response.status_code == 200:
            token_data = response.json()
           
            # Calculate expiry time
            expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
           
            # Save in config instance only
            self.config.APP_ACCESS_TOKEN = token_data['access_token']
            self.config.APP_EXPIRES_AT = expires_at.isoformat()
           
            # print(f"New token obtained: {self.config.APP_ACCESS_TOKEN[:20]}...")
            # print(f"Token expires at: {self.config.APP_EXPIRES_AT}")
 
            return token_data['access_token']
        else:
            logger.warning(f"Failed to get app token: {response.text}")
            return None
   
    def get_valid_access_token(self):
        """Get a valid application access token, refreshing if necessary"""
        try:
            if self.config.APP_EXPIRES_AT:
                expires_at = datetime.fromisoformat(self.config.APP_EXPIRES_AT)
                # print(f"Token expires at: {expires_at}")
                # print(f"Current time + 5 min: {datetime.now() + timedelta(minutes=5)}")
               
                if expires_at <= datetime.now() + timedelta(minutes=5):
                    # print("App token expired or expiring soon, refreshing...")
                    return self.get_app_access_token()
                else:
                    # print("Using existing valid app token")
                    return self.config.APP_ACCESS_TOKEN
            else:
                # print("No existing token, getting new one...")
                return self.get_app_access_token()
               
        except Exception as e:
            # print(f"Error getting valid access token: {e}")
            return self.get_app_access_token()