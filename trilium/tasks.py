from loguru import logger
from typing import Any

from dishka.integrations.aiogram import FromDishka, inject

from app.models.action_result import ActionResult
from app.models.message_action import CustomMessageAction
from app.plugins.base import AsyncTask
from app.savmes import SavmesService

from .helper import add_bookmark_urls, add_note


class TriliumNote(AsyncTask):

    name = "TriliumNote"

    action = CustomMessageAction(
        code="CST_NOTE",
        caption="Note",
        order=501,
        executor_args={
            "task_name": name,
            "is_instant": True,
            "regex": "*",
        },
    )

    @inject
    async def arun_impl(
        self,
        *args: Any,
        savmes_service: FromDishka[SavmesService],
        msgdoc_id: str,
        **_: Any,
    ) -> ActionResult:
        if not (msgdoc := await savmes_service.get_msgdoc_by_id(msgdoc_id)):
            logger.warning(f"Message document [{msgdoc_id}] not found. Aborting.")
            return ActionResult(success=False, popup_text="Message not found.")

        if not (note_text := msgdoc.message_text):
            logger.warning(f"No text in message: {msgdoc_id}")
            return ActionResult(success=False, popup_text="No text in message.")

        source_data = msgdoc.get_source_data()
        try:
            parent_note_id = add_note(note_text, source_data.source_id, source_data.title)
        except Exception:
            logger.exception("Error occured on adding new note.")
            parent_note_id = None

        if not parent_note_id:
            return ActionResult(
                success=False,
                popup_text="Some error occured on adding note, please check logs."
            )

        return ActionResult(
            success=True,
            popup_text=f"Note saved successfully in: {parent_note_id}",
            actions_updated=True
        )


class TriliumBookmark(AsyncTask):

    name = "TriliumBookmark"

    action = CustomMessageAction(
        code="CST_BOOK",
        caption="Bookmark",
        order=502,
        executor_args={
            "task_name": name,
            "is_instant": True,
            "parse_links": True,
        },
    )

    async def arun_impl(self, links: list[str], *args: Any, **_: Any) -> None:
        add_bookmark_urls(links)
