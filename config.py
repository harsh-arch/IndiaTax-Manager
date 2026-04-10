import os
import json

# WARNING: Hardcoding the secret key is not recommended for security.
# Anyone who sees this code knows your secret key.
# Replace 'a_very_secret_random_string_please_change_me' with your own complex string.
SECRET_KEY_VALUE = 'a_very_secret_random_string_please_change_me'

# Define base directory for file paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = SECRET_KEY_VALUE
    WTF_CSRF_ENABLED = True # Enable CSRF protection for forms

    # --- Email Configuration (Debug Server) ---
    MAIL_SERVER = 'localhost'   # Debug server runs on localhost
    MAIL_PORT = 1025            # Default port for python -m smtpd
    MAIL_USE_TLS = False        # No TLS for debug server
    MAIL_USE_SSL = False        # No SSL for debug server
    MAIL_USERNAME = None        # No username needed
    MAIL_PASSWORD = None        # No password needed
    # Default sender address (can be anything for debug)
    MAIL_DEFAULT_SENDER = ('Tax App Admin', 'noreply@taxapp.local')

    # --- File Handling Configuration ---
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    USER_DATA_DIR = os.path.join(DATA_DIR, 'user_data')

    # --- Ensure data directories exist ---
    @staticmethod
    def ensure_data_dirs():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.USER_DATA_DIR, exist_ok=True)
        # Create users file if it doesn't exist with an empty JSON object
        if not os.path.exists(Config.USERS_FILE):
            # Check if the directory exists first
            if not os.path.exists(Config.DATA_DIR):
                 os.makedirs(Config.DATA_DIR, exist_ok=True)
            # Now create the file
            try:
                with open(Config.USERS_FILE, 'w') as f:
                    json.dump({}, f)
            except IOError as e:
                 print(f"Error: Could not create users file at {Config.USERS_FILE}: {e}")
                 # Depending on severity, you might want to exit or raise the error


# IMPORTANT: Call this immediately to ensure directories are ready when other modules import Config
Config.ensure_data_dirs()