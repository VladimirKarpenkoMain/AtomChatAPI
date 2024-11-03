import asyncio
from app.core.database import async_session_maker
from app.auth.models import User
from app.chat.models import Message
from app.auth.auth_utilits import get_password_hash
from sqlalchemy import text
import uuid
from datetime import datetime

from app.core.logger import logger


async def add_test_users():
    async with async_session_maker() as session:
        existing_users = await session.execute(text("SELECT * FROM users LIMIT 1"))
        if existing_users.scalar() is not None:
            logger.info("The test data already exists.")
            return

        # Создаем трех пользователей
        user1 = User(
            id=uuid.uuid4(),
            username="test_user1",
            email="test1@example.com",
            hashed_password=get_password_hash("test_password_1"),
            is_moderator=False
        )
        user2 = User(
            id=uuid.uuid4(),
            username="test_user2",
            email="test2@example.com",
            hashed_password=get_password_hash("test_password_2"),
            is_moderator=False
        )
        user3 = User(
            id=uuid.uuid4(),
            username="test_moderator",
            email="moderator@example.com",
            hashed_password=get_password_hash("moderator_password_3"),
            is_moderator=True
        )

        session.add_all([user1, user2, user3])
        await session.commit()
        logger.info("Test users have been successfully added.")

        # Добавляем по 10 сообщений между пользователями
        await add_test_messages(session, user1, user2)
        await add_test_messages(session, user1, user3)
        await add_test_messages(session, user2, user3)


async def add_test_messages(session, sender, recipient):
    messages = []
    for i in range(10):
        message = Message(
            message_text=f"Тестовое сообщение {i + 1} от {sender.username} к {recipient.username}",
            sender_id=sender.id,
            recipient_id=recipient.id,
            created_at=datetime.utcnow()
        )
        messages.append(message)

    session.add_all(messages)
    await session.commit()
    logger.info(f"Messages between {sender.username} and {recipient.username} have been successfully added.")


if __name__ == "__main__":
    asyncio.run(add_test_users())
