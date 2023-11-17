import asyncio
import logging
from typing import Any

from celery.contrib.abortable import AbortableTask

logger = logging.getLogger("cerrrbot")


class AsyncTask(AbortableTask):
    CHECK_ABORT_TIMEOUT: float = 2.0

    def run(self, *args, **kwargs) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None

        if loop and loop.is_running():
            loop.create_task(self.arun(*args, **kwargs))
        else:
            asyncio.run(self.arun(*args, **kwargs))

    async def arun(self, *args, **kwargs) -> None:
        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(self.check_aborted())
            task_group.create_task(self.arun_impl(*args, **kwargs))

    async def check_aborted(self) -> None:
        while not self.is_aborted():
            await asyncio.sleep(self.CHECK_ABORT_TIMEOUT)
        await self.on_abort()

    async def on_abort(self) -> None:
        ...

    async def arun_impl(self, *args, **kwargs) -> Any:
        raise NotImplementedError
