import re
from typing import Any

import httpx
from loguru import logger
from trilium_py.client import ETAPI

from .settings import settings

trilium_client = ETAPI(settings.url, settings.token)

urlregex = (
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


def extract_note_title(message_text: str) -> str:
    text = message_text.strip().replace('\n', ' ')
    if len(text) <= 50:
        return text

    subset = text[:50]
    last_comma_or_dot = max(subset.rfind(','), subset.rfind('.'))

    if last_comma_or_dot != -1:
        return subset[:last_comma_or_dot].strip()

    if subset[-1].isalnum() and text[50].isalnum():
        return subset[:47] + "..."
    else:
        return subset.strip()


def add_bookmark_urls(text_links: list[str]) -> bool:
    urls = set(text_links)
    existing_content = trilium_client.get_note_content(settings.note_id_bookmarks_url)
    adding_content = _horizontal_line() + _paragraph(
        "<br>".join(_link(url) for url in urls)
    )
    new_content = existing_content + adding_content
    result = trilium_client.update_note_content(
        settings.note_id_bookmarks_url, new_content
    )
    return result


def add_note(message_text: str, chat_id: str, source_title: str | None) -> str | None:
    content = _transform_message_text(message_text)
    content = "<br>".join(content.split("\n"))

    if "-" in chat_id:
        chat_id = chat_id.replace("-", "")

    parent_note_title = source_title or chat_id

    parent_note_id = create_or_get_parent_note(
        settings.note_id_book_notes_all, chat_id, parent_note_title
    )

    note_title = extract_note_title(message_text)
    result = trilium_client.create_note(
        parentNoteId=parent_note_id,
        title=note_title,
        type="text",
        content=content,
    )

    return parent_note_title if result else None


def _link(content: str) -> str:
    return f"""<a href="{content}">{content}</a>"""


def _paragraph(content: str) -> str:
    return f"<p>{content}</p>"


def _horizontal_line() -> str:
    return "<hr>"


def _transform_message_text(content: str):
    return re.sub(
        urlregex, lambda x: '<a href="{}">{}</a>'.format(x.group(), x.group()), content
    )


def create_or_get_parent_note(parent_note_id: str, note_id: str, title: str) -> str:
    result = trilium_client.get_note(note_id)
    if result.get("status") == httpx.codes.NOT_FOUND:
        result = trilium_client.create_note(
            parentNoteId=parent_note_id,
            title=title,
            type="book",
            content="none",
            noteId=note_id,
        )

    try:
        note_id = result["note"]["noteId"]
    except KeyError:
        note_id = result["noteId"]

    return note_id


def _init_notes() -> None:

    logger.info("Initializing notes and root notebook...")

    note_id_book_root = settings.note_id_book_root

    trilium_client.create_note(
        parentNoteId="root",
        title="[TG] Cerrrbot",
        type="book",
        content="CerrrBot Root Book",
        noteId=note_id_book_root
    )

    trilium_client.create_note(
        parentNoteId=settings.note_id_book_root,
        title="[TG] Bookmarks URLs",
        type="text",
        content="<hr>",
        noteId=settings.note_id_bookmarks_url,
    )

    trilium_client.create_note(
        parentNoteId=settings.note_id_book_root,
        title="[TG] All notes",
        type="book",
        content="CerrrBot message notes book",
        noteId=settings.note_id_book_notes_all,
    )

    logger.info("Initializing completed.")


async def ensure_notebook_initialized(*args: Any, **_: Any) -> None:
    response_check = trilium_client.get_note(settings.note_id_book_root)
    if response_check.get("status") == httpx.codes.NOT_FOUND:
        _init_notes()