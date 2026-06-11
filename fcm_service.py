"""
Firebase Cloud Messaging (FCM) Service

This module provides a clean interface to send push notifications
to mobile applications using the Firebase Admin SDK.
"""

import logging
from typing import Dict, Optional, Tuple

import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError

# =====================================================================
# Configuration & Setup
# =====================================================================
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =====================================================================
# Services
# =====================================================================
class FCMService:
    """
    A service class to handle Firebase Cloud Messaging operations.
    Designed with Clean Code principles: Single Responsibility, explicit typing,
    and structured error handling.
    """

    def __init__(self, service_account_path: str):
        """
        Initialize the FCMService with a service account key.

        Args:
            service_account_path (str): The absolute path to the Firebase service account JSON file.
        """
        self._initialize_app(service_account_path)

    def _initialize_app(self, service_account_path: str) -> None:
        """
        Initialize the Firebase Admin SDK if it hasn't been initialized yet.
        """
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully.")
            except FileNotFoundError:
                logger.error("Service account key file not found: %s", service_account_path)
                raise
            except Exception as e:
                logger.error("Failed to initialize Firebase Admin SDK: %s", e)
                raise

    def send_to_device(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str]:
        """
        Send a notification to a specific device using its FCM token.

        Args:
            token (str): The FCM registration token of the target device.
            title (str): The title of the notification.
            body (str): The body text of the notification.
            data (Optional[Dict[str, str]]): Additional key-value pairs to send to the app.
                                             Note: FCM requires all values in data to be strings.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success, 
                              and the message ID or error message.
        """
        try:
            notification = messaging.Notification(title=title, body=body)
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
            )

            response = messaging.send(message)
            logger.info("Successfully sent message to device. Message ID: %s", response)
            return True, response

        except ValueError as ve:
            logger.error("Invalid arguments provided: %s", ve)
            return False, str(ve)
        except messaging.UnregisteredError as ue:
            logger.warning("Token is unregistered or expired. Token should be removed. Error: %s", ue)
            return False, "UNREGISTERED"
        except messaging.SenderIdMismatchError as sme:
            logger.error("Sender ID mismatch (Token belongs to a different project): %s", sme)
            return False, "SENDER_ID_MISMATCH"
        except messaging.QuotaExceededError as qe:
            logger.error("FCM Quota exceeded: %s", qe)
            return False, "QUOTA_EXCEEDED"
        except FirebaseError as fe:
            logger.error("Firebase error while sending to token: %s", fe)
            return False, str(fe)
        except Exception as e:
            logger.error("Unexpected error while sending to token: %s", e)
            return False, str(e)

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str]:
        """
        Send a notification to all devices subscribed to a specific topic.

        Args:
            topic (str): The name of the FCM topic.
            title (str): The title of the notification.
            body (str): The body text of the notification.
            data (Optional[Dict[str, str]]): Additional key-value pairs to send to the app.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success, 
                              and the message ID or error message.
        """
        try:
            notification = messaging.Notification(title=title, body=body)
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info("Successfully sent message to topic '%s'. Message ID: %s", topic, response)
            return True, response

        except FirebaseError as fe:
            logger.error("Firebase error while sending to topic '%s': %s", topic, fe)
            return False, str(fe)
        except Exception as e:
            logger.error("Unexpected error while sending to topic '%s': %s", topic, e)
            return False, str(e)


# =====================================================================
# Example Usage
# =====================================================================
if __name__ == "__main__":
    # In a production environment, you should load this from environment variables
    # import os
    # SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "path/to/key.json")

    # Uncomment lines below to test if you have a valid serviceAccountKey.json
    
    # try:
    #     fcm_service = FCMService(service_account_path=SERVICE_ACCOUNT_PATH)
    #
    #     # Example 1: Send to a specific device
    #     dummy_token = ""
    #     custom_data = {
    #         "type": "NOTI_UPDATE",
    #         "noti_id": "12345"
    #     }
    #     success, result = fcm_service.send_to_device(
    #         token=dummy_token,
    #         title="Thông báo test 1",
    #         body="Báo cáo đang được giao",
    #         data=custom_data
    #     )

        # # Example 2: Send to a topic
        # success_topic, result_topic = fcm_service.send_to_topic(
        #     topic="news",
        #     title="Bản tin mới",
        #     body="Có thông tin mới dành cho bạn."
        # )

    # except Exception as main_e:
    #     logger.critical("Application stopped due to error: %s", main_e)
    pass
