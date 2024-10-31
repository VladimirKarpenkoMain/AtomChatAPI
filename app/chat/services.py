from datetime import datetime

from pydantic import UUID4
from sqlalchemy.exc import IntegrityError

from app.auth.dao import UsersDao
from app.chat.dao import MessageDAO
from app.chat.shemas import SMessageCreate
from app.chat.websocket import notify_users_about_new_message, notify_chat_list_update
from app.core.exceptions import UserSearchNotFoundException, \
    UserMessagesBetweenYourselfException, UserMessagesBetweenSameException, UsersIdNotFoundException, OneUserIdNotFoundException


class ChatService:

    @staticmethod
    async def get_all_chats_for_user(current_user_id: UUID4, cursor_last_message_time: datetime):
        raw_chats = await MessageDAO.get_chats_of_user(current_user_id, cursor_last_message_time=cursor_last_message_time)
        chats = {
            "chats": [
                {
                    "partner_id": chat.chat_partner_id,
                    "partner_username": chat.username,
                    "last_message_time": chat.last_message_time
                }
                for chat in raw_chats
            ],
            "cursor_last_message_time": None if raw_chats == [] else raw_chats[-1].last_message_time
        }
        return chats

    @staticmethod
    async def get_messages_between_users(
            user_1_id: UUID4,
            user_2_id: UUID4,
            cursor_time: datetime,
            cursor_message_id: int,
            moder_flag: bool = False
    ):
        if user_1_id == user_2_id:
            raise UserMessagesBetweenSameException
        users = await UsersDao.find_users_for_chat(user_1_id, user_2_id)
        if not users:
            raise UsersIdNotFoundException
        if len(users) == 1:
            raise OneUserIdNotFoundException(user_id=users[0].id)

        raw_messages = await MessageDAO.get_messages_between_users(user_1_id, user_2_id, cursor_time, cursor_message_id)
        users_map = {user.id: user.username for user in users}
        return {
            "participants": [
                {
                    "participant_id": user_1_id,
                    "is_current_user": True if not moder_flag else False
                },
                {
                    "participant_id": user_2_id,
                    "is_current_user": False
                }
            ],
            "messages": [
                {
                    "sender_id": message.sender_id,
                    "username": users_map.get(message.sender_id),
                    "message_text": message.message_text,
                    "created_at": message.created_at,
                }
                for message in raw_messages
            ],
            "cursor_time":  None if raw_messages == [] else raw_messages[-1].created_at,
            "cursor_message_id": None if raw_messages == [] else raw_messages[-1].id
        }

    @classmethod
    async def add_message(cls, message: SMessageCreate, current_user_id: UUID4):
        if current_user_id == message.recipient_id:
            raise UserMessagesBetweenYourselfException
        try:
            new_message = await MessageDAO.add(
                message_text=message.message_text,
                sender_id=current_user_id,
                recipient_id=message.recipient_id
            )

            await notify_users_about_new_message(new_message)
            await notify_chat_list_update(current_user_id, new_message.recipient_id, new_message.created_at)
            return {
                "status": "success",
                "sender_id": new_message.sender_id,
                "recipient_id": new_message.recipient_id,
                "message_text": new_message.message_text,
                "created_at": new_message.created_at,
            }
        except IntegrityError:
            raise OneUserIdNotFoundException(message.recipient_id)

    @classmethod
    async def find_users_by_username(cls, username: str, limit: int, offset: int):
        raw_users = await UsersDao.find_by_username(username, limit, offset)
        if not raw_users:
            raise UserSearchNotFoundException
        new_offset = offset + limit if raw_users else offset
        users = {
            "users": [
                {
                    "id": user.id,
                    "username": user.username
                }
                for user in raw_users
            ],
            "pagination": {
                "limit": limit,
                "current_offset": offset,
                "new_offset": new_offset,
                "is_end": True if len(raw_users) < limit else False
            }
        }
        return users

    @classmethod
    async def get_all_chats(cls, limit: int, offset: int):
        raw_chats = await MessageDAO.get_all_users_chats(limit, offset)
        new_offset = offset + limit if raw_chats else offset
        chats = {
            "chats": [
                {
                    "chat": {
                        "participants": [
                            {
                                "user_id": chat[0],
                                "username": chat[1]
                            },
                            {
                                "user_id": chat[2],
                                "username": chat[3]
                            }
                        ],
                        "last_message_time": chat[4]
                    }
                }
                for chat in raw_chats
            ],
            "pagination": {
                "limit": limit,
                "current_offset": offset,
                "new_offset": new_offset,
                "is_end": True if len(raw_chats) < limit else False
            }
        }
        return chats