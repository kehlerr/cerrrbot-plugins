from models.message_document import MessageDocument
from plugins.base import AsyncTask
from services.notifications import Notification, push_message_notification

from .helper import TelegraphDownloader


class TelegraphScrapeTask(AsyncTask):
    async def arun_impl(self, link: str, *args, msgdoc_id: str, **kwargs) -> None:
        downloader = TelegraphDownloader(link)
        await downloader.download()

        await push_message_notification(
            Notification(
                text=downloader.get_result_info(),
                reply_to_message_id=MessageDocument(msgdoc_id).message_id,
            )
        )
