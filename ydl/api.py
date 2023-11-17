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
    await dl_request_manager.finish_request(request_id)