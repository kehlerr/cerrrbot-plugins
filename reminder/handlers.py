from datetime import UTC, datetime

from dishka import AsyncContainer
from loguru import logger

from app.notifications.exceptions import PushNotificationError
from app.notifications.service import NotificationService
from app.plugins.reminder.exceptions import FailedParsingReminderError

from .models import Reminder
from .repository import ReminderRepository
from .services import ReminderService


async def on_startup(container: AsyncContainer) -> None:
    async with container() as request_container:
        notification_service = await request_container.get(NotificationService)
        reminder_repo = await request_container.get(ReminderRepository)

        await sync_reminders(notification_service, reminder_repo)


async def sync_reminders(notification_service: NotificationService, reminder_repo: ReminderRepository) -> None:

    logger.info("Syncing reminders...")

    now = int(datetime.now(UTC).timestamp())

    reminders = await reminder_repo.get_many({})
    for reminder in reminders:
        if reminder.send_count == 1 and now >= reminder.send_at:
            logger.info(f"Cleaning up old reminder: {reminder.key}")
            await reminder_repo.delete({"key": reminder.key})
            continue

        try:
            await notification_service.push_message_notification(reminder)
            logger.info(f"Restored reminder: {reminder.key}")
        except PushNotificationError:
            logger.info(f"Reminder already exists: {reminder.key}")


async def add_reminder(
    remind_text: str, chat_id: int, reminder_service: ReminderService, notification_service: NotificationService
) -> Reminder:
    if not (result_parsed := await reminder_service.parse_reminder_input(remind_text)):
        raise FailedParsingReminderError

    reminder_notification = await reminder_service.create_reminder_notification(chat_id, result_parsed)
    await notification_service.push_message_notification(reminder_notification)

    return reminder_notification
