import json
import logging
import requests
import google.auth.transport.requests
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class FCMNativeService:
    """
    FCM Service using standard HTTP v1 API with pure requests and google-auth.
    Does not use firebase-admin library.
    """
    def __init__(self, service_account_path: str):
        self.service_account_path = service_account_path
        try:
            with open(service_account_path, 'r') as f:
                data = json.load(f)
                self.project_id = data.get('project_id')
            
            if not self.project_id:
                raise ValueError("project_id not found in serviceAccountKey.json")

            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_path, 
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
        except Exception as e:
            logger.error(f"Failed to load service account: {e}")
            raise e

    def get_access_token(self) -> str:
        request = google.auth.transport.requests.Request()
        self.credentials.refresh(request)
        return self.credentials.token

    def send_to_device(self, token: str, title: str, body: str, data: dict = None) -> tuple[bool, str]:
        """
        Sends a message to a specific device using HTTP v1 API.
        Returns:
            (True, "Success") if sent.
            (False, "UNREGISTERED") if token is invalid/unregistered.
            (False, "Error message") for other errors.
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; UTF-8',
            }

            payload = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": title,
                        "body": body
                    }
                }
            }

            if data:
                payload["message"]["data"] = {str(k): str(v) for k, v in data.items()}

            url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
            
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()


            logger.info(response_data)
            if response.status_code == 200:
                return True, "Success"
            
            # Handle Errors
            if 'error' in response_data:
                error_details = response_data['error'].get('details', [])
                for detail in error_details:
                    error_code = detail.get('errorCode')
                    if error_code == 'UNREGISTERED':
                        logger.warning("Token is unregistered or expired. Token should be removed.")
                        return False, "UNREGISTERED"
                    elif error_code == 'SENDER_ID_MISMATCH':
                        logger.error("Sender ID mismatch (Token belongs to a different project).")
                        return False, "SENDER_ID_MISMATCH"
                    elif error_code == 'QUOTA_EXCEEDED':
                        logger.error("FCM Quota exceeded.")
                        return False, "QUOTA_EXCEEDED"
                        
                error_msg = response_data['error'].get('message', 'Unknown Error')
                logger.error(f"Firebase error while sending to token: {error_msg}")
                return False, error_msg
                
            return False, f"HTTP {response.status_code}"

        except Exception as e:
            logger.error(f"Error sending native FCM message: {e}")
            return False, str(e)

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    import sys
    try:
        service = FCMNativeService("")
        # Try sending to a token with custom data payload
        custom_data = {
            "type": "NOTI_UPDATE",
            "noti_id": "12345",
            "url": "https://example.com"
        }
        success, msg = service.send_to_device(
            token="", 
            title=None, 
            body="<p>Thong bao</p> <p> Test2105_1 duoc giao cho anh/chi boi Demo3. Vui long hoan thanh truoc 00:00:00 ngay 30/06/2025. </p>",
            data=custom_data
        )
        print(f"Result: {success}, {msg}")
    except Exception as e:
        print(f"Init error (expected if key missing): {e}")

