from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from groq import AsyncGroq
from loguru import logger

from app import app_settings

from ..models import Reminder, ReminderParamsExtracted
from ..repository import ReminderRepository
from .datetime_helper import DatetimeHelper
from .llm_helper import LLMHelper


class ReminderService:
    def __init__(
        self,
        client: AsyncGroq,
        model: str,
        repository: ReminderRepository,
        timezone: ZoneInfo | None = None,
    ) -> None:
        self.timezone = timezone or getattr(app_settings, "tz", ZoneInfo("UTC"))
        self._llm_helper = LLMHelper(client, model)
        self._datetime_helper = DatetimeHelper(timezone=self.timezone)
        self.repository = repository

    async def parse_reminder_input(self, user_input: str) -> ReminderParamsExtracted | None:
        # 3. Generate dynamic context for the system prompt
        now = datetime.now(tz=self.timezone)
        tomorrow = now + timedelta(days=1)
        day_after = now + timedelta(days=2)

        ENGLISH_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        current_context_dates = {
            "today_datetime": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "today_weekday": ENGLISH_WEEKDAYS[now.weekday()],
            "tomorrow_date": tomorrow.strftime("%Y-%m-%d"),
            "tomorrow_weekday": ENGLISH_WEEKDAYS[tomorrow.weekday()],
            "day_after_tomorrow_date": day_after.strftime("%Y-%m-%d"),
            "day_after_tomorrow_weekday": ENGLISH_WEEKDAYS[day_after.weekday()],
            "timezone_name": getattr(self.timezone, "key", str(self.timezone)),
            "timezone_offset": now.strftime("%z"),
        }

        extracted_reminder_params = await self._llm_helper.extract_reminder_params(current_context_dates, user_input)
        if extracted_reminder_params:
            logger.info(f"Reminder extracted params: {extracted_reminder_params}")
        else:
            logger.info("Failed to extract reminder params")

        return extracted_reminder_params

    async def create_reminder_notification(self, chat_id: int, data: ReminderParamsExtracted) -> Reminder:
        return await self.repository.insert(
            Reminder(
                text=data.text,
                send_at=self._datetime_helper.calculate_send_at(data),
                repeat_in=self._datetime_helper.calculate_repeat_seconds(data.repeat_unit, data.repeat_value),
                send_count=data.send_count,
                chat_id=chat_id,
                is_repeatable=data.is_repeatable,
            )
        )
