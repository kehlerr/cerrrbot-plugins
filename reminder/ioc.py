from typing import Any

from dishka import Provider, Scope, provide
from groq import AsyncGroq
from pymongo.asynchronous.database import AsyncDatabase

from app import app_settings

from .repository import ReminderRepository
from .services import ReminderService
from .settings import ReminderSettings


class ReminderProvider(Provider):
    def __init__(self, settings: ReminderSettings, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.settings = settings

    @provide(scope=Scope.APP)
    def get_groq_client(self) -> AsyncGroq:
        return AsyncGroq(api_key=self.settings.groq_api_key)

    @provide(scope=Scope.APP)
    def get_reminder_repository(self, db: AsyncDatabase) -> ReminderRepository:
        return ReminderRepository(db)

    @provide(scope=Scope.APP)
    def get_reminder_service(self, client: AsyncGroq, repository: ReminderRepository) -> ReminderService:
        return ReminderService(
            client=client,
            model=self.settings.groq_model,
            repository=repository,
            timezone=app_settings.tz,
        )
