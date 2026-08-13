from app.plugins.base import Plugin

from .helper import ensure_notebook_initialized
from .settings import settings
from .tasks import TriliumBookmark, TriliumNote

plugin = Plugin(
    name="trilium", settings=settings, tasks=(TriliumNote, TriliumBookmark), on_startup_hook=ensure_notebook_initialized
)

__all__ = ("plugin",)
