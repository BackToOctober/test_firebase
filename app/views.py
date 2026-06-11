from flask import flash, redirect
from flask_appbuilder import ModelView, SimpleFormView, expose, action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.sqla.models import User
from wtforms import Form, StringField, TextAreaField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired
from . import appbuilder, db
from .models import UserFCMToken, NotificationOutbox
from .services import NotificationService

class UserFCMTokenModelView(ModelView):
    datamodel = SQLAInterface(UserFCMToken)
    list_columns = ['user.username', 'device_info', 'token', 'created_on']
    search_columns = ['user', 'device_info', 'token']
    add_columns = ['user', 'device_info', 'token']
    edit_columns = ['user', 'device_info', 'token']

def get_user_choices():
    users = db.session.query(User).all()
    return [(str(u.id), u.username) for u in users]

class SendNotificationForm(Form):
    title = StringField('Tiêu đề', validators=[DataRequired()])
    body = TextAreaField('Nội dung', validators=[DataRequired()])
    send_to_all = BooleanField('Gửi tới tất cả User có token', default=False)
    users = SelectMultipleField('Hoặc chọn người nhận cụ thể', choices=[])

class SendNotificationView(SimpleFormView):
    form = SendNotificationForm
    form_title = 'Gửi Thông báo (Push Notification)'
    message = 'Thông báo đã được đưa vào hàng đợi xử lý.'

    def form_get(self, form):
        form.users.choices = get_user_choices()
        
    def form_post(self, form):
        form.users.choices = get_user_choices()
        if not form.validate():
            pass
            
    @expose("/form", methods=["GET"])
    def this_form_get(self):
        return super(SendNotificationView, self).this_form_get()

    @expose("/form", methods=["POST"])
    def this_form_post(self):
        return super(SendNotificationView, self).this_form_post()

    def form_valid(self, form):
        title = form.title.data
        body = form.body.data
        send_to_all = form.send_to_all.data
        selected_user_ids = form.users.data

        service = NotificationService()
        try:
            success, message = service.queue_notification(title, body, send_to_all, selected_user_ids)
            if success:
                flash(message, "info")
            else:
                flash(message, "warning")
        except Exception as e:
            flash(f"Lỗi khi lưu vào Outbox: {e}", "danger")

        return redirect(self.get_redirect())

class NotificationOutboxModelView(ModelView):
    datamodel = SQLAInterface(NotificationOutbox)
    list_columns = ['user.username', 'title', 'status', 'created_on', 'processed_on']
    search_columns = ['user', 'title', 'status', 'token']
    
    @action("send_selected", "Gửi Ngay", "Bạn có chắc chắn muốn gửi các thông báo đã chọn?", "fa-paper-plane")
    def send_selected(self, items):
        if not isinstance(items, list):
            items = [items]

        service = NotificationService()
        try:
            success, message, sc, ec = service.process_outbox_items(items)
            if success:
                flash(message, "info")
            else:
                flash(message, "danger")
        except Exception as e:
            flash(f"Lỗi hệ thống: {e}", "danger")
            
        return redirect(self.get_redirect())


# Register views
appbuilder.add_view(
    UserFCMTokenModelView,
    "Quản lý FCM Tokens",
    icon="fa-mobile",
    category="Push Notification",
    category_icon="fa-bell"
)

appbuilder.add_view(
    SendNotificationView,
    "Tạo Thông báo mới",
    icon="fa-pencil",
    category="Push Notification"
)

appbuilder.add_view(
    NotificationOutboxModelView,
    "Hàng đợi (Outbox)",
    icon="fa-envelope",
    category="Push Notification"
)
