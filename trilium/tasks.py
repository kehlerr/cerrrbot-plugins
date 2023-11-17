from celery import Task
from common import AppResult
from models.message_document import MessageDocument

from .helper import add_bookmark_urls, add_note


class TriliumNote(Task):

    def run(self, _, *args, msgdoc_id: str, **kwargs) -> AppResult:
        msgdoc = MessageDocument(msgdoc_id)
        forward_from_id, title = msgdoc.get_from_chat_data()
        if not forward_from_id:
            forward_from_id, title = msgdoc.get_from_user_data()

        return AppResult(add_note(msgdoc.message_text, forward_from_id, title))


class TriliumBookmark(Task):

    def run(self, links, *args, msgdoc_id: str, **kwargs) -> AppResult:
        msgdoc = MessageDocument(msgdoc_id)
        return AppResult(add_bookmark_urls(msgdoc.message_text, links))
