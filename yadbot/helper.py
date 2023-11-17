import asyncio
import logging
import os
import posixpath
import sys

import yadisk

logger = logging.getLogger(__name__)

from settings import (
    APP_DIRECTORY_PATH,
    APP_ID,
    APP_SECRET,
    APP_TOKEN,
    UPLOAD_DIRECTORY_PATH,
)


class App:
    def __init__(self):
        self.y_app = yadisk.YaDisk(APP_ID, APP_SECRET, APP_TOKEN, default_args={"n_retries": 5, "retry_interval": 60})
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

    async def sync_files(self) -> None:
        await self._upload(APP_DIRECTORY_PATH)

    async def _upload(self, src_path: os.PathLike) -> None:
        print(list(os.walk(src_path))[0])
        _, dirnames, files_list = list(os.walk(src_path))[0]

        for dirname in dirnames:
            await self._upload(os.path.join(src_path, dirname))

        dst_path = self._create_upload_directory(src_path)

        if files_list:
            await self._upload_files(src_path, dst_path, files_list)
        if src_path != APP_DIRECTORY_PATH and not os.listdir(src_path):
            os.rmdir(src_path)

    def _create_upload_directory(self, src_path: os.PathLike) -> str:
        dst_path = UPLOAD_DIRECTORY_PATH
        dir_path = src_path.split(APP_DIRECTORY_PATH)[-1]
        if dir_path:
            dst_path = posixpath.join(dst_path, dir_path)
            self._create_upload_tree(dir_path)
        return dst_path

    def _create_upload_tree(self, dir_path: str) -> None:
        dirnames = dir_path.split(os.path.sep)
        current_dir_path = UPLOAD_DIRECTORY_PATH
        for dir_name in dirnames:
            current_dir_path = posixpath.join(current_dir_path, dir_name)
            try:
                self.y_app.mkdir(current_dir_path)
            except yadisk.exceptions.PathExistsError:
                logger.warning(f"Path {current_dir_path} already exists")

    async def _upload_files(self, src_path: os.PathLike, dst_path: os.PathLike, files_list: list[str]) -> None:
        logger.info(f"Files to upload:{files_list} from directory: {src_path}")
        async with asyncio.TaskGroup() as task_group:
            for file_name in files_list:
                if file_name.endswith(".part"):
                    continue

                file_path = posixpath.join(src_path, file_name)
                file_path_dest = posixpath.join(dst_path, file_name)
                task_group.create_task(self._upload_file(file_path, file_path_dest))

    async def _upload_file(self, file_path: str, file_path_dest: str) -> None:
        print(f"Uploading file: {file_path} to {file_path_dest}")
        try:
            logger.info(f"Uploading {file_path}")
            self.y_app.upload(file_path, file_path_dest)
        except yadisk.exceptions.PathExistsError:
            logger.warning(f"File already exists: {file_path_dest}")
        except yadisk.exceptions.YaDiskError as exc:
            logger.error(f"Some error occured: {exc}")
            self._stuck_files.add(file_path)
            return

        try:
            os.remove(file_path)
        except Exception as exc:
            logger.error(f"System error occured while deleting file:{exc}")
            self._stuck_files.add(file_path)

        try:
            self._stuck_files.remove(file_path)
        except KeyError:
            ...


app = App()