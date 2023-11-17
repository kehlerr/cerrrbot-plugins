import re
from functools import partial

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    KeyboardButton,
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from common import AppResult
from exceptions import CommandArgsValidationError, EmptyCommandArgsError

from .api import dl_stop
from .models import CommandActions, CommandStates, YDLCommandArgs, YDLSMessageData
from .dl_request import YDLSRequestHandler, YDLVRequestHandler, get_reply_text_from_result


router = Router()


@router.message(CommandStates.waiting_url, F.text.casefold() == "cancel")
async def on_cancel_start(message: Message, bot: Bot, state: FSMContext) -> None:
    replied_message = await message.answer("canceled", reply_markup=ReplyKeyboardRemove())
    await replied_message.delete()
    await message.delete()
    await state.clear()


@router.callback_query(YDLSMessageData.filter(F.action == CommandActions.STOP))
async def on_action_pressed(query: CallbackQuery, callback_data: YDLSMessageData) -> None:
    await dl_stop(callback_data.id)


@router.message(Command(re.compile(r"ydl[s,v]"), ignore_case=True))
async def ydls_cmd(message: Message, command: CommandObject, state: FSMContext) -> None:
    await _run_cmd(command.command, command.args, message, state)


@router.message(CommandStates.waiting_url)
async def process_specified_args(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    cmd_name = state_data["cmd_name"]
    cmd_args = message.text
    await state.clear()
    await _run_cmd(cmd_name, cmd_args, message, state)


async def _run_cmd(cmd_name: str, cmd_args: str, message: Message, state: FSMContext):
    handler_cls = YDLVRequestHandler if cmd_name == "ydlv" else YDLSRequestHandler
    try:
        handler = handler_cls(*cmd_args.split(maxsplit=1))
    except EmptyCommandArgsError:
        await _on_empty_cmd_args(message, state, cmd_name)
        return
    except CommandArgsValidationError as exc:
        await message.reply(str(exc))
        return

    before_exec = partial(cmd_on_before_exec, message)
    after_exec = partial(cmd_on_after_exec, message)
    await handler.execute(before_exec=before_exec, after_exec=after_exec)


async def _on_empty_cmd_args(message: Message, state: FSMContext, cmd_name: str) -> None:
    await state.set_state(CommandStates.waiting_url)
    await state.update_data(cmd_name=cmd_name)
    await message.reply("Specify URL to downlload:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Cancel"),]],
            resize_keyboard=True,
        )
    )


async def cmd_on_before_exec(message: Message, request_id: str, dl_args: YDLCommandArgs) -> Message:
    if dl_args.timeout > 0:
        reply_text = f"Download started for {dl_args.timeout} seconds"
    else:
        reply_text = "Download started"
    replied_message = await message.reply(
        reply_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Stop",
                callback_data=YDLSMessageData(action=CommandActions.STOP, id=request_id).pack(),
            )
        ]])
    )
    return replied_message


async def cmd_on_after_exec(message: Message, dl_result: AppResult, replied_message: Message) -> None:
    reply_text = get_reply_text_from_result(dl_result)
    await message.reply(reply_text)
    await replied_message.delete()
