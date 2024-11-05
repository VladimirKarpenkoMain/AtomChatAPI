from operator import or_

from pydantic import UUID4, EmailStr
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.auth.models import Blocked, User
from app.core.dao import BaseDao
from app.core.database import async_session_maker


# DAO-класс для работы с пользователями в базе данных
class UsersDao(BaseDao):
    model = User

    # Метод для обновления refresh-токена пользователя
    @classmethod
    async def update_refresh_token(cls, user_id: UUID4, token: str):
        """
        Обновляет refresh-токен для указанного пользователя.
        :param user_id: UUID4 идентификатор пользователя
        :param token: Новый refresh-токен
        """
        try:
            async with async_session_maker() as session:
                # Находим пользователя по ID
                query = select(cls.model).filter_by(id=user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()

                # Обновляем refresh-токен и сохраняем изменения
                user.refresh_token = token
                await session.commit()
        except (SQLAlchemyError, Exception) as e:
            # Логируем ошибку, если обновление не удалось
            cls._log_error(
                e,
                error_message=f"Cannot update refresh token, model {cls.model.__name__}",
                extra={"user_id": user_id, "token": token},
            )

    # Метод для поиска пользователя по email или имени пользователя
    @classmethod
    async def find_by_email_or_username(cls, email: EmailStr, username: str):
        """
        Ищет пользователя по email или username.
        :param email: Email пользователя
        :param username: Username пользователя
        :return: Объект пользователя, если найден, иначе None
        """
        try:
            async with async_session_maker() as session:
                # Выполняем поиск по email или username
                query = select(cls.model).where(
                    or_(cls.model.email == email, cls.model.username == username)
                )
                result = await session.execute(query)
                users = result.scalar_one_or_none()
                return users
        except (SQLAlchemyError, Exception) as e:
            # Логируем ошибку, если поиск не удался
            cls._log_error(
                e,
                error_message=f"Cannot find by email or username, model {cls.model.__name__}",
                extra={"email": email, "username": username},
            )

    # Метод для получения пользователей, участвующих в одном чате
    @classmethod
    async def find_users_for_chat(cls, user_1_id: UUID4, user_2_id: UUID4):
        """
        Находит двух пользователей по их ID для чата.
        :param user_1_id: ID первого пользователя
        :param user_2_id: ID второго пользователя
        :return: Список из найденных пользователей (до двух пользователей)
        """
        try:
            async with async_session_maker() as session:
                # Находим пользователей, чьи ID совпадают с указанными
                query = select(cls.model).where(
                    or_(cls.model.id == user_1_id, cls.model.id == user_2_id)
                )
                result = await session.execute(query)
                users = result.scalars().all()
                return users
        except (SQLAlchemyError, Exception) as e:
            # Логируем ошибку, если поиск не удался
            cls._log_error(
                e,
                error_message=f"Cannot find users for chat, model {cls.model.__name__}",
                extra={"user_1_id": user_1_id, "user_2_id": user_2_id},
            )

    # Метод для поиска пользователей по username с пагинацией
    @classmethod
    async def find_by_username(cls, username: str, limit: int, offset: int):
        """
        Ищет пользователей, чьи username соответствуют шаблону.
        :param username: Часть или полный username для поиска
        :param limit: Ограничение на количество результатов
        :param offset: Смещение для пагинации
        :return: Список найденных пользователей
        """
        try:
            async with async_session_maker() as session:
                # Выполняем поиск пользователей с username, соответствующим шаблону
                query = (
                    select(cls.model)
                    .where(cls.model.username.ilike(f"%{username}%"))
                    .limit(limit)
                    .offset(offset)
                )
                result = await session.execute(query)
                users = result.scalars().all()
                return users
        except (SQLAlchemyError, Exception) as e:
            # Логируем ошибку, если поиск не удался
            cls._log_error(
                e,
                error_message=f"Cannot find {cls.model.__name__} by username",
                extra={"username": username, "limit": limit, "offset": offset},
            )


# DAO-класс для работы с заблокированными пользователями
class BlockDao(BaseDao):
    model = Blocked
