from pydantic import Field
from app.plugins.base import PluginSettings


class ReminderSettings(PluginSettings):
    NAME = "reminder"

    groq_api_key: str
    groq_model: str = Field(default="llama-3.3-70b-versatile")
