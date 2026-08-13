from app.plugins.base import Plugin

from .commands import router as commands_router
from .settings import settings
from .tasks import YDLSTask, YDLVTask

plugin = Plugin(
    name="ydl",
    settings=settings,
    commands_router=commands_router,
    tasks=(
        YDLSTask,
        YDLVTask,
    ),
)


__all__ = ("plugin",)
