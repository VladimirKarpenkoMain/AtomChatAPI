from datetime import datetime

from pydantic import UUID4
from sqlalchemy.exc import IntegrityError

from app.auth.dao import UsersDao
from app.chat.dao import MessageDAO
from app.chat.shemas import SWebsocketMessage
from app.core.exceptions import (
    OneUserIdNotFoundException,
    UserMessagesBetweenSameException,
    UserMessagesBetweenYourselfException,
    UserSearchNotFoundException,
    UsersIdNotFoundException,
)


class ChatService:
    """
    Сервисный слой для работы с чатами и сообщениями. Содержит методы для получения и добавления сообщений,
    а также для поиска пользователей по имени.
    """

    @staticmethod
    async def get_all_chats_for_user(
        current_user_id: UUID4, cursor_last_message_time: datetime
    ):
        """
        Получить список всех чатов для текущего пользователя с последними сообщениями.

        :param current_user_id: UUID текущего пользователя.
        :param cursor_last_message_time: Метка времени для пагинации.
        :return: Словарь с информацией о чатах и курсором для пагинации.
        """
        # Получение сырых данных чатов с использованием DAO
        raw_chats = await MessageDAO.get_chats_of_user(
            current_user_id, cursor_last_message_time=cursor_last_message_time
        )

        # Форматирование результата
        chats = {
            "chats": [
                {
                    "partner_id": chat.chat_partner_id,
                    "partner_username": chat.username,
                    "last_message_time": chat.last_message_time,
                }
                for chat in raw_chats
            ],
            # Определение курсора для следующей пагинации
            "cursor_last_message_time": (
                None if not raw_chats else raw_chats[-1].last_message_time
            ),
        }
        return chats

    @staticmethod
    async def get_messages_between_users(
        user_1_id: UUID4,
        user_2_id: UUID4,
        cursor_time: datetime,
        cursor_message_id: int,
        moder_flag: bool = False,
    ):
        """
        Получить сообщения между двумя пользователями.

        :param user_1_id: UUID первого пользователя.
        :param user_2_id: UUID второго пользователя.
        :param cursor_time: Метка времени для пагинации.
        :param cursor_message_id: ID сообщения для пагинации.
        :param moder_flag: Флаг модерации, определяет, кто текущий пользователь.
        :raises UserMessagesBetweenSameException: Исключение при попытке получить сообщения между одним и тем же пользователем.
        :raises UsersIdNotFoundException: Исключение, если не найдены оба пользователя.
        :raises OneUserIdNotFoundException: Исключение, если найден только один пользователь.
        :return: Словарь с информацией о пользователях и сообщениях.
        """
        # Проверка на попытку получения сообщений между одним и тем же пользователем
        if user_1_id == user_2_id:
            raise UserMessagesBetweenSameException

        # Поиск пользователей в базе данных
        users = await UsersDao.find_users_for_chat(user_1_id, user_2_id)
        if not users:
            raise UsersIdNotFoundException
        if len(users) == 1:
            raise OneUserIdNotFoundException(user_id=users[0].id)

        # Получение сообщений между пользователями
        raw_messages = await MessageDAO.get_messages_between_users(
            user_1_id, user_2_id, cursor_time, cursor_message_id
        )

        # Создание словаря для отображения ID пользователя на имя
        users_map = {user.id: user.username for user in users}
        return {
            "participants": [
                {
                    "participant_id": user_1_id,
                    "is_current_user": True if not moder_flag else False,
                },
                {"participant_id": user_2_id, "is_current_user": False},
            ],
            # Форматирование списка сообщений
            "messages": [
                {
                    "sender_id": message.sender_id,
                    "username": users_map.get(message.sender_id),
                    "message_text": message.message_text,
                    "created_at": message.created_at,
                }
                for message in raw_messages
            ],
            # Определение курсоров для следующей пагинации
            "cursor_time": None if not raw_messages else raw_messages[-1].created_at,
            "cursor_message_id": None if not raw_messages else raw_messages[-1].id,
        }

    @classmethod
    async def add_message(cls, message: SWebsocketMessage, sender_id: UUID4):
        """
        Добавить новое сообщение в базу данных.

        :param message: Данные сообщения.
        :param sender_id: UUID отправителя.
        :raises UserMessagesBetweenYourselfException: Исключение при попытке отправить сообщение самому себе.
        :raises OneUserIdNotFoundException: Исключение, если получатель не найден.
        :return: Словарь со статусом операции.
        """
        # Проверка на попытку отправки сообщения самому себе
        if sender_id == message.recipient_id:
            raise UserMessagesBetweenYourselfException
        try:
            # Добавление сообщения с использованием DAO
            await MessageDAO.add(
                message_text=message.message_text,
                sender_id=sender_id,
                recipient_id=message.recipient_id,
            )
            return {
                "status": "success",
            }
        except IntegrityError:
            # Обработка ошибки целостности данных, если получатель не найден
            raise OneUserIdNotFoundException(message.recipient_id)

    @classmethod
    async def find_users_by_username(cls, username: str, limit: int, offset: int):
        """
        Найти пользователей по имени.

        :param username: Имя пользователя для поиска.
        :param limit: Максимальное количество записей для возврата.
        :param offset: Смещение для пагинации.
        :raises UserSearchNotFoundException: Исключение, если пользователи не найдены.
        :return: Словарь с информацией о пользователях и данными о пагинации.
        """
        # Поиск пользователей по имени
        raw_users = await UsersDao.find_by_username(username, limit, offset)
        if not raw_users:
            raise UserSearchNotFoundException

        # Расчет нового смещения для пагинации
        new_offset = offset + limit if raw_users else offset
        users = {
            "users": [{"id": user.id, "username": user.username} for user in raw_users],
            "pagination": {
                "limit": limit,
                "current_offset": offset,
                "new_offset": new_offset,
                "is_end": True if len(raw_users) < limit else False,
            },
        }
        return users

    @classmethod
    async def get_all_chats(cls, limit: int, offset: int):
        """
        Получить список всех чатов между пользователями.

        :param limit: Максимальное количество записей для возврата.
        :param offset: Смещение для пагинации.
        :return: Словарь с информацией о чатах и данными о пагинации.
        """
        # Получение всех чатов с использованием DAO
        raw_chats = await MessageDAO.get_all_users_chats(limit, offset)

        # Расчет нового смещения для пагинации
        new_offset = offset + limit if raw_chats else offset
        chats = {
            "chats": [
                {
                    "chat": {
                        "participants": [
                            {"user_id": chat[0], "username": chat[1]},
                            {"user_id": chat[2], "username": chat[3]},
                        ],
                        "last_message_time": chat[4],
                    }
                }
                for chat in raw_chats
            ],
            "pagination": {
                "limit": limit,
                "current_offset": offset,
                "new_offset": new_offset,
                "is_end": True if len(raw_chats) < limit else False,
            },
        }
        return chats
