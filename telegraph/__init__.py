from app.plugins.base import Plugin

from .settings import settings
from .tasks import TelegraphScrapeTask

plugin = Plugin(name="telegraph", tasks=(TelegraphScrapeTask,), settings=settings)

__all__ = ("plugin",)
