from datetime import datetime

from pydantic import UUID4
from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from app.auth.models import User
from app.chat.models import Message
from app.core.config import settings
from app.core.dao import BaseDao
from app.core.database import async_session_maker


class MessageDAO(BaseDao):
    """
    Data Access Object (DAO) для работы с сообщениями пользователей.
    """

    model = Message

    @classmethod
    async def get_chats_of_user(
        cls,
        current_user_id: UUID4,
        cursor_last_message_time: datetime,
        limit: int = settings.BASE_LIMIT_CHATS_FOR_USER,
    ):
        """
        Получить чаты текущего пользователя с последними сообщениями.

        Этот метод извлекает список уникальных чатов для указанного пользователя,
        сортируя их по времени последнего сообщения.

        :param current_user_id: UUID текущего пользователя.
        :param cursor_last_message_time: Метка времени для пагинации.
        :param limit: Максимальное количество записей для возврата.
        :return: Список чатов с данными о пользователе и времени последнего сообщения.
        """
        async with async_session_maker() as session:
            try:
                # Подзапрос для получения партнера по чату и времени последнего сообщения
                sub_query = (
                    select(
                        case(
                            (
                                cls.model.sender_id == current_user_id,
                                cls.model.recipient_id,
                            ),
                            else_=cls.model.sender_id,
                        ).label("chat_partner_id"),
                        func.max(cls.model.created_at).label("last_message_time"),
                    )
                    .where(
                        or_(
                            cls.model.sender_id == current_user_id,
                            cls.model.recipient_id == current_user_id,
                        )
                    )
                    .group_by("chat_partner_id")
                    .subquery()
                )

                # Основной запрос для получения чатов и информации о пользователе
                query = select(
                    sub_query.c.chat_partner_id,
                    User.username,
                    sub_query.c.last_message_time,
                ).join(User, User.id == sub_query.c.chat_partner_id)

                # Добавление фильтра для пагинации
                if cursor_last_message_time:
                    query = query.where(
                        sub_query.c.last_message_time < cursor_last_message_time
                    )

                # Сортировка по времени последнего сообщения и ограничение количества записей
                query = query.order_by(desc(sub_query.c.last_message_time)).limit(limit)

                # Выполнение запроса и возврат результата
                result = await session.execute(query)
                chats = result.all()
                return chats
            except (SQLAlchemyError, Exception) as e:
                # Логирование ошибок
                cls._log_error(
                    e,
                    error_message=f"Не удалось получить чаты пользователя, модель {cls.model.__name__}",
                    extra={
                        "current_user_id": str(current_user_id),
                        "cursor_last_message_time": str(cursor_last_message_time),
                        "limit": limit,
                    },
                )

    @classmethod
    async def get_messages_between_users(
        cls,
        current_user_id: UUID4,
        participant_user_id: UUID4,
        cursor_time: datetime | None = None,
        cursor_message_id: int | None = None,
        limit: int = settings.BASE_LIMIT_MESSAGES_FOR_USER,
    ):
        """
        Получить сообщения между двумя пользователями.

        Этот метод возвращает список сообщений между текущим пользователем и другим пользователем,
        с возможностью пагинации по времени и ID сообщения.

        :param current_user_id: UUID текущего пользователя.
        :param participant_user_id: UUID второго участника чата.
        :param cursor_time: Метка времени для пагинации.
        :param cursor_message_id: ID сообщения для пагинации.
        :param limit: Максимальное количество записей для возврата.
        :return: Список сообщений с данными о тексте, отправителе и времени создания.
        """
        async with async_session_maker() as session:
            try:
                # Основной запрос для получения сообщений между пользователями
                query = select(
                    cls.model.id,
                    cls.model.message_text,
                    cls.model.sender_id,
                    cls.model.created_at,
                ).where(
                    or_(
                        and_(
                            cls.model.sender_id == current_user_id,
                            cls.model.recipient_id == participant_user_id,
                        ),
                        and_(
                            cls.model.sender_id == participant_user_id,
                            cls.model.recipient_id == current_user_id,
                        ),
                    )
                )

                # Добавление условий для пагинации
                if cursor_time and cursor_message_id:
                    query = query.where(
                        or_(
                            cls.model.created_at < cursor_time,
                            and_(
                                cls.model.created_at == cursor_time,
                                cls.model.id < cursor_message_id,
                            ),
                        )
                    )

                # Сортировка по времени создания сообщения и ограничение количества записей
                query = query.order_by(desc(cls.model.created_at)).limit(limit)

                # Выполнение запроса и возврат результата
                result = await session.execute(query)
                messages = result.all()
                return messages
            except (SQLAlchemyError, Exception) as e:
                # Логирование ошибок
                cls._log_error(
                    e,
                    error_message=f"Не удалось получить сообщения между пользователями, модель {cls.model.__name__}",
                    extra={
                        "current_user_id": current_user_id,
                        "participant_user_id": participant_user_id,
                        "cursor_time": cursor_time,
                        "cursor_message_id": cursor_message_id,
                        "limit": limit,
                    },
                )

    @classmethod
    async def get_all_users_chats(cls, limit: int, offset: int):
        """
        Получить все чаты между пользователями.

        Этот метод извлекает список всех уникальных чатов между пользователями,
        с информацией о каждом участнике и времени последнего сообщения.

        :param limit: Максимальное количество записей для возврата.
        :param offset: Смещение для пагинации.
        :return: Список чатов с данными о пользователях и времени последнего сообщения.
        """
        try:
            async with async_session_maker() as session:
                # Создание алиасов для отправителя и получателя
                sender = aliased(User)
                recipient = aliased(User)

                # Подзапрос для получения уникальных пар пользователей и времени последнего сообщения
                sub_query = (
                    select(
                        func.least(cls.model.sender_id, cls.model.recipient_id).label(
                            "user1_id"
                        ),
                        func.greatest(
                            cls.model.sender_id, cls.model.recipient_id
                        ).label("user2_id"),
                        func.max(cls.model.created_at).label("last_message_time"),
                    )
                    .group_by("user1_id", "user2_id")
                    .subquery()
                )

                # Основной запрос для получения чатов и информации о пользователях
                query = (
                    select(
                        sub_query.c.user1_id,
                        sender.username.label("user1_username"),
                        sub_query.c.user2_id,
                        recipient.username.label("user2_username"),
                        sub_query.c.last_message_time,
                    )
                    .join(sender, sender.id == sub_query.c.user1_id)
                    .join(recipient, recipient.id == sub_query.c.user2_id)
                    .order_by(desc(sub_query.c.last_message_time))
                    .limit(limit)
                    .offset(offset)
                )

                # Выполнение запроса и возврат результата
                result = await session.execute(query)
                all_chats = result.all()
                return all_chats
        except (SQLAlchemyError, Exception) as e:
            # Логирование ошибок
            cls._log_error(
                e,
                error_message=f"Не удалось получить все чаты между пользователями, модель {cls.model.__name__}",
                extra={"offset": offset, "limit": limit},
            )
