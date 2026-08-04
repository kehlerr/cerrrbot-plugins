from app.infrastructure import make_redis_client
from app.repositories.cached_model_repository import CachedModelRepository
from app.repositories.exceptions import EntryNotFoundError

from .models import YDLCommandArgs


class YDLArgsRepository(CachedModelRepository[YDLCommandArgs]):
    model_class = YDLCommandArgs
    KEY_PREFIX = "YDL"

    async def is_exists(self, request_id: str, request: YDLCommandArgs) -> bool:
        try:
            await self.select(request_id)
        except EntryNotFoundError:
            ...
        else:
            return True

        async for _, stored_request in self.iter_all():
            if str(request.url) == str(stored_request.url):
                return True

        return False


async def get_repo() -> YDLArgsRepository:
    redis_client = await make_redis_client()
    return YDLArgsRepository(redis_client)
