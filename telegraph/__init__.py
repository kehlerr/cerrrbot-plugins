from app.plugins.base import Plugin

from .tasks import TelegraphScrapeTask
from .settings import settings

plugin = Plugin(
    name="telegraph",
    tasks=(TelegraphScrapeTask,),
    settings=settings
)

__all__ = ("plugin",)
