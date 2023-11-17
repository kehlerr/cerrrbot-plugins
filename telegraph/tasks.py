import asyncio

from celery import Task
from common import AppResult

from services.notifications import Notification, push_message_notification

from .helper import TelegraphDownloader


class TelegraphScrapeTask(Task):
    def run(self, links: list[dict[str, str]], *args) -> AppResult:
        result = AppResult()
        for link in links:
            downloader = TelegraphDownloader(link)
            downloader.download()
            result.merge(downloader.status)
        asyncio.run(push_message_notification(Notification(text="TG DL finished")))
        return result

