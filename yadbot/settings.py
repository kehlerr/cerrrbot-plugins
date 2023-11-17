import os

from decouple import config

APP_ID = config("YADBOT_APP_ID")
APP_TOKEN = os.getenv("YADBOT_APP_TOKEN")
APP_SECRET = config("YADBOT_APP_SECRET")

APP_DIRECTORY_PATH: str = config("YADBOT_DIRECTORY_PATH")
if not APP_DIRECTORY_PATH or not os.path.exists(APP_DIRECTORY_PATH):
    raise FileNotFoundError(APP_DIRECTORY_PATH)
if not APP_DIRECTORY_PATH.endswith(os.path.sep):
    APP_DIRECTORY_PATH += os.path.sep

UPLOAD_DIRECTORY_PATH = "/cerrrbot"

CHECK_DELAY_DEFAULT = 600
CHECK_DELAY_STUCK = 3600
