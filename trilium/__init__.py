from app.plugins.base import Plugin

from .settings import settings
from .tasks import TriliumBookmark, TriliumNote
from .helper import ensure_notebook_initialized


plugin = Plugin(
    name="trilium",
    settings=settings,
    tasks=(TriliumNote, TriliumBookmark),
    on_startup_hook=ensure_notebook_initialized
)

__all__ = ("plugin",)

