import os
from typing import Optional
from uuid import uuid4

from common import get_seconds_from_time
from exceptions import CommandArgsValidationError, EmptyCommandArgsError
from httpx import URL
from pydantic import ValidationError

from .api import dl_exec
from .models import YDLCommandArgs
from .settings import YDL_DEFAULT_DIRECTORY_DST, YDLS_DEFAULT_TIMEOUT


class YDLRequestHandler:
    DEFAULT_TIMEOUT: float

    def __init__(self, *args) -> None:
        self._dl_args = self._parse_dl_cmd_args(*args)
        self.request_id: str = uuid4().hex

    async def execute(
        self,
        before_exec: Optional[callable] = None,
        after_exec: Optional[callable] = None,
    ) -> None:
        if before_exec is not None:
            before_exec_result = await before_exec(self.request_id, self._dl_args)
        else:
            before_exec_result = None

        dl_result = await dl_exec(self.request_id, self._dl_args)

        if after_exec is not None:
            await after_exec(dl_result, before_exec_result)

    def _parse_dl_cmd_args(
        self, url: str, timeout: Optional[int | float] = None
    ) -> YDLCommandArgs:
        if not url:
            raise EmptyCommandArgsError("Need specify url to download")

        if timeout is not None:
            try:
                timeout = get_seconds_from_time(timeout)
                if timeout <= 0:
                    raise CommandArgsValidationError(
                        f"Timeout must be greater 0: {timeout}"
                    )
            except ValueError:
                raise CommandArgsValidationError(f"Invalid timeout value: {timeout}")
        else:
            timeout = self.DEFAULT_TIMEOUT

        directory_dst = self._prepare_directory_dst(url) or YDL_DEFAULT_DIRECTORY_DST
        try:
            return YDLCommandArgs(url=url, timeout=timeout, directory_dst=directory_dst)
        except ValidationError as exc:
            raise CommandArgsValidationError(f"{exc}\nInvalid args: {url}; {timeout}")

    def _prepare_directory_dst(self, *args, **kwargs) -> str | None:
        raise NotImplementedError


class YDLSRequestHandler(YDLRequestHandler):
    DEFAULT_TIMEOUT: float = YDLS_DEFAULT_TIMEOUT

    def _prepare_directory_dst(cls, url: str) -> str | None:
        _url = URL(url)
        host_part: str = _url.host.split(".")[-2]
        path_part: str = _url.path.rstrip(os.path.sep).split(os.path.sep)[-1]
        if host_part and path_part:
            dir_name: str = f"[{host_part}] {path_part}"
            return os.path.join(YDL_DEFAULT_DIRECTORY_DST, dir_name)


class YDLVRequestHandler(YDLRequestHandler):
    DEFAULT_TIMEOUT: float = -1.0
    SUBDIR_KEYS: tuple[str, ...] = ("plname",)

    def _prepare_directory_dst(self, url: str) -> str:
        _url = URL(url)
        host_part: str = _url.host.split(".")[-2]
        dir_path: str = YDL_DEFAULT_DIRECTORY_DST
        if host_part:
            dir_path = os.path.join(dir_path, f"[{host_part}]")

        for key in self.SUBDIR_KEYS:
            param_value = _url.params.get(key)
            if param_value:
                dir_path = os.path.join(dir_path, param_value)
                break

        return dir_path
