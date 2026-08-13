import os

from pydantic import Field

from app import app_settings
from app.plugins.base import PluginSettings


class YdlSettings(PluginSettings):
    NAME = "YDL"

    v_hosts: list[str] = Field(default_factory=list)
    s_hosts: list[str] = Field(default_factory=list)
    data_directory: str = Field(default_factory=lambda: os.path.join(app_settings.data_root, "YDL"))
    default_timeout: int = Field(default=1800)
    max_timeout: int = Field(default=43200)


settings = YdlSettings()  # type: ignore
