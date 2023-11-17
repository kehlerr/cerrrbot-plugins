import asyncio
from typing import Optional, Union

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from pydantic import BaseModel, HttpUrl


class CommandStates(StatesGroup):
    waiting_url = State()


class CommandActions:
    STOP = "st"


class YDLSMessageData(CallbackData, prefix="YDLS"):
    action: str
    id: str


class YDLCommandArgs(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    url: HttpUrl
    directory_dst: str
    timeout: Optional[int|float] = -1.0


class YDLRequestResult(BaseModel):
    errorcode: Optional[int | None] = None
    output_info: Optional[str | bytes | None] = None
    errors_info: Optional[str | bytes | None] = None
    elapsed: Optional[float | None] = None

    @property
    def is_success(self) -> bool:
        return not bool(self.errorcode)

    def dict(self, *args, **kwargs) -> dict[str, str]:
        data = super().dict(*args, **kwargs)
        for key, value in data.items():
            if isinstance(value, bytes):
                data[key] = value.decode()
        return data


class YDLRequestData(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: str
    url: str
    result: YDLRequestResult
    timeout: Optional[int | float] = None
    proc: Optional[asyncio.subprocess.Process]
    started_at: float = -1.0
    finished_at: Optional[float] = -1.0
