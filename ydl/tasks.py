from loguru import logger
from typing import Any, Iterable

from dishka.integrations.aiogram import FromDishka, inject

from app.models.message_action import CustomMessageAction
from app.notifications import Notification, NotificationService
from app.plugins.base import AsyncTask
from app.savmes import SavmesService

from .api import dl_stop, get_reply_text_from_result
from .dl_request import YDLRequestHandler, YDLSRequestHandler, YDLVRequestHandler
from .models import YDLRequestResult
from .settings import settings


class YDLTask(AsyncTask):
    HANDLER_CLS: type[YDLRequestHandler]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.current_request_id: str | None = None

    @inject
    async def arun_impl(
        self,
        links: Iterable[str],
        *args: Any,
        savmes_service: FromDishka[SavmesService],
        notification_service: FromDishka[NotificationService],
        msgdoc_id: str,
        **_: Any,
    ) -> None:
        if not (msgdoc := await savmes_service.get_msgdoc_by_id(msgdoc_id)):
            logger.warning(f"Message document [{msgdoc_id}] not found. Aborting {self.name}.")
            return

        links_list = list(links)
        if not links_list:
            logger.warning(f"No valid links provided to {self.name}.")
            return

        handler = self.HANDLER_CLS(links_list[0])
        self.current_request_id = handler.request_id

        async def on_after_exec(result: YDLRequestResult | None, *args_cb: Any) -> None:
            await notification_service.push_message_notification(
                Notification(
                    text=get_reply_text_from_result(result),
                    reply_to_message_id=msgdoc.message_id,
                )
            )

        await handler.execute(after_exec=on_after_exec)

    async def on_abort(self) -> None:
        if self.current_request_id:
            await dl_stop(self.current_request_id)
        await super().on_abort()


class YDLVTask(YDLTask):
    HANDLER_CLS = YDLVRequestHandler

    name = "YDLVTask"

    action = CustomMessageAction(
        code="YDLV",
        caption="YDLV",
        order=602,
        executor_args={
            "task_name": name,
            "parse_links": True,
            "allowed_hosts": settings.hosts,
        },
    )


class YDLSTask(YDLTask):
    HANDLER_CLS = YDLSRequestHandler

    name = "YDLSTask"

    action = CustomMessageAction(
        code="YDLS",
        caption="YDLS",
        order=601,
        executor_args={
            "task_name": name,
            "parse_links": True,
            "allowed_hosts": settings.hosts,
        },
    )

