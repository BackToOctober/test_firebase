import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Flask basic config
CSRF_ENABLED = True
SECRET_KEY = '\2\1thisismyscretkey\1\2\e\y\y\h'

# Database config
# Connect to PostgreSQL container mapped to localhost
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://fcm_user:fcm_password@localhost:15432/fcm_db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-AppBuilder specific config
APP_NAME = "FCM Notification App"
APP_THEME = ""  # Default theme
