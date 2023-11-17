import asyncio
import logging
import signal
from datetime import datetime

import psutil

from .models import YDLCommandArgs, YDLRequestData, YDLRequestResult

logger = logging.getLogger("cerrrbot")


class DLRequestManager:

    MAX_TIMEOUT: int = 60*60*12
    CMD_PATTERN: str = "timeout --signal SIGINT {cmd_timeout} yt-dlp \"{url}\" -P \"{output_dir}\""

    def __init__(self):
        self._requests: dict[str, YDLRequestData] = {}

    async def add_request(self, request_id: str, request_args: YDLCommandArgs) -> YDLRequestResult:
        url = request_args.url
        if self._requests:
            if request_id in self._requests or url in (v.url for v in self._requests.values()):
                return YDLRequestResult(errorcode=-1, stderr=f"Duplicated request for url: {url}")

        request = YDLRequestData(
            id=request_id,
            url=url,
            timeout=request_args.timeout,
            result=YDLRequestResult()
        )
        self._requests[request_id] = request
        cmd: str = self.CMD_PATTERN.format(cmd_timeout=self.MAX_TIMEOUT, url=url, output_dir=request_args.directory_dst)
        await self.run_proc(request, cmd)
        return request.result

    async def run_proc(self, request: YDLRequestData, cmd: str) -> None:
        request.proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        request.started_at = datetime.now().timestamp()
        logger.info(f"[YDL][{request.id}] Starting subprocess with pid: {request.proc.pid} at: {request.started_at}")
        try:
            await asyncio.wait_for(
                request.proc.communicate(),
                timeout=request.timeout if request.timeout > 0 else self.MAX_TIMEOUT
            )
        except asyncio.TimeoutError:
            pass
        finally:
            await self.finish_request(request.id)

    async def finish_request(self, request_id: str) -> tuple[str|None, str|None] | None:
        request = self._requests.pop(request_id, None)
        if request is None:
            logger.warning(f"[YDL][{request_id}] Request not found")
            return

        proc_result = await self._terminate_proc(request.proc)
        request.finished_at = datetime.now().timestamp()
        self._process_proc_result(request, *proc_result)
        logger.info(f"[YDL][{request_id}] Request finished at {request.finished_at}")

    def _process_proc_result(self,
        request: YDLRequestData,
        errorcode: int | None,
        stdout: bytes | None,
        stderr: bytes | None
    ) -> None:
        if errorcode is not None:
            request.result.errorcode = errorcode
        logger.info(f"[YDL][{request.id}] Process {request.proc.pid} exited with code: {request.result.errorcode}")

        if stdout is not None:
            request.result.output_info = stdout
        logger.debug(f"[YDL][{request.id}] Process {request.proc.pid} stdout: {request.result.output_info}")

        if stderr is not None:
            request.result.errors_info = stderr
        logger.info(f"[YDL][{request.id}] Process {request.proc.pid} stderr: {request.result.errors_info}")

        if request.started_at > 0 and request.finished_at > 0:
            request.result.elapsed = request.finished_at - request.started_at

    async def _terminate_proc(self, proc: asyncio.subprocess.Process) -> tuple[int | None, bytes | None, bytes | None]:
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


dl_request_manager = DLRequestManager()