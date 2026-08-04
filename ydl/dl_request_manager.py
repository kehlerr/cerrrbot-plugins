import asyncio
import logging
import signal
from datetime import datetime

import psutil

from .models import YDLCommandArgs, YDLErrorCode, YDLRequestData, YDLRequestResult
from .repository import YDLArgsRepository
from .settings import settings

logger = logging.getLogger("cerrrbot")


class DLRequestManager:
    def __init__(self, repo: YDLArgsRepository) -> None:
        self._repo = repo
        self._requests: dict[str, YDLRequestData] = {}

    async def add_request(self, request_id: str, request_args: YDLCommandArgs) -> YDLRequestResult:
        url = request_args.url
        is_request_duplicated = await self._repo.is_exists(request_id, request_args)
        if is_request_duplicated:
            return YDLRequestResult(
                errorcode=YDLErrorCode.DUPLICATED_REQUEST,
                errors_info=f"Duplicated request for url: {url}"
            )
        await self._repo.insert(request_id, request_args)

        request = YDLRequestData(
            id=request_id,
            url=str(url),
            timeout=request_args.timeout,
            result=YDLRequestResult()
        )
        self._requests[request_id] = request

        cmd_args = [
            "timeout",
            "--signal",
            "SIGINT",
            str(settings.max_timeout),
            "yt-dlp",
            str(url),
            "-P",
            request_args.directory_dst,
        ]
        await self.run_proc(request, cmd_args)
        return request.result

    async def run_proc(self, request: YDLRequestData, cmd_args: list[str]) -> None:
        try:
            request.proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as exc:
            logger.exception(f"[YDL][{request.id}] Failed to spawn process: {exc}")
            request.result.errorcode = YDLErrorCode.PROCESS_SPAWN_FAILED
            request.result.errors_info = f"Failed to spawn yt-dlp process: {exc}"
            return


        request.started_at = datetime.now().timestamp()
        logger.info(
            f"[YDL][{request.id}] Starting subprocess PID {request.proc.pid} at {request.started_at}"
        )

        stdout, stderr = b"", b""
        effective_timeout = request.timeout if (request.timeout and request.timeout > 0) else settings.max_timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                request.proc.communicate(),
                timeout=effective_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"[YDL][{request.id}] Async task finished by timeout")
            request.result.errors_info = f"Download timed out after {effective_timeout}s"
        except Exception as exc:
            logger.error(f"[YDL][{request.id}] Error during process communication: {exc}")
        finally:
            logger.info(f"[YDL][{request.id}] Finishing request process")
            await self.finish_request(request.id, stdout=stdout, stderr=stderr)

    async def finish_request(
        self, request_id: str, stdout: bytes = b"", stderr: bytes = b""
    ) -> YDLRequestResult | None:
        try:
            await self._repo.delete(request_id)
        except Exception:
            pass

        request: YDLRequestData | None = self._requests.pop(request_id, None)
        if request is None:
            logger.warning(f"[YDL][{request_id}] Request not found or already finished")
            return None

        exit_code = await self._terminate_proc(request.proc)
        request.finished_at = datetime.now().timestamp()
        self._process_proc_result(request, exit_code, stdout, stderr)
        logger.info(f"[YDL][{request_id}] Request finished at {request.finished_at}")
        return request.result

    def _process_proc_result(
        self,
        request: YDLRequestData,
        errorcode: int | None,
        stdout: bytes | None,
        stderr: bytes | None,
    ) -> None:
        if errorcode is not None:
            request.result.errorcode = errorcode

        pid_str = request.proc.pid if request.proc else "N/A"
        logger.info(
            f"[YDL][{request.id}] Process {pid_str} exited with code: {request.result.errorcode}"
        )

        if stdout:
            request.result.output_info = stdout
        if stderr:
            if request.result.errors_info and isinstance(request.result.errors_info, str):
                request.result.errors_info = request.result.errors_info.encode() + b"\n" + stderr
            else:
                request.result.errors_info = stderr

        if request.started_at and request.finished_at and request.started_at > 0 and request.finished_at > 0:
            request.result.elapsed = request.finished_at - request.started_at

    async def _terminate_proc(
        self, proc: asyncio.subprocess.Process | None
    ) -> int | None:
        if proc is None:
            return None

        returncode = proc.returncode
        if returncode is None:
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.send_signal(signal.SIGINT)
                    except (psutil.NoSuchProcess, ProcessLookupError):
                        pass
                try:
                    parent.send_signal(signal.SIGINT)
                except (psutil.NoSuchProcess, ProcessLookupError):
                    pass
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass

            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                try:
                    proc.kill()
                except Exception:
                    pass

            returncode = proc.returncode

        return returncode

