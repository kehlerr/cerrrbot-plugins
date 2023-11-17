import logging

from common import AppResult

from .dl_request_manager import DLRequestManager
from .models import YDLCommandArgs, YDLRequestResult
from .repository import get_repo
from .settings import DUPLICATED_REQUEST_ERROR_CODE

logger = logging.getLogger("cerrrbot")


_dl_request_manager: DLRequestManager | None = None

async def _get_request_manager() -> DLRequestManager:
    global _dl_request_manager
    if _dl_request_manager is None:
        repo = await get_repo()
        _dl_request_manager = DLRequestManager(repo)

    return _dl_request_manager


async def dl_exec(request_id: str, request_args: YDLCommandArgs) -> AppResult:
    dl_request_manager = await _get_request_manager()
    try:
        result = await dl_request_manager.add_request(request_id, request_args)
    except Exception as exc:
        logger.exception(exc)
        result = YDLRequestResult(errorcode=-100, stderr=str(exc))
    return AppResult(result.is_success, data=result.dict())


async def dl_stop(request_id: str) -> None:
    logger.info(f"[YDL][{request_id}] Stopping request manually")
    dl_request_manager = await _get_request_manager()
    await dl_request_manager.finish_request(request_id)


def get_reply_text_from_result(result: AppResult) -> str:
    if result.errorcode == DUPLICATED_REQUEST_ERROR_CODE:
        return "URL is already processing"

    success_outputs: tuple[str, ...] = ("Interrupted by user", "Exiting normally")
    is_really_failed: bool = False
    if result.errors_info:
        has_success_output = any([v in result.errors_info for v in success_outputs])
        if not has_success_output:
            is_really_failed = True

    reply_text = "Download finished"
    if is_really_failed or not result:
        reply_text += f" with errors:\n{result.errors_info}"
    else:
        reply_text += " successfully"

    elapsed = result.elapsed
    if elapsed:
        reply_text += f"; elapsed {elapsed:.2f} seconds"

    return reply_text
