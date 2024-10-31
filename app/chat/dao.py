from datetime import datetime

from dns.e164 import query
from pydantic import UUID4
from sqlalchemy import select, case, func, desc, or_, and_
from sqlalchemy.orm import aliased
from app.core.config import settings

from app.core.database import async_session_maker
from app.core.dao import BaseDao
from app.chat.models import Message
from app.auth.models import User


class MessageDAO(BaseDao):
    model = Message

    @classmethod
    async def get_chats_of_user(
            cls,
            current_user_id: UUID4,
            cursor_last_message_time: datetime,
            limit: int = settings.BASE_LIMIT_CHATS_FOR_USER
    ):
        async with async_session_maker() as session:
            """
            запрос
            SELECT
                CASE WHEN
                    sender_id = current_user_id
                THEN
                    recipient_id
                ELSE
                    sender_id
                END AS chat_partner_id,
                MAX(created_at) as last_message_time FROM messages
            WHERE sender_id=current_user_id
            OR recipient_id=current_user_id
            GROUP BY chat_partner_id
            ORDER by last_message_time DESC;
            """
            sub_query = select(
                case(
                    (
                        cls.model.sender_id == current_user_id,
                        cls.model.recipient_id
                    ), else_=cls.model.sender_id).label('chat_partner_id'),
                func.max(cls.model.created_at).label('last_message_time')
            ).where(
                or_(
                    cls.model.sender_id == current_user_id,
                    cls.model.recipient_id == current_user_id
                )
            ).group_by('chat_partner_id').subquery()

            query = select(
                sub_query.c.chat_partner_id,
                User.username,
                sub_query.c.last_message_time
            ).join(
                User, User.id == sub_query.c.chat_partner_id
            )

            if cursor_last_message_time:
                query = query.where(
                    sub_query.c.last_message_time < cursor_last_message_time
                )

            query = query.order_by(
                desc(sub_query.c.last_message_time)
            ).limit(limit)

            result = await session.execute(query)
            chats = result.all()
            return chats

    @classmethod
    async def get_messages_between_users(
            cls, current_user_id,
            participant_user_id,
            cursor_time: datetime = None,
            cursor_message_id: int = None,
            limit=settings.BASE_LIMIT_MESSAGES_FOR_USER
    ):
        async with (async_session_maker() as session):
            query = select(
                cls.model.id,
                cls.model.message_text,
                cls.model.sender_id,
                cls.model.created_at,
            ).where(
                or_(
                    and_(
                        cls.model.sender_id == current_user_id,
                        cls.model.recipient_id == participant_user_id
                    ),
                    and_(
                        cls.model.sender_id == participant_user_id,
                        cls.model.recipient_id == current_user_id
                    )
                )
            )

            if cursor_time and cursor_message_id:
                query = query.where(
                    or_(
                        cls.model.created_at < cursor_time,
                        and_(
                            cls.model.created_at == cursor_time,
                            cls.model.id < cursor_message_id
                        )
                    )
                )

            query = query.order_by(
                desc(cls.model.created_at)
            ).limit(limit)

            result = await session.execute(query)
            messages = result.all()
            return messages

    @classmethod
    async def get_all_users_chats(cls, limit: int, offset: int):
        async with async_session_maker() as session:
            # Создаем алиасы для отправителя и получателя для удобства
            sender = aliased(User)
            recipient = aliased(User)

            # Подзапрос для получения уникальных пар пользователей и времени последнего сообщения
            sub_query = select(
                func.least(cls.model.sender_id, cls.model.recipient_id).label("user1_id"),
                func.greatest(cls.model.sender_id, cls.model.recipient_id).label("user2_id"),
                func.max(cls.model.created_at).label("last_message_time")
            ).group_by("user1_id", "user2_id").subquery()

            # Основной запрос для получения чатов
            query = select(
                sub_query.c.user1_id,
                sender.username.label("user1_username"),
                sub_query.c.user2_id,
                recipient.username.label("user2_username"),
                sub_query.c.last_message_time
            ).join(
                sender, sender.id == sub_query.c.user1_id
            ).join(
                recipient, recipient.id == sub_query.c.user2_id
            ).order_by(
                desc(sub_query.c.last_message_time)
            ).limit(limit).offset(offset)

            result = await session.execute(query)
            all_chats = result.all()
            return all_chats
