from pydantic import Field

from app.plugins.base import PluginSettings


class ReminderSettings(PluginSettings):
    NAME = "REMINDER"

    groq_api_key: str | None = Field(default=None)
    groq_model: str = Field(default="llama-3.3-70b-versatile")
