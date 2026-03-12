import os
import functools
import json
import logging
import os
import traceback
from datetime import datetime
from flask import jsonify, make_response
from logging.handlers import TimedRotatingFileHandler


BASE_URL_EMAIL = os.getenv("BASE_URL_EMAIL")
LOGO_PATH = r'utils/logo/logo.png'

os.makedirs("logs", exist_ok=True)

# Logger setup
logger = logging.getLogger("app-logs")
logger.setLevel(logging.INFO)

# Remove existing handlers (if any)
for h in list(logger.handlers):
    logger.removeHandler(h)

# Name the file with today's date
today = datetime.now().strftime("%Y-%m-%d")
log_file_path = f"logs/app-logs-{today}.log"

file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8",
    utc=False
)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


# ─── Decorator Definition ────────────────────────────────────────────────────
def log_errors_and_respond(status_code: int = 500,platform:str=""):
    """
    Decorator that logs exceptions to file and returns a JSON error response.

    :param status_code: HTTP status code to return on error.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                tb = traceback.format_exc()
                # Log only to file
                logger.error("Exception in %s: %s\n%s", func.__name__, exc, tb)
                # Return JSON error response
                
                if platform:
                    payload={
                    "age": [],
                    "gender": [],
                    "time": [],
                    "device": [],
                    "region": []
                    }
                    return make_response(jsonify(payload), status_code)
                
                payload = {"response": str(exc),"error": str(exc), "endpoint": func.__name__}
                return make_response(jsonify(payload), status_code)

        return wrapper

    return decorator
