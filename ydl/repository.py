
from repositories.cache import CacheRepositoryBase

from repositories.exceptions import EntryNotFoundError
from .models import YDLCommandArgs


class YDLArgsRepository(CacheRepositoryBase):
    model_cls = YDLCommandArgs
    KEY_PREFIX = "YDL"

    async def is_exists(self, request_id: str, request: YDLCommandArgs) -> bool:
        try:
            await self.select(request_id)
        except EntryNotFoundError:
            ...
        else:
            return True

        all_requests = await self.get_all()
        for stored_request in all_requests.values():
            if request.url == stored_request.url:
                return True

        return False


_repo: YDLArgsRepository | None = None


async def get_repo() -> YDLArgsRepository:
    global _repo
    if _repo is None:
        _repo = YDLArgsRepository()
        await _repo.init_client()
    return _repo