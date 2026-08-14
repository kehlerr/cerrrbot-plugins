from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from app import app_settings

from ..constants import DEFAULT_TIME_OF_DAY, WEEK_LENGTH, TimeUnit, Weekday
from ..models import ReminderParamsExtracted


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

    def __init__(self, timezone: ZoneInfo | None = None) -> None:
        self._tz = timezone or getattr(app_settings, "tz", ZoneInfo("UTC"))

    def calculate_send_at(self, reminder_params: ReminderParamsExtracted) -> int:
        now = datetime.now(tz=self._tz)
        send_at_dt: datetime = now

        if reminder_params.exact_time_iso:
            parsed_dt = datetime.fromisoformat(reminder_params.exact_time_iso)
            if parsed_dt.tzinfo is None:
                send_at_dt = parsed_dt.replace(tzinfo=self._tz)
            elif parsed_dt.tzinfo == UTC and self._tz != UTC:
                send_at_dt = parsed_dt.replace(tzinfo=None).replace(tzinfo=self._tz)
            else:
                send_at_dt = parsed_dt.astimezone(self._tz)

        elif reminder_params.target_weekday:
            target_idx = self._WEEKDAY_MAP[reminder_params.target_weekday]
            current_idx = now.weekday()

            days_ahead = target_idx - current_idx
            if days_ahead < 0:
                days_ahead += WEEK_LENGTH

            target_time = reminder_params.target_time or DEFAULT_TIME_OF_DAY
            hh, mm = map(int, target_time.split(":"))

            # Shift to next week if the target time today has already passed
            if days_ahead == 0 and (now.hour > hh or (now.hour == hh and now.minute >= mm)):
                days_ahead += WEEK_LENGTH

            if reminder_params.is_next_week:
                if target_idx > current_idx or (target_idx == current_idx and days_ahead == 0):
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
                    send_at_dt = now + relativedelta(months=value)

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
