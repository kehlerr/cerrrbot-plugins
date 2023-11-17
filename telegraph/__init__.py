from models import CustomMessageAction

from .tasks import TelegraphScrapeTask

actions = (
    CustomMessageAction(code="TGHP_DL", caption="Telegraph DL", order=600, method_args={
        "task_name": "plugins.telegraph.tasks.TelegraphScrapeTask",
        "parse_links": True,
        "allowed_hosts": ["telegra.ph"]
    }),
)

tasks = (
    TelegraphScrapeTask,
)