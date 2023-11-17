import asyncio
from typing import Any

from celery import Task


class AsyncTask(Task):
    def run(self, *args, **kwargs) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None

        if loop and loop.is_running():
            loop.create_task(self.arun(*args, **kwargs))
        else:
            asyncio.run(self.arun(*args, **kwargs))

    async def arun(self, *args, **kwargs) -> Any:
        raise NotImplementedError
