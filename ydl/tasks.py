import asyncio

from celery import Task
from common import AppResult

from .dl_request import YDLSRequestHandler, YDLVRequestHandler


class YDLTask(Task):
    HANDLER_CLS: YDLSRequestHandler | YDLVRequestHandler

    def run(self, link, *args, **kwargs) -> AppResult:
        handler = self.HANDLER_CLS(link)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None

        if loop and loop.is_running():
            loop.create_task(handler.execute())
        else:
            asyncio.run(handler.execute())


class YDLVTask(YDLTask):
    HANDLER_CLS = YDLVRequestHandler


class YDLSTask(YDLTask):
    HANDLER_CLS = YDLSRequestHandler