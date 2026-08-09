import re
from typing import Any, Iterable

from dishka.integrations.aiogram import FromDishka, inject
from loguru import logger

from app.models.message_action import CustomMessageAction
from app.notifications import Notification, NotificationService
from app.plugins.base import AsyncTask
from app.savmes import SavmesService

from .helper import TelegraphDownloader, TelegraphDownloadResult
from .settings import settings


TELEGRAPH_URL_PATTERN = re.compile(r"^https?://telegra\.ph/[a-zA-Z0-9_-]+/?$")


class TelegraphScrapeTask(AsyncTask):

    name = "TelegraphScrapeTask"

    action = CustomMessageAction(
        code="TGHP_DL",
        caption="Telegraph DL",
        order=600,
        executor_args={
            "task_name": name,
            "parse_links": True,
            "allowed_hosts": settings.hosts
        },
    )

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

        links = {link for link in links if TELEGRAPH_URL_PATTERN.match(link)}
        if not links:
            logger.warning(f"No valid Telegraph links provided to {self.name}.")
            return

        results: list[TelegraphDownloadResult] = []

        async with TelegraphDownloader() as downloader:
            for link in links:
                result = await downloader.download(link)
                results.append(result)

        notification_text = "\n".join(res.get_result_info() for res in results)

        await notification_service.push_message_notification(
            Notification(
                text=notification_text,
                reply_to_message_id=msgdoc.message_id,
            )
        )
