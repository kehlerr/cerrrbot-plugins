import asyncio
import logging
import os
import re

import aiofiles
import httpx
from common import AppResult, create_directory
from httpx import URL, HTTPError, Response

logger = logging.getLogger("cerrrbot")


SEARCH_REGEX = r'(img|video)\ssrc="(?P<file_url>[^"]+)"'


class TelegraphDownloader:
    SCHEME = "https"

    def __init__(self, url: str) -> None:
        self.status = AppResult()
        # self._url = URL(url, scheme=self.SCHEME)
        self._url = URL(url)
        self._directory_path = None
        self._page_content = None
        self._media_data = None

    async def download(self) -> None:
        self._fetch_page_content()
        self._parse_page_media()
        self._prepare_download_media()
        await self._download_media()

    def get_result_info(self) -> str:
        if self.status:
            return "[TGDL] finished succesfully"
        return "[TGDL] failed:\n{}".format(self.status.info)

    def _fetch_page_content(self) -> None:
        try:
            self._page_content = httpx.get(self._url).text
        except HTTPError as exc:
            self._page_content = ""
            logger.error(f"Request error occured: {exc}")

    def _parse_page_media(self):
        re_pattern = re.compile(SEARCH_REGEX)
        self._media_data = [
            match.group("file_url") for match in re_pattern.finditer(self._page_content)
        ]

    def _prepare_download_media(self) -> None:
        if not self._media_data:
            self.status = AppResult(False, "Empty media urls")
            return

        self._setup_directory()
        self._setup_media_data()

    def _setup_media_data(self) -> None:
        media_data = []
        for media_path in self._media_data:
            file_name = media_path.split("/")[-1]
            media_url = self._url.copy_with(path=media_path)
            media_data.append((media_url, file_name))

        self._media_data = media_data

    def _setup_directory(self) -> None:
        dir_name = self._url.path.split("/")[-1]
        create_result = create_directory(dir_name)
        if not create_result:
            self.status = create_result
            return

        self._directory_path = create_result.data["path"]

    async def _download_media(self) -> None:
        if not self.status:
            return

        tasks = []
        async with asyncio.TaskGroup() as task_group:
            for media in self._media_data:
                task = task_group.create_task(self._download_file(*media))
                tasks.append(task)

        result = AppResult()
        result.merge(*[t.result() for t in tasks])
        self.status = result

    async def _download_file(self, url: str, file_name: str) -> AppResult:
        file_path = os.path.join(self._directory_path, file_name)
        async with httpx.AsyncClient() as client:
            response: Response = await client.get(url)

        async with aiofiles.open(file_path, "wb") as fd:
            await fd.write(response.content)

        return AppResult()
