from datetime import datetime
from typing import Dict
from fastapi import WebSocket

from pydantic import UUID4


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID4, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID4):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: UUID4):
        websocket = self.active_connections.pop(user_id, None)
        if websocket:
            await websocket.close()

    async def send_personal_message(self, message: dict, recipient_id: UUID4):
        websocket = self.active_connections.get(recipient_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Ошибка отправки сообщения пользователю {recipient_id}: {e}")
                #await self.disconnect(recipient_id)  # отключение при ошибке
        else:
            print(f"Соединение с пользователем {recipient_id} не найдено")


async def notify_users_about_new_message(new_message):
    message_data = {
        "sender_id": str(new_message.sender_id),
        "recipient_id": str(new_message.recipient_id),
        "message_text": new_message.message_text,
        "created_at": str(new_message.created_at)
    }
    await manager.send_personal_message(message_data, new_message.sender_id)
    await manager.send_personal_message(message_data, new_message.recipient_id)


async def notify_chat_list_update(user_id: UUID4, partner_id: UUID4, last_message_time: datetime):
    message_data = {
        "event": "new_message",
        "partner_id": str(partner_id),
        "last_message_time": str(last_message_time)
    }
    await manager.send_personal_message(message_data, user_id)
    await manager.send_personal_message(message_data, partner_id)

manager = ConnectionManager()