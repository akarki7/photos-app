from datetime import datetime
import os
import hashlib


def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")


def get_log_file_path(BASE_DIR):
    current_date = get_current_date()
    log_file_path = os.path.join(BASE_DIR, "logs", f"{current_date}.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    return log_file_path


def custom_hash_function(key):
    return hashlib.sha256(key.encode()).hexdigest()

