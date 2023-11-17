import asyncio

from celery import Task
from common import AppResult
from models.message_document import MessageDocument
from services.notifications import Notification, push_message_notification

from .helper import TelegraphDownloader


class TelegraphScrapeTask(Task):
    def run(self, links, *args, msgdoc_id: str, **kwargs) -> None:
        result = AppResult()
        for link in links:
            downloader = TelegraphDownloader(link)
            downloader.download()
            result.merge(downloader.status)

        asyncio.run(
            push_message_notification(
                Notification(
                    text=result and "TG DL finished succesfully" or "TG DL failed",
                    reply_to_message_id=MessageDocument(msgdoc_id).message_id
                )
            )
        )