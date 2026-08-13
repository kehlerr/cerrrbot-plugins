import asyncio
from enum import IntEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from pydantic import BaseModel, HttpUrl


class YDLErrorCode(IntEnum):
    DUPLICATED_REQUEST = -10
    PROCESS_SPAWN_FAILED = -1
    EXECUTION_FAILED = -100


class CommandStates(StatesGroup):
    waiting_url = State()


class CommandActions:
    STOP = "st"


class YDLSMessageData(CallbackData, prefix="YDLS"):
    action: str
    id: str


class YDLCommandArgs(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    url: HttpUrl
    directory_dst: str
    timeout: int | float = -1.0


class YDLRequestResult(BaseModel):
    errorcode: int | None = None
    output_info: str | bytes | None = None
    errors_info: str | bytes | None = None
    elapsed: float | None = None

    @property
    def is_success(self) -> bool:
        return self.errorcode == 0 or self.errorcode is None

    @property
    def errors_text(self) -> str | None:
        if isinstance(self.errors_info, bytes):
            return self.errors_info.decode("utf-8", errors="replace")
        return self.errors_info

    @property
    def output_text(self) -> str | None:
        if isinstance(self.output_info, bytes):
            return self.output_info.decode("utf-8", errors="replace")
        return self.output_info

    def model_dump(self, *args, **kwargs) -> dict:
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if isinstance(value, bytes):
                data[key] = value.decode("utf-8", errors="replace")
        return data


class YDLRequestData(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    id: str
    url: str
    result: YDLRequestResult
    timeout: int | float | None = None
    proc: asyncio.subprocess.Process | None = None
    started_at: float | None = None
    finished_at: float | None = None
