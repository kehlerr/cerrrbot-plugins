import os
import re
from dataclasses import dataclass
from typing import Any, Self

import aiofiles
import httpx
from httpx import URL, Response
from loguru import logger

from app.file_ops import create_directory

SEARCH_REGEX = r'(img|video)\ssrc="(?P<file_url>[^"]+)"'


@dataclass
class TelegraphDownloadResult:
    url: str
    success: bool
    media_count: int = 0
    error: str | None = None

    def get_result_info(self) -> str:
        if self.success:
            return f"[TGDL] finished successfully for {self.url} ({self.media_count} files)"
        return f"[TGDL] failed for {self.url}:\n{self.error}"


class TelegraphDownloader:
    SCHEME = "https"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> Self:
        if self._client is None:
            self._client = httpx.AsyncClient()
            self._owns_client = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def download(self, url: str) -> TelegraphDownloadResult:
        parsed_url = URL(url)

        close_after = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient()
            close_after = True

        try:
            page_content = await self._fetch_page_content(client, parsed_url)
            media_urls = self._parse_page_media(page_content)
            if not media_urls:
                return TelegraphDownloadResult(url=url, success=False, error="No media files found")

            dir_name = parsed_url.path.strip("/").split("/")[-1] or "telegraph_media"
            directory_path = create_directory(dir_name)

            prepared_media = self._prepare_media_data(parsed_url, media_urls)
            downloaded_count = await self._download_media(client, directory_path, prepared_media)

            return TelegraphDownloadResult(url=url, success=True, media_count=downloaded_count)
        except Exception as exc:
            logger.error(f"Request/download error occurred for {url}: {exc}")
            return TelegraphDownloadResult(url=url, success=False, error=str(exc))
        finally:
            if close_after:
                await client.aclose()

    async def _fetch_page_content(self, client: httpx.AsyncClient, url: URL) -> str:
        response: Response = await client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_page_media(self, page_content: str) -> list[str]:
        re_pattern = re.compile(SEARCH_REGEX)
        return [match.group("file_url") for match in re_pattern.finditer(page_content)]

    def _prepare_media_data(self, base_url: URL, media_urls: list[str]) -> list[tuple[URL, str]]:
        prepared = []
        for idx, media_path in enumerate(media_urls, start=1):
            raw_name = media_path.split("/")[-1]
            file_name = f"{idx:03d}_{raw_name}"
            if media_path.startswith("http://") or media_path.startswith("https://"):
                media_url = URL(media_path)
            elif media_path.startswith("/"):
                media_url = base_url.copy_with(path=media_path)
            else:
                media_url = base_url.copy_with(path=base_url.path.rstrip("/") + "/" + media_path)
            prepared.append((media_url, file_name))
        return prepared

    async def _download_media(
        self,
        client: httpx.AsyncClient,
        directory_path: str,
        media_data: list[tuple[URL, str]],
    ) -> int:
        downloaded_count = 0
        for media_url, file_name in media_data:
            if await self._download_file(client, directory_path, media_url, file_name):
                downloaded_count += 1

        return downloaded_count

    async def _download_file(
        self,
        client: httpx.AsyncClient,
        directory_path: str,
        url: URL,
        file_name: str,
    ) -> bool:
        try:
            file_path = os.path.join(directory_path, file_name)
            response: Response = await client.get(url)
            response.raise_for_status()
            async with aiofiles.open(file_path, "wb") as fd:
                await fd.write(response.content)
            return True
        except Exception as exc:
            logger.error(f"Failed to download file {url}: {exc}")
            return False
