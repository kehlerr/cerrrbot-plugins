import logging

from common import AppResult

from .dl_request_manager import dl_request_manager
from .models import YDLCommandArgs, YDLRequestResult

logger = logging.getLogger("cerrrbot")


async def dl_exec(request_id: str, request_args: YDLCommandArgs) -> AppResult:
    try:
        result = await dl_request_manager.add_request(request_id, request_args)
    except Exception as exc:
        logger.exception(exc)
        result = YDLRequestResult(errorcode=-100, stderr=str(exc))
    return AppResult(result.is_success, data=result.dict())


async def dl_stop(request_id: str) -> None:
    logger.info(f"[YDL][{request_id}] Stopping request manually")
    await dl_request_manager.finish_request(request_id)


def get_reply_text_from_result(result: AppResult) -> str:
    is_really_failed: bool = False
    if result.errors_info:
        if "Interrupted by user" not in result.errors_info:
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
