import asyncio
from typing import Any, ClassVar, Iterable, get_origin

from aiogram import Router
from celery import Task
from celery.contrib.abortable import AbortableTask
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ioc import get_app_container
from app.models.message_action import CustomMessageAction


class PluginSettings(BaseSettings):
    NAME: ClassVar[str]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=True)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if name := getattr(cls, "NAME", ""):
            model_config = {**cls.model_config, "env_prefix": f"{name}_"}
            cls.model_config = SettingsConfigDict(**model_config)

    @model_validator(mode="before")
    @classmethod
    def _bypass_required_if_disabled(cls, data: dict[str, Any]) -> dict[str, Any]:
        enabled_val = data.get("enabled", True)
        is_disabled = (
            enabled_val is False
            or (isinstance(enabled_val, str) and enabled_val.lower() in ("false", "0", "no", "off"))
        )
        if not is_disabled:
            return data

        for field_name, field_info in cls.model_fields.items():
            if field_info.is_required() and (field_name not in data or data[field_name] is None):
                annotation = field_info.annotation
                origin = get_origin(annotation) or annotation
                if origin is list:
                    data[field_name] = []
                elif origin is dict:
                    data[field_name] = {}
                elif origin is int or origin is float:
                    data[field_name] = 0
                elif origin is bool:
                    data[field_name] = False
                else:
                    data[field_name] = ""
        return data


class AsyncTask(AbortableTask):
    CHECK_ABORT_TIMEOUT: float = 2.0

    action: CustomMessageAction | None = None

    def run(self, *args, **kwargs) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = None

        if loop and loop.is_running():
            return loop.create_task(self.arun(*args, **kwargs))
        else:
            return asyncio.run(self.arun(*args, **kwargs))

    async def arun(self, *args, **kwargs) -> Any:
        container = get_app_container()
        async with container() as dishka_container:
            kwargs["dishka_container"] = dishka_container

            abort_task: asyncio.Task | None = None

            async def run_impl():
                try:
                    return await self.arun_impl(*args, **kwargs)
                finally:
                    if abort_task and not abort_task.done():
                        abort_task.cancel()

            async with asyncio.TaskGroup() as task_group:
                impl_task = task_group.create_task(run_impl())
                abort_task = task_group.create_task(self.check_aborted(impl_task))

            return impl_task.result()

    async def check_aborted(self, impl_task: asyncio.Task) -> None:
        task_id = getattr(self.request, "id", None)
        if not task_id:
            return
        try:
            while not impl_task.done() and not self.is_aborted(task_id=task_id):
                await asyncio.sleep(self.CHECK_ABORT_TIMEOUT)

            if not impl_task.done() and self.is_aborted(task_id=task_id):
                await self.on_abort()
                impl_task.cancel()
        except asyncio.CancelledError:
            pass

    async def on_abort(self) -> None:
        ...

    async def arun_impl(self, *args, **kwargs) -> Any:
        raise NotImplementedError


class Plugin:
    name: str = ""
    settings: PluginSettings | None = None
    commands_router: Router | None = None
    tasks: Iterable[type[AsyncTask]] = ()
    _actions: Iterable[CustomMessageAction] = ()

    def __init__(
        self,
        name: str | None = None,
        settings: PluginSettings | None = None,
        commands_router: Router | None = None,
        tasks: Iterable[type[AsyncTask]] | None = None,
        actions: Iterable[CustomMessageAction] | None = None,
    ) -> None:
        if name is not None:
            self.name = name
        if settings is not None:
            self.settings = settings
        if commands_router is not None:
            self.commands_router = commands_router
        if tasks is not None:
            self.tasks = tasks
        if actions is not None:
            self._actions = actions

    def __repr__(self) -> str:
        return f"<Plugin name={self.name!r} enabled={self.enabled}>"

    @property
    def enabled(self) -> bool:
        if self.settings is not None:
            return self.settings.enabled
        return True

    @property
    def actions(self) -> list[CustomMessageAction]:
        actions = []
        for action in self._actions:
            actions.append(action)

        for task in self.tasks:
            if task.action:
                actions.append(task.action)
        return actions
