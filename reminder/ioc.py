from typing import Any
from dishka import Provider, Scope, provide
from groq import AsyncGroq
from pymongo.asynchronous.database import AsyncDatabase

from .services import ReminderService
from .repository import ReminderRepository
from .settings import ReminderSettings


class ReminderProvider(Provider):
    def __init__(self, settings: ReminderSettings, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.settings = settings

    @provide(scope=Scope.APP)
    def get_reminder_repository(self, db: AsyncDatabase) -> ReminderRepository:
        return ReminderRepository(db)

    @provide(scope=Scope.APP)
    def get_reminder_service(self, repository: ReminderRepository) -> ReminderService:
        return ReminderService(
            AsyncGroq(api_key=self.settings.groq_api_key),
            model=self.settings.groq_model,
            repository=repository,
        )
