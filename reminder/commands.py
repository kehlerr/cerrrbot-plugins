import re
from functools import partial

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from common import AppResult
from exceptions import CommandArgsValidationError, EmptyCommandArgsError
 
from services.notifications import Notification, push_message_notification


router = Router()


# 1. Create reminder on specific time (Tomorrow at 20:00, 12 of May)
# 2. Create periodic reminder (Every day at 10PM)
# 3. Create reminder after N days/hours


@router.message(Command("remind", ignore_case=True))
async def remind_cmd(message: Message, command: CommandObject, state: FSMContext) -> None:
    message_text = command.message_text


async def create_reminder(text: str, send_at: int, repeat_in: int = 0, send_count: int = 1) -> Notification:
    return Notification(
        text=text,
        send_at=send_at,
        repeat_in=repeat_in,
        send_count=send_count
    )
