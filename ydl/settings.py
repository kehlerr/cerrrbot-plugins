import os

from decouple import config
from settings import DATA_DIRECTORY_ROOT

cast_to_list = lambda v: [s.strip() for s in v.split(",") if s]

YDLS_HOSTS = config("CERRRBOT_YDLS_HOSTS", default="", cast=cast_to_list)
YDLV_HOSTS = config("CERRRBOT_YDLV_HOSTS", default="", cast=cast_to_list)
del cast_to_list

YDLS_DEFAULT_TIMEOUT = config("CERRRBOT_YDLS_DEFAULT_TIMEOUT", default=1800, cast=float)

YDL_DEFAULT_DIRECTORY_DST = os.path.join(DATA_DIRECTORY_ROOT, "YDL")

DUPLICATED_REQUEST_ERROR_CODE = -10