import logging
from flask import Flask
from flask_appbuilder import AppBuilder
from flask_appbuilder.models.sqla.base import SQLA
from flask_migrate import Migrate

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)

with app.app_context():
    from . import models
    appbuilder = AppBuilder(app, db.session)
    from . import views, api

import click
from flask.cli import with_appcontext

@app.cli.group()
def fcm():
    """FCM Notification commands."""
    pass

@fcm.command("process-outbox")
@click.option('--limit', default=100, help='Number of messages to process')
@with_appcontext
def process_outbox(limit):
    """Process pending notifications in outbox."""
    from .dao import NotificationOutboxDAO
    from .services import NotificationService

    service = NotificationService()
    if not service.fcm:
        print("Error initializing FCM Service.")
        return

    pending_items = NotificationOutboxDAO.get_pending(limit)
    if not pending_items:
        print("No pending notifications found.")
        return

    print(f"Processing {len(pending_items)} notifications...")
    try:
        success, message, sc, ec = service.process_outbox_items(pending_items)
        print(message)
    except Exception as e:
        print(f"Error processing outbox: {e}")
