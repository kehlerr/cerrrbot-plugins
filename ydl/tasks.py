from common import AppResult
from functools import partial

from plugins.base import AsyncTask

from models.message_document import MessageDocument
from services.notifications import Notification, push_message_notification

from .api import get_reply_text_from_result, dl_stop
from .dl_request import YDLRequestHandler, YDLSRequestHandler, YDLVRequestHandler


class YDLTask(AsyncTask):
    HANDLER_CLS: type[YDLRequestHandler]
    request_id: str

    async def arun_impl(self, link, *args, msgdoc_id: str, **kwargs) -> None:
        on_after_exec = partial(self.on_after_exec, msgdoc_id)
        handler = self.HANDLER_CLS(link)
        self.request_id = handler.request_id
        await handler.execute(after_exec=on_after_exec)

    async def on_after_exec(self, msgdoc_id: str, result: AppResult, *args) -> None:
        await push_message_notification(
            Notification(
                text=get_reply_text_from_result(result),
                reply_to_message_id=MessageDocument(msgdoc_id).message_id,
            )
        )

    async def on_abort(self) -> None:
        await dl_stop(self.request_id)
        await super().on_abort()


class YDLVTask(YDLTask):
    HANDLER_CLS = YDLVRequestHandler


class YDLSTask(YDLTask):
    HANDLER_CLS = YDLSRequestHandler
