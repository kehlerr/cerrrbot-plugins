
from app.plugins.base import Plugin
from .commands import router as commands_router

plugin = Plugin(
    name="reminder",
    commands_router=commands_router,
)

__all__ = ("plugin", "commands_router")