import os

from decouple import config

APP_ID = config("YADBOT_APP_ID")
APP_TOKEN = os.getenv("YADBOT_APP_TOKEN")
APP_SECRET = config("YADBOT_APP_SECRET")
APP_DIRECTORY_PATH = config("YADBOT_DIRECTORY_PATH")

UPLOAD_DIRECTORY_PATH = "/cerrrbot"

CHECK_DELAY_DEFAULT = 600
CHECK_DELAY_STUCK = 3600
