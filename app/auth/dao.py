from operator import or_

from pydantic import UUID4, EmailStr

from app.core.dao import BaseDao
from app.auth.models import User, Blocked
from app.core.database import async_session_maker
from sqlalchemy import select


class UsersDao(BaseDao):
    model = User

    @classmethod
    async def update_refresh_token(cls, user_id: UUID4, token: str):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            user.refresh_token = token
            await session.commit()

    @classmethod
    async def find_by_email_or_username(cls, email: EmailStr, username: str):
        async with async_session_maker() as session:
            query = select(cls.model).where(
                or_(
                    cls.model.email == email,
                    cls.model.username == username
                )
            )
            result = await session.execute(query)
            users = result.scalar_one_or_none()
            return users

    @classmethod
    async def find_users_for_chat(cls, user_1_id: UUID4, user_2_id: UUID4):
        async with async_session_maker() as session:
            query = select(cls.model).where(
                or_(
                    cls.model.id == user_1_id,
                    cls.model.id == user_2_id
                )
            )
            result = await session.execute(query)
            users = result.scalars().all()
            return users

    @classmethod
    async def find_by_username(cls, username: str, limit: int, offset: int):
        async with async_session_maker() as session:
            query = select(cls.model).where(
                cls.model.username.ilike(f"%{username}%")
            ).limit(limit).offset(offset)
            result = await session.execute(query)
            users = result.scalars().all()
            return users

class BlockDao(BaseDao):
    model = Blocked
