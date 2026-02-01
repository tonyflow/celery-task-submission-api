import logging

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from database.engine import async_session
from database.models import User

_logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token.

    Utility function to retrieve the user trying to access the API based on the provided bearer
    token.
    """
    token = credentials.credentials
    async with async_session() as session:
        result = await session.execute(select(User).where(User.api_key == token))
        user = result.scalar_one_or_none()

        if not user:
            _logger.error(f"User with api_key {token[:3]}... not found")
            raise HTTPException(status_code=401, detail="Unauthorized")

        return user
