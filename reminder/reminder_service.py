import logging
from typing import Any, Mapping
from datetime import datetime, timedelta

from groq import AsyncGroq
from groq.types.chat import ChatCompletion
from pydantic import ValidationError

from services.notifications import Notification

from .constants import DEFAULT_TIME_OF_DAY, REMINDER_SYSTEM_PROMPT, WEEK_LENGTH, TimeUnit, Weekday
from .models import ReminderParamsExtracted


logger = logging.getLogger("cerrrbot")


class LLMHelper:

    _SYSTEM_PROMPT = REMINDER_SYSTEM_PROMPT
    _tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_reminder_parameters",
                "description": "Extract scheduling parameters and clean text for a new reminder.",
                "parameters": ReminderParamsExtracted.model_json_schema()
            },
        }
    ]

    def __init__(self, llm_client: AsyncGroq):
        self._llm_client = llm_client

    async def extract_reminder_params(self, context: Mapping[str, Any], user_input: str) -> ReminderParamsExtracted | None:
        system_prompt = self._prepare_system_prompt(context)
        response = await self._send_input(system_prompt, user_input)
        return self._parse_response(response)

    def _prepare_system_prompt(self, context: Mapping[str, Any]) -> str:
        return self._SYSTEM_PROMPT.format(**context)

    def _parse_response(self, chat_completion_response: ChatCompletion | None) -> ReminderParamsExtracted | None:
        if not chat_completion_response:
            return None

        message = chat_completion_response.choices[0].message
        if not message.tool_calls:
            logger.error("No tool calls returned by the model.")
            return None

        try:
            raw_json_arguments = message.tool_calls[0].function.arguments
        except IndexError:
            logger.error("No arguments returned by the model.")
            return None


        # 6. Validate the raw JSON against our Pydantic model
        try:
            validated_data = ReminderParamsExtracted.model_validate_json(raw_json_arguments)
            return validated_data
        except ValidationError as e:
            # If the LLM hallucinated the format, Pydantic catches it here
            logger.error(f"Pydantic Validation Error:\n{e.json()}")
            return None

    async def _send_input(self, system_prompt: str, user_input: str) -> ChatCompletion | None:
        try:
            return await self._llm_client.chat.completions.create(  # type: ignore
                # model="llama-3.1-8b-instant", # The fastest and cheapest model for tool calling
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                tools=self._tools,
                tool_choice={"type": "function", "function": {"name": "extract_reminder_parameters"}},
                temperature=0.1,
            )
        except Exception as exc:
            logger.error(f"API Error: {exc}")

        return None


class DatetimeHelper:
    _WEEKDAY_MAP = {
        Weekday.MONDAY: 0,
        Weekday.TUESDAY: 1,
        Weekday.WEDNESDAY: 2,
        Weekday.THURSDAY: 3,
        Weekday.FRIDAY: 4,
        Weekday.SATURDAY: 5,
        Weekday.SUNDAY: 6,
    }

    @classmethod
    def calculate_send_at(cls, reminder_params: ReminderParamsExtracted) -> int:
        now = datetime.now()
        send_at_dt: datetime = now

        if reminder_params.exact_time_iso:
            send_at_dt = datetime.fromisoformat(reminder_params.exact_time_iso)

        elif reminder_params.target_weekday:
            target_idx = cls._WEEKDAY_MAP[reminder_params.target_weekday]
            current_idx = now.weekday()

            days_ahead = target_idx - current_idx
            if days_ahead < 0:
                days_ahead += WEEK_LENGTH

            target_time = reminder_params.target_time or DEFAULT_TIME_OF_DAY
            hh, mm = map(int, target_time.split(":"))

            # Shift to next week if the target time today has already passed
            if days_ahead == 0:
                if now.hour > hh or (now.hour == hh and now.minute >= mm):
                    days_ahead += WEEK_LENGTH

            if reminder_params.is_next_week:
                days_ahead += WEEK_LENGTH

            send_at_dt = now + timedelta(days=days_ahead)
            send_at_dt = send_at_dt.replace(hour=hh, minute=mm, second=0, microsecond=0)

        elif reminder_params.start_in_unit and reminder_params.start_in_value:
            value = reminder_params.start_in_value
            match reminder_params.start_in_unit:
                case TimeUnit.MINUTES:
                    send_at_dt = now + timedelta(minutes=value)
                case TimeUnit.HOURS:
                    send_at_dt = now + timedelta(hours=value)
                case TimeUnit.DAYS:
                    send_at_dt = now + timedelta(days=value)
                case TimeUnit.WEEKS:
                    send_at_dt = now + timedelta(weeks=value)
                case TimeUnit.MONTHS:
                    send_at_dt = now + timedelta(days=value * 30)

        return int(send_at_dt.timestamp())

    @staticmethod
    def calculate_repeat_seconds(unit: TimeUnit | None, value: int | None) -> int:
        if not unit or not value:
            return 0

        match unit:
            case TimeUnit.MINUTES:
                return value * 60
            case TimeUnit.HOURS:
                return value * 3600
            case TimeUnit.DAYS:
                return value * 86400
            case TimeUnit.WEEKS:
                return value * 604800
            case TimeUnit.MONTHS:
                return value * 30 * 86400 

        return 0


class ReminderService:
    def __init__(self, client: AsyncGroq) -> None:
        self._llm_helper = LLMHelper(client)
        self._datetime_helper = DatetimeHelper()

    async def parse_reminder_input(self, user_input: str) -> ReminderParamsExtracted | None:
        # 3. Generate dynamic context for the system prompt
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        day_after = now + timedelta(days=2)

        current_context_dates = {
            "today_datetime": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "today_weekday": now.strftime("%A"),
            "tomorrow_date": tomorrow.strftime("%Y-%m-%d"),
            "tomorrow_weekday": tomorrow.strftime("%A"),
            "day_after_tomorrow_date": day_after.strftime("%Y-%m-%d"),
            "day_after_tomorrow_weekday": day_after.strftime("%A"),
        }

        extracted_reminder_params = await self._llm_helper.extract_reminder_params(current_context_dates, user_input)
        if extracted_reminder_params:
            logger.info(f"Reminder extracted params: {extracted_reminder_params}")
        else:
            logger.info("Failed to extract reminder params")

        return extracted_reminder_params

    def build_reminder_notification(self, chat_id: int, data: ReminderParamsExtracted) -> Notification:
        return Notification(
            text=data.text,
            send_at=self._datetime_helper.calculate_send_at(data),
            repeat_in=self._datetime_helper.calculate_repeat_seconds(data.repeat_unit, data.repeat_value),
            send_count=data.send_count,
            chat_id=str(chat_id)
        )
