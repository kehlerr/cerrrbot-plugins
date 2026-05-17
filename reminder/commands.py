import logging
import os
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from groq import AsyncGroq

from services.notifications import push_message_notification

from .reminder_service import ReminderService


logger = logging.getLogger("cerrrbot")

router = Router()

reminder_service = ReminderService(AsyncGroq(api_key=os.environ.get("GROQ_API_KEY")))


@router.message(Command("remind", ignore_case=True))
async def remind_cmd(message: Message, command: CommandObject, state: FSMContext) -> None:
    if not (remind_text := command.text):
        await message.reply("Введите текст напоминания")
        return

    if not (result_parsed := await reminder_service.parse_reminder_input(remind_text)):
        await message.reply("Не удалось распознать напоминание :(")
        return

    reminder_notification = reminder_service.build_reminder_notification(message.chat.id, result_parsed)
    await push_message_notification(reminder_notification)

    readable_time = datetime.fromtimestamp(reminder_notification.send_at).strftime("%Y-%m-%d %H:%M")
    await message.reply(f"✅ Напоминание запланировано: {readable_time}")
