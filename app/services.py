import os
from datetime import datetime
from .dao import UserFCMTokenDAO, NotificationOutboxDAO
import logging

log = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        try:
            from fcm_native_service import FCMNativeService
            key_path = os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey.json')
            self.fcm = FCMNativeService(service_account_path=key_path)
        except Exception as e:
            log.error(f"Error initializing FCM Service: {e}")
            self.fcm = None

    def register_device_token(self, user_id: int, token: str, device_info: str):
        existing_token = UserFCMTokenDAO.get_by_token(token)
        if existing_token:
            if existing_token.user_id != user_id:
                existing_token.user_id = user_id
                existing_token.device_info = device_info
                UserFCMTokenDAO.commit()
            return True, "Token updated"
            
        UserFCMTokenDAO.create(user_id, token, device_info)
        try:
            UserFCMTokenDAO.commit()
            return True, "Token registered successfully"
        except Exception as e:
            UserFCMTokenDAO.rollback()
            log.error(f"Error registering FCM token: {e}")
            raise e

    def unregister_device_token(self, user_id: int, token: str):
        token_record = UserFCMTokenDAO.get_by_token_and_user(token, user_id)
        if token_record:
            try:
                UserFCMTokenDAO.delete(token_record)
                UserFCMTokenDAO.commit()
                return True, "Token unregistered successfully"
            except Exception as e:
                UserFCMTokenDAO.rollback()
                log.error(f"Error unregistering FCM token: {e}")
                raise e
        return False, "Token not found or does not belong to this user"

    def queue_notification(self, title: str, body: str, send_to_all: bool, selected_user_ids: list):
        if not send_to_all and not selected_user_ids:
            return False, "Vui lòng chọn ít nhất 1 người dùng hoặc tick chọn 'Gửi tới tất cả'."
            
        if not send_to_all:
            selected_user_ids = [int(i) for i in selected_user_ids]
            
        tokens = UserFCMTokenDAO.get_tokens_for_users(selected_user_ids, send_to_all)
        if not tokens:
            return False, "Không tìm thấy Token FCM nào cho các user được chọn."
            
        success_count = 0
        for token_record in tokens:
            NotificationOutboxDAO.create(
                user_id=token_record.user_id,
                token=token_record.token,
                title=title,
                body=body,
                status="PENDING"
            )
            success_count += 1
            
        try:
            NotificationOutboxDAO.commit()
            return True, f"Đã đưa {success_count} thông báo vào Hàng đợi (Outbox). Hãy sang mục Outbox để tiến hành gửi."
        except Exception as e:
            NotificationOutboxDAO.rollback()
            log.error(f"Error queueing notification: {e}")
            raise e

    def process_outbox_items(self, items):
        if not self.fcm:
            return False, "Lỗi: Không thể tải module FCMService.", 0, 0

        success_count = 0
        error_count = 0
        
        for item in items:
            if item.status != 'PENDING':
                continue
                
            success, error_msg = self.fcm.send_to_device(
                token=item.token,
                title=item.title,
                body=item.body
            )
            
            item.processed_on = datetime.now()
            if success:
                item.status = "SENT"
                success_count += 1
            else:
                item.error_message = error_msg
                if error_msg == "UNREGISTERED":
                    item.status = "UNREGISTERED"
                    orig_token = UserFCMTokenDAO.get_by_token(item.token)
                    if orig_token:
                        UserFCMTokenDAO.delete(orig_token)
                else:
                    item.status = "FAILED"
                error_count += 1

        try:
            NotificationOutboxDAO.commit()
            return True, f"Đã xử lý: Thành công {success_count}, Thất bại {error_count}.", success_count, error_count
        except Exception as e:
            NotificationOutboxDAO.rollback()
            log.error(f"Error processing outbox items: {e}")
            raise e
