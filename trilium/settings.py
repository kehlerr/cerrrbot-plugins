from decouple import config
from settings import SCHEME

# Trilium settings
## Trilium basics
TRILIUM_TOKEN = config("CERRRBOT_TRILIUM_TOKEN", default="")
TRILIUM_HOST = config("CERRRBOT_TRILIUM_HOST", default="localhost")
TRILIUM_PORT = config("CERRRBOT_TRILIUM_PORT", default=8080, cast=int)
TRILIUM_URL = f"{SCHEME}://{TRILIUM_HOST}:{TRILIUM_PORT}"
## Notebooks IDs
TRILIUM_NOTE_ID_BOOK_ROOT = config("CERRRBOT_TRILIUM_NOTE_ID_BOOK_ROOT", default=None)
TRILIUM_NOTE_ID_BOOKMARKS_URL = config("CERRRBOT_TRILIUM_NOTE_ID_BOOKMARKS_URL", default=None)
TRILIUM_NOTE_ID_BOOK_NOTES_ALL = config("CERRRBOT_TRILIUM_NOTE_ID_BOOK_NOTES_ALL", default=None)
TRILIUM_NOTE_ID_TODO = config("CERRRBOT_TRILIUM_NOTE_ID_TODO", default=None)
