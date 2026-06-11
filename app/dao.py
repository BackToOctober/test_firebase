from .models import UserFCMToken, NotificationOutbox
from . import db

class BaseDAO:
    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()

class UserFCMTokenDAO(BaseDAO):
    @staticmethod
    def get_by_token_and_user(token: str, user_id: int):
        return db.session.query(UserFCMToken).filter_by(token=token, user_id=user_id).first()

    @staticmethod
    def get_by_token(token: str):
        return db.session.query(UserFCMToken).filter_by(token=token).first()

    @staticmethod
    def create(user_id: int, token: str, device_info: str):
        record = UserFCMToken(user_id=user_id, token=token, device_info=device_info)
        db.session.add(record)
        return record

    @staticmethod
    def delete(record: UserFCMToken):
        db.session.delete(record)

    @staticmethod
    def get_tokens_for_users(user_ids=None, send_to_all=False):
        query = db.session.query(UserFCMToken)
        if not send_to_all and user_ids:
            query = query.filter(UserFCMToken.user_id.in_(user_ids))
        return query.all()

class NotificationOutboxDAO(BaseDAO):
    @staticmethod
    def create(user_id: int, token: str, title: str, body: str, status: str = "PENDING"):
        outbox = NotificationOutbox(
            user_id=user_id,
            token=token,
            title=title,
            body=body,
            status=status
        )
        db.session.add(outbox)
        return outbox

    @staticmethod
    def get_pending(limit: int = 100):
        return db.session.query(NotificationOutbox).filter_by(status='PENDING').limit(limit).all()
