import logging

from .dl_request_manager import DLRequestManager
from .models import YDLCommandArgs, YDLErrorCode, YDLRequestResult
from .repository import get_repo

logger = logging.getLogger("cerrrbot")


_dl_request_manager: DLRequestManager | None = None


async def _get_request_manager() -> DLRequestManager:
    global _dl_request_manager
    if _dl_request_manager is None:
        repo = await get_repo()
        _dl_request_manager = DLRequestManager(repo)

    return _dl_request_manager



async def dl_exec(request_id: str, request_args: YDLCommandArgs) -> YDLRequestResult:
    dl_request_manager = await _get_request_manager()
    try:
        result = await dl_request_manager.add_request(request_id, request_args)
        return result
    except Exception as exc:
        logger.exception(f"[YDL][{request_id}] Download execution failed: {exc}")
        return YDLRequestResult(errorcode=YDLErrorCode.EXECUTION_FAILED, errors_info=str(exc))


async def dl_stop(request_id: str) -> None:
    logger.info(f"[YDL][{request_id}] Stopping request manually")
    dl_request_manager = await _get_request_manager()
    await dl_request_manager.finish_request(request_id)


def get_reply_text_from_result(result: YDLRequestResult | None) -> str:
    if result is None:
        return "Download request processing failed."

    if result.errorcode == YDLErrorCode.DUPLICATED_REQUEST:
        return "URL is already processing"


    errors_text = result.errors_text or ""
    success_outputs: tuple[str, ...] = ("Interrupted by user", "Exiting normally")
    is_really_failed: bool = False

    if errors_text:
        has_success_output = any(v in errors_text for v in success_outputs)
        if not has_success_output:
            is_really_failed = True

    if result.errorcode and result.errorcode != 0:
        is_really_failed = True

    reply_text = "Download finished"
    if is_really_failed:
        reply_text += f" with errors:\n{errors_text or 'Unknown error'}"
    else:
        reply_text += " successfully"

    if result.elapsed:
        reply_text += f"; elapsed {result.elapsed:.2f} seconds"

    return reply_text

