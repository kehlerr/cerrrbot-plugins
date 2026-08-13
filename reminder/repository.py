from app.infrastructure.repositories import MongoRepository

from .models import Reminder


class ReminderRepository(MongoRepository[Reminder]):
    collection_name = "reminders"
    model_class = Reminder
