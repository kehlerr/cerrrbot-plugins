import logging
import os
import posixpath
import sys
import time
from typing import Optional

import argparse
import yadisk

logger = logging.getLogger(__name__)

from .settings import APP_ID, APP_SECRET, APP_TOKEN, APP_DIRECTORY_PATH, UPLOAD_DIRECTORY_PATH, CHECK_DELAY_DEFAULT, CHECK_DELAY_STUCK

class App:
    def __init__(self):
        self.y_app = yadisk.YaDisk(APP_ID, APP_SECRET, APP_TOKEN)
        self._stuck_files = set()

    def has_stuck(self) -> bool:
        return bool(self._stuck_files)

    def check_token(self) -> bool:
        return self.y_app.check_token()

    def get_token(self) -> str:
        url = self.y_app.get_code_url()
        print(f"Go to the following url: {url}")
        code = input("Enter the confirmation code: ")

        try:
            response = self.y_app.get_token(code)
        except yadisk.exceptions.BadRequestError:
            print("Bad code, now exiting")
            sys.exit(1)

        self.y_app.token = response.access_token
        if not self.y_app.check_token():
            print("Something went wrong. Not sure how though...")

        return self.y_app.token

    def sync_files(self) -> None:
        self._upload_directory()

    def _upload_directory(self, src_path: Optional[os.PathLike] = APP_DIRECTORY_PATH) -> None:
        dst_path = UPLOAD_DIRECTORY_PATH
        dir_name = src_path.split(APP_DIRECTORY_PATH)[-1].split(os.path.sep)[-1]
        if dir_name:
            dst_path = posixpath.join(dst_path, dir_name)
            try:
                self.y_app.mkdir(dst_path)
            except yadisk.exceptions.PathExistsError:
                logger.warning(f"Path {dst_path} already exists")

        self._upload_files(src_path, dst_path)

    def _upload_files(self, src_path: os.PathLike, dst_path: os.PathLike) -> None:
        files_list = os.listdir(src_path)
        if not files_list:
            logger.debug(f"No files to upload here:{src_path}")
            return

        logger.info(f"Files to upload:{files_list}")

        for file_name in files_list:
            file_path = posixpath.join(src_path, file_name)
            if os.path.isdir(file_path):
                self._upload_directory(file_path)
                continue

            file_path_dest = posixpath.join(dst_path, file_name)
            try:
                logger.info(f"Uploading {file_path}")
                self.y_app.upload(file_path, file_path_dest)
            except yadisk.exceptions.PathExistsError:
                logger.warning(f"File already exists: {file_path_dest}")
            except yadisk.exceptions.YaDiskError as exc:
                logger.error(f"Some error occured: {exc}")
                self._stuck_files.add(file_path)
                continue

            try:
                os.remove(file_path)
            except Exception as exc:
                logger.error(f"System error occured while deleting file:{exc}")
                self._stuck_files.add(file_path)

            try:
                self._stuck_files.remove(file_path)
            except KeyError:
                continue

        if src_path != APP_DIRECTORY_PATH and not os.listdir(src_path):
            os.rmdir(src_path)


def main():
    app = App()
    if not app.check_token():
        if not APP_TOKEN:
            logger.error("Need specify token!")
        else:
            logger.error("Token is invalid")
        sys.exit(1)

    logger.info("Starting syncing...")

    while True:
        app.sync_files()
        pause = CHECK_DELAY_DEFAULT if not app.has_stuck() else CHECK_DELAY_STUCK
        time.sleep(pause)


def get_token():
    app = App()
    token = app.get_token()
    os.environ["YADBOT_TOKEN"] = token
    print(f"Token is: {token}")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Yandex Disk and cerrrbot syncer")
    argparser.add_argument('-t', '--token-only', help="Run for getting token only", action="store_true")

    params = argparser.parse_args()
    if params.token_only:
        get_token()
    else:
        main()