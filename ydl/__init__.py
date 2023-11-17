from models import CustomMessageAction

from .commands import router as commands_router
from .settings import YDLS_HOSTS, YDLV_HOSTS
from .tasks import YDLSTask, YDLVTask

actions = (
    CustomMessageAction(
        code="YDLS",
        caption="YDLS",
        order=601,
        method_args={
            "task_name": "plugins.ydl.tasks.YDLSTask",
            "parse_links": True,
            "allowed_hosts": YDLS_HOSTS,
        },
    ),
    CustomMessageAction(
        code="YDLV",
        caption="YDLV",
        order=602,
        method_args={
            "task_name": "plugins.ydl.tasks.YDLVTask",
            "parse_links": True,
            "allowed_hosts": YDLV_HOSTS,
        },
    ),
)

tasks = (
    YDLSTask,
    YDLVTask,
)


__all__ = ("commands_router", "tasks")
