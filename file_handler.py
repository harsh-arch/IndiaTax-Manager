import json
import os
from config import Config # Imports the Config class directly
import logging

logging.basicConfig(level=logging.INFO)

# --- User Credential Handling ---

def load_users():
    """Loads the users dictionary from the JSON file."""
    try:
        # Ensure the file exists before trying to open it
        if not os.path.exists(Config.USERS_FILE):
             logging.warning(f"Users file not found ({Config.USERS_FILE}), creating empty file.")
             # Attempt to create it if ensure_data_dirs didn't catch it or it was deleted
             Config.ensure_data_dirs() # Re-run checks just in case
             if not os.path.exists(Config.USERS_FILE): # If still not there after check
                  logging.error(f"Failed to create users file at {Config.USERS_FILE}.")
                  return {} # Return empty dict if creation fails

        with open(Config.USERS_FILE, 'r') as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return {}
            users = json.loads(content)
        return users
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from users file ({Config.USERS_FILE}): {e}. Returning empty dict.")
        return {}
    except FileNotFoundError:
         # This should theoretically be handled by the check above, but keep for safety
        logging.error(f"Users file not found ({Config.USERS_FILE}) despite checks. Returning empty dict.")
        return {}
    except Exception as e: # Catch other potential errors like permissions
        logging.error(f"Unexpected error loading users file ({Config.USERS_FILE}): {e}")
        return {}


def save_users(users_data):
    """Saves the users dictionary to the JSON file."""
    try:
        # Ensure target directory exists
        os.makedirs(os.path.dirname(Config.USERS_FILE), exist_ok=True)

        temp_file = Config.USERS_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(users_data, f, indent=4)
        os.replace(temp_file, Config.USERS_FILE)
        return True
    except IOError as e:
        logging.error(f"Error saving users file ({Config.USERS_FILE}): {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError as rm_err:
                 logging.error(f"Error removing temp file ({temp_file}): {rm_err}")
        return False
    except Exception as e: # Catch other potential errors
        logging.error(f"Unexpected error saving users file ({Config.USERS_FILE}): {e}")
        return False

# --- Individual User Financial Data Handling ---

def get_user_data_file(username):
    """Constructs the path to a user's data file."""
    safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-')).rstrip()
    if not safe_username:
        raise ValueError("Invalid username for file path.")
    return os.path.join(Config.USER_DATA_DIR, f"data_{safe_username}.json")

def load_user_data(username):
    """Loads financial data for a specific user."""
    filepath = get_user_data_file(username)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.info(f"Data file not found for user '{username}', returning empty structure.")
        return {"profile": {}, "financials": {}}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON for user '{username}' ({filepath}): {e}")
        return {"profile": {}, "financials": {}} # Return default on error
    except ValueError as e: # Catch invalid username
        logging.error(f"Error loading data: {e}")
        return {"profile": {}, "financials": {}} # Return default on error
    except Exception as e: # Catch other potential errors
        logging.error(f"Unexpected error loading data for user '{username}' ({filepath}): {e}")
        return {"profile": {}, "financials": {}}

def save_user_data(username, data):
    """Saves financial data for a specific user."""
    try:
        filepath = get_user_data_file(username) # Get path first to catch ValueError early
        # Ensure target directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        temp_file = filepath + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, filepath)
        return True
    except IOError as e:
        logging.error(f"Error saving data file for user '{username}' ({filepath}): {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError as rm_err:
                 logging.error(f"Error removing temp file ({temp_file}): {rm_err}")
        return False
    except ValueError as e:
        logging.error(f"Error saving data: {e}")
        return False
    except Exception as e: # Catch other potential errors
        logging.error(f"Unexpected error saving data for user '{username}' ({filepath}): {e}")
        return False


def create_initial_user_data(username):
    """Creates an empty data file when a user registers."""
    initial_data = {
        "profile": {
            "filing_status": None
        },
        "financials": {} # Store data by year, e.g., {"2023": {"income": [], "expenses": []}}
    }
    # Ensure the user_data directory exists before trying to save
    os.makedirs(Config.USER_DATA_DIR, exist_ok=True)
    return save_user_data(username, initial_data)