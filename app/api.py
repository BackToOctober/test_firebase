from flask import request
from flask_appbuilder.api import BaseApi, expose
from flask_appbuilder.security.decorators import protect
from . import appbuilder
from .services import NotificationService
import logging

log = logging.getLogger(__name__)

class FCMApi(BaseApi):
    resource_name = "fcm"

    @expose('/register', methods=['POST'])
    @protect() # Require authentication
    def register_token(self):
        """
        API for mobile app to register FCM token.
        Requires authentication.
        Expects JSON payload: {"token": "fcm_token_string", "device_info": "optional_info"}
        """
        if not request.is_json:
            return self.response_400(message="Request must be JSON")
            
        data = request.json
        token = data.get("token")
        device_info = data.get("device_info", "")

        if not token:
            return self.response_400(message="Token is required")

        # In FAB, g.user is available when using @protect()
        from flask import g
        user_id = g.user.id

        service = NotificationService()
        try:
            success, message = service.register_device_token(user_id, token, device_info)
            if success:
                status_code = 200 if "updated" in message else 201
                return self.response(status_code, message=message)
            return self.response(400, message=message)
        except Exception as e:
            return self.response(500, message="Database error")

    @expose('/unregister', methods=['POST'])
    @protect()
    def unregister_token(self):
        """
        API for mobile app to unregister FCM token (e.g. on Logout).
        Expects JSON payload: {"token": "fcm_token_string"}
        """
        if not request.is_json:
            return self.response_400(message="Request must be JSON")
            
        data = request.json
        token = data.get("token")

        if not token:
            return self.response_400(message="Token is required")

        from flask import g
        user_id = g.user.id

        service = NotificationService()
        try:
            success, message = service.unregister_device_token(user_id, token)
            if success:
                return self.response(200, message=message)
            return self.response(404, message=message)
        except Exception as e:
            return self.response(500, message="Database error")

appbuilder.add_api(FCMApi)
