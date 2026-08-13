from app.exceptions import AppError


class ReminderError(AppError):
    pass


class FailedParsingReminderError(ReminderError):
    detail = "Failed to parse reminder parameters."
