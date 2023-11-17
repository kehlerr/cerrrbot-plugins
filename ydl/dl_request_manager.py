import asyncio
import logging
import signal
from datetime import datetime

import psutil

from .repository import YDLArgsRepository
from .models import YDLCommandArgs, YDLRequestData, YDLRequestResult
from .settings import DUPLICATED_REQUEST_ERROR_CODE

logger = logging.getLogger("cerrrbot")


class DLRequestManager:
    MAX_TIMEOUT: int = 60 * 60 * 12
    CMD_PATTERN: str = (
        'timeout --signal SIGINT {cmd_timeout} yt-dlp "{url}" -P "{output_dir}"'
    )

    def __init__(self, repo: YDLArgsRepository):
        self._repo = repo
        self._requests: dict[str, YDLRequestData] = {}

    async def add_request(self, request_id: str, request_args: YDLCommandArgs) -> YDLRequestResult:
        url = request_args.url
        is_request_duplicated = await self._repo.is_exists(request_id, request_args)
        if is_request_duplicated:
            return YDLRequestResult(
                errorcode=DUPLICATED_REQUEST_ERROR_CODE,
                stderr=f"Duplicated request for url: {url}"
            )
        await self._repo.insert(request_id, request_args)

        request = YDLRequestData(
            id=request_id,
            url=url,
            timeout=request_args.timeout,
            result=YDLRequestResult()
        )
        self._requests[request_id] = request
        cmd: str = self.CMD_PATTERN.format(
            cmd_timeout=self.MAX_TIMEOUT, url=url, output_dir=request_args.directory_dst
        )
        await self.run_proc(request, cmd)
        return request.result

    async def run_proc(self, request: YDLRequestData, cmd: str) -> None:
        request.proc: asyncio.subprocess.Process = (
            await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        )
        request.started_at = datetime.now().timestamp()
        logger.info(
            f"[YDL][{request.id}] Starting subprocess with pid: {request.proc.pid} at: {request.started_at}"
        )
        try:
            await asyncio.wait_for(
                request.proc.communicate(),
                timeout=request.timeout if request.timeout > 0 else self.MAX_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.debug(f"[YDL][{request.id}] async task finished by timeout")
            pass
        finally:
            logger.info(f"[YDL][{request.id}] Finishing normally")
            await self.finish_request(request.id)

    async def finish_request(
        self, request_id: str
    ) -> tuple[str | None, str | None] | None:
        await self._repo.pop(request_id)
        request: YDLRequestData | None = self._requests.pop(request_id, None)
        if request is None:
            # this case could be when request was finished manually
            logger.warning(f"[YDL][{request_id}] Request not found")
            return

        proc_result = await self._terminate_proc(request.proc)
        request.finished_at = datetime.now().timestamp()
        self._process_proc_result(request, *proc_result)
        logger.info(f"[YDL][{request_id}] Request finished at {request.finished_at}")

    def _process_proc_result(
        self,
        request: YDLRequestData,
        errorcode: int | None,
        stdout: bytes | None,
        stderr: bytes | None,
    ) -> None:
        if errorcode is not None:
            request.result.errorcode = errorcode
        logger.info(
            f"[YDL][{request.id}] Process {request.proc.pid} exited with code: {request.result.errorcode}"
        )

        if stdout is not None:
            request.result.output_info = stdout
        logger.debug(
            f"[YDL][{request.id}] Process {request.proc.pid} stdout: {request.result.output_info}"
        )

        if stderr is not None:
            request.result.errors_info = stderr
        logger.info(
            f"[YDL][{request.id}] Process {request.proc.pid} stderr: {request.result.errors_info}"
        )

        if request.started_at > 0 and request.finished_at > 0:
            request.result.elapsed = request.finished_at - request.started_at

    async def _terminate_proc(
        self, proc: asyncio.subprocess.Process
    ) -> tuple[int | None, bytes | None, bytes | None]:
        errorcode, stdout, stderr = None, None, None
        if proc:
            errorcode = proc.returncode
            if errorcode is None:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    child.send_signal(signal.SIGINT)
                parent.send_signal(signal.SIGINT)
            try:
                stdout = await proc.stdout.read()
                stderr = await proc.stderr.read()
            except RuntimeError:
                pass
        return errorcode, stdout, stderr
