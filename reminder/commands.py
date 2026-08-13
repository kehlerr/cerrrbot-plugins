from datetime import datetime
from typing import Any

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject
from loguru import logger

from app.notifications import NotificationService

from .exceptions import FailedParsingReminderError
from .handlers import add_reminder
from .services import ReminderService

router = Router()


@router.message(Command("remind", ignore_case=True))
@inject
async def remind_cmd(
    message: Message,
    command: CommandObject,
    reminder_service: FromDishka[ReminderService],
    notification_service: FromDishka[NotificationService],
    *args: Any,
    **kwargs: Any,
) -> None:

    if not (remind_text := command.text):
        await message.reply("Введите текст напоминания")
        return

    try:
        reminder = await add_reminder(remind_text, message.chat.id, reminder_service, notification_service)
    except FailedParsingReminderError:
        logger.exception("Error occured on adding new reminder")
        await message.reply("Не удалось распознать напоминание :(")
        return

    readable_time = datetime.fromtimestamp(reminder.send_at).strftime("%Y-%m-%d %H:%M")
    await message.reply(f"✅ Напоминание запланировано: {readable_time}")
