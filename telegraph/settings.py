from app.plugins.base import PluginSettings


class TelegraphPluginSettings(PluginSettings):
    NAME = "TELEGRAPH"

    hosts: list[str]


settings = TelegraphPluginSettings()  # type: ignore