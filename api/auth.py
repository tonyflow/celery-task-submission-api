import logging

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from cache import instance as cache_instance
from models import UserResponseBase, CachedUserValue

_logger = logging.getLogger(__name__)

security = HTTPBearer()

USERS_CACHE_REGION = "users"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token.

    Utility function to retrieve the user trying to access the API based on the provided bearer
    token and the stored API key.

    Important!!! The cache is here to showcase how the database can be alleviated from certain
    requests. Nevertheless, this cache is not updated and when relying on state - like credits - from
    stale data, it can lead to inconsistencies. Because of this the cache in this implementation is
    primarily user to retrieve metadata like name and API keys which are not updated.

    It is not used to rely on the amount of credits a user may have.
    """
    # 1. Extract credentials
    token = credentials.credentials

    # 2. Try to avoid database hop by checking the cache first
    cached_user = cache_instance.hget(USERS_CACHE_REGION, token)
    if cached_user is not None:
        cached_user_value = CachedUserValue.model_validate_json(cached_user)
        return CachedUserValue.model_validate_json(cached_user)

    # 3. Proceed to the database
    async with async_session() as session:
        result = await session.execute(select(User).where(User.api_key == token))
        user = result.scalar_one_or_none()

        # 4. Raise if no user is found
        if not user:
            _logger.error(f"User with api_key {token[:3]}... not found")
            raise HTTPException(status_code=401, detail="Unauthorized")

        # 5. Update the cache with the user
        # 5.1 Convert user to pydantic cached value that we can serialize
        cached_user_value = CachedUserValue.model_validate(user)
        # 5.2 Write to cache
        cache_instance.hset(
            name=USERS_CACHE_REGION,
            key=token,
            value=cached_user_value.model_dump_json()
        )

        return user
