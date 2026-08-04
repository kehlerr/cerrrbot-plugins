import os
import re
from typing import Callable
from uuid import uuid4

from httpx import URL
from pydantic import HttpUrl, ValidationError

from app.exceptions import CommandArgsValidationError, EmptyCommandArgsError

from .api import dl_exec
from .models import YDLCommandArgs
from .settings import settings
from .utils import get_seconds_from_time


def _sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


class YDLRequestHandler:
    DEFAULT_TIMEOUT = settings.default_timeout

    def __init__(self, url: str, timeout: int | float | str | None = None) -> None:
        self._dl_args = self._parse_dl_cmd_args(url, timeout)
        self.request_id: str = uuid4().hex

    async def execute(
        self,
        before_exec: Callable | None = None,
        after_exec: Callable | None = None,
    ) -> None:
        if before_exec is not None:
            before_exec_result = await before_exec(self.request_id, self._dl_args)
        else:
            before_exec_result = None

        dl_result = await dl_exec(self.request_id, self._dl_args)

        if after_exec is not None:
            await after_exec(dl_result, before_exec_result)

    def _parse_dl_cmd_args(
        self, url: str, timeout: int | float | str | None = None
    ) -> YDLCommandArgs:
        if not url:
            raise EmptyCommandArgsError("Need specify url to download")

        if timeout is not None:
            try:
                parsed_timeout = get_seconds_from_time(timeout)
                if parsed_timeout <= 0:
                    raise CommandArgsValidationError(
                        f"Timeout must be greater than 0: {parsed_timeout}"
                    )
            except ValueError:
                raise CommandArgsValidationError(f"Invalid timeout value: {timeout}")
        else:
            parsed_timeout = self.DEFAULT_TIMEOUT

        directory_dst = self._prepare_directory_dst(url) or settings.data_directory
        try:
            return YDLCommandArgs(url=HttpUrl(url), timeout=parsed_timeout, directory_dst=directory_dst)
        except ValidationError as exc:
            raise CommandArgsValidationError(f"{exc}\nInvalid args: {url}; {timeout}")

    def _prepare_directory_dst(self, url: str) -> str | None:
        raise NotImplementedError


class YDLSRequestHandler(YDLRequestHandler):
    def _prepare_directory_dst(self, url: str) -> str | None:
        try:
            _url = URL(url)
            host_parts = _url.host.split(".")
            host_part = host_parts[-2] if len(host_parts) >= 2 else _url.host
            path_part = _url.path.rstrip("/\\").split("/")[-1]
            if host_part and path_part:
                dir_name = _sanitize_filename(f"[{host_part}] {path_part}")
                return os.path.join(settings.data_directory, dir_name)
        except Exception:
            pass
        return settings.data_directory


class YDLVRequestHandler(YDLRequestHandler):
    DEFAULT_TIMEOUT = -1
    SUBDIR_KEYS: tuple[str, ...] = ("plname",)

    def _prepare_directory_dst(self, url: str) -> str:
        dir_path: str = settings.data_directory
        try:
            _url = URL(url)
            host_parts = _url.host.split(".")
            host_part = host_parts[-2] if len(host_parts) >= 2 else _url.host
            if host_part:
                dir_path = os.path.join(dir_path, f"[{_sanitize_filename(host_part)}]")

            for key in self.SUBDIR_KEYS:
                param_value = _url.params.get(key)
                if param_value:
                    dir_path = os.path.join(dir_path, _sanitize_filename(param_value))
                    break
        except Exception:
            pass

        return dir_path

