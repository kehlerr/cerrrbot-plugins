from app.plugins.base import Plugin

from .settings import settings
from .tasks import TriliumBookmark, TriliumNote

plugin = Plugin(
    name="trilium",
    settings=settings,
    tasks=(TriliumNote, TriliumBookmark),
)

__all__ = ("plugin",)

