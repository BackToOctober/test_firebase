from datetime import datetime
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

class UserFCMToken(Model):
    __tablename__ = 'user_fcm_token'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    user = relationship("User") # Relates to FAB's User model
    token = Column(String(255), unique=True, nullable=False)
    device_info = Column(String(255))
    created_on = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.device_info or 'Unknown Device'}"

class NotificationOutbox(Model):
    __tablename__ = 'notification_outbox'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    user = relationship("User")
    token = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(String(1000), nullable=False)
    status = Column(String(50), default='PENDING', nullable=False) # PENDING, SENT, FAILED, UNREGISTERED
    error_message = Column(String(500), nullable=True)
    created_on = Column(DateTime, default=datetime.now)
    processed_on = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Outbox: {self.title} - {self.status}"
