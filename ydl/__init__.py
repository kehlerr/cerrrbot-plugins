from models import CustomMessageAction

from .commands import router as commands_router
from .tasks import YDLSTask, YDLVTask
from .settings import YDLS_HOSTS, YDLV_HOSTS


actions = (
    CustomMessageAction(code="YDLS", caption="YDLS", order=601, method_args={
        "task_name": "plugins.ydl.tasks.YDLSTask",
        "is_instant": True,
        "parse_links": True,
        "allowed_hosts": YDLS_HOSTS
    }),
    CustomMessageAction(code="YDLV", caption="YDLV", order=602, method_args={
        "task_name": "plugins.ydl.tasks.YDLVTask",
        "is_instant": True,
        "parse_links": True,
        "allowed_hosts": YDLV_HOSTS
    }),
)

tasks = (
    YDLSTask,
    YDLVTask,
)


__all__ = (
    "commands_router",
    "tasks"
)
