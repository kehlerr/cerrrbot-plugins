from pydantic import Field

from app.plugins.base import PluginSettings


class TriliumSettings(PluginSettings):
    NAME = "TRILIUM"

    token: str
    scheme: str = Field(default="http")
    host: str
    port: int

    note_id_book_root: str
    note_id_bookmarks_url: str
    note_id_book_notes_all: str
    note_id_todo: str

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


settings = TriliumSettings()  # type: ignore
