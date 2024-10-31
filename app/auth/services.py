from pydantic import UUID4

from app.auth.dao import BlockDao
from app.core.exceptions import UserIsAlreadyBlockedException


class BlockService:
    @classmethod
    async def block_user(cls, user_id: UUID4, moderator_id: UUID4, reason: str):
        user = await BlockDao.find_one_or_none(blocked_user_id=user_id)
        if user:
            raise UserIsAlreadyBlockedException
        await BlockDao.add(blocked_user_id=user_id, reason=reason, moderator_id=moderator_id)
        response_data = {
            "detail": "The user has been blocked.",
            "blocked_user_id": user_id
        }
        return response_data