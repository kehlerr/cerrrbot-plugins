from pydantic import BaseModel, Field

from .constants import TimeUnit, Weekday


class ReminderParamsExtracted(BaseModel):
    text: str = Field(
        description="The extracted reminder text in the original Russian language without bot commands or time/date references."
    )

    exact_time_iso: str | None = Field(
        default=None,
        description="ISO 8601 datetime string. Use ONLY for exact calendar dates or 'today/tomorrow' with a specific time (e.g., '2026-05-18T20:00:00')."
    )

    target_time: str | None = Field(
        default=None,
        description="Time in HH:MM format. If time is not explicitly stated, use '12:00'."
    )

    target_weekday: Weekday | None = Field(
        default=None,
        description="Target day of the week."
    )

    is_next_week: bool | None = Field(
        default=False,
        description="Set to true ONLY if the user explicitly says 'next' or 'next week'."
    )

    start_in_unit: TimeUnit | None = Field(
        default=None,
        description="Unit of time for relative start intervals. Use this for 'in X' (через X)."
    )

    start_in_value: int | None = Field(
        default=None,
        description="Numeric value for the relative start interval (e.g., 10 for 'in 10 days')."
    )

    repeat_unit: TimeUnit | None = Field(
        default=None,
        description="ONLY for RECURRING tasks (e.g., 'every day', 'каждый', 'daily'). Must be null for one-time reminders."
    )

    repeat_value: int | None = Field(
        default=None,
        description="Interval value for repeating tasks (e.g., 1 for 'every day')."
    )

    send_count: int = Field(
        default=1,
        description="Number of times to send. Set to -1 for infinitely repeating (periodic) tasks. Otherwise set to 1."
    )