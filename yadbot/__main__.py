import argparse
import logging
import os
import sys
import time

from .helper import app
from .settings import CHECK_DELAY_DEFAULT, CHECK_DELAY_STUCK

logger = logging.getLogger(__name__)



def run():
    if not app.check_token():
        logger.error("Token is invalid")
        sys.exit(1)

    logger.info("Starting syncing...")

    while True:
        app.sync_files()
        pause = CHECK_DELAY_DEFAULT if not app.has_stuck() else CHECK_DELAY_STUCK
        time.sleep(pause)


def set_token_to_env():
    token = app.get_token()
    os.environ["YADBOT_TOKEN"] = token
    print("Token set in env var `YADBOT_TOKEN`")


argparser = argparse.ArgumentParser(description="Yandex Disk and cerrrbot syncer")
argparser.add_argument('-t', '--token-setup', help="Run for getting token only", action="store_true")
params = argparser.parse_args()
if params.token_setup:
    set_token_to_env()
else:
    run()
