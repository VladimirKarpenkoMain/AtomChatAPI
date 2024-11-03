from operator import or_
from sqlalchemy.exc import SQLAlchemyError
from pydantic import UUID4, EmailStr
from app.core.dao import BaseDao
from app.auth.models import User, Blocked
from app.core.database import async_session_maker
from sqlalchemy import select

class UsersDao(BaseDao):
    model = User

    @classmethod
    async def update_refresh_token(cls, user_id: UUID4, token: str):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).filter_by(id=user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                user.refresh_token = token
                await session.commit()
        except (SQLAlchemyError, Exception) as e:
            cls._log_error(
                e,
                error_message=f"Cannot update refresh token, model {cls.model.__name__}",
                extra={
                    "user_id": user_id,
                    "token": token
                }
            )


    @classmethod
    async def find_by_email_or_username(cls, email: EmailStr, username: str):
        try:
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
        except (SQLAlchemyError, Exception) as e:
            cls._log_error(
                e,
                error_message=f"Cannot find by email or username, model {cls.model.__name__}",
                extra={
                    "email": email,
                    "username": username
                }
            )

    @classmethod
    async def find_users_for_chat(cls, user_1_id: UUID4, user_2_id: UUID4):
        try:
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
        except (SQLAlchemyError, Exception) as e:
            cls._log_error(
                e,
                error_message=f"Cannot find users for chat, model {cls.model.__name__}",
                extra={
                    "user_1_id": user_1_id,
                    "user_2_id": user_2_id
                }
            )

    @classmethod
    async def find_by_username(cls, username: str, limit: int, offset: int):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).where(
                    cls.model.username.ilike(f"%{username}%")
                ).limit(limit).offset(offset)
                result = await session.execute(query)
                users = result.scalars().all()
                return users
        except (SQLAlchemyError, Exception) as e:
            cls._log_error(
                e,
                error_message=f"Cannot find {cls.model.__name__} by username",
                extra={
                    "username": username,
                    "limit": limit,
                    "offset": offset
                }
            )

class BlockDao(BaseDao):
    model = Blocked