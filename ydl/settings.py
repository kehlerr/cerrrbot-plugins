import os

from pydantic import Field

from app.plugins.base import PluginSettings
from app import app_settings


class YdlSettings(PluginSettings):
    NAME = "YDL"

    hosts: list[str] = Field(default_factory=list)
    data_directory: str = Field(default_factory=lambda: os.path.join(app_settings.data_root, "YDL"))
    default_timeout: int = Field(default=1800)
    max_timeout: int = Field(default=43200)


settings = YdlSettings()  # type: ignore
