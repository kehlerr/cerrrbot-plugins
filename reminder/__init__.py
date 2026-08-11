from app.plugins.base import Plugin

from .commands import router as commands_router
from .handlers import on_startup
from .ioc import ReminderProvider
from .settings import ReminderSettings

settings = ReminderSettings()


plugin = Plugin(
    name="reminder",
    settings=settings,
    commands_router=commands_router,
    providers=[ReminderProvider(settings)],
    on_startup_hook=on_startup,
)

__all__ = ("plugin",)