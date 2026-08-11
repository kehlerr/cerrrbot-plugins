from .models import Reminder
from app.repositories.mongo import MongoRepository


class ReminderRepository(MongoRepository[Reminder]):
    collection_name = "reminders"
    model_class = Reminder
