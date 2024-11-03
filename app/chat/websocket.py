from datetime import datetime
from typing import Dict
from fastapi import WebSocket
from fastapi.exceptions import WebSocketException

from pydantic import UUID4

from app.chat.shemas import SWebsocketMessage, SWebsocketPersonalMessage, SWebsocketEventMessage
from app.core.exceptions import ErrorHandler
from app.core.logger import logger


class ConnectionManager(ErrorHandler):
    _type_error_message = "Websocket Error"
    _type_error = WebSocketException

    def __init__(self):
        self.active_connections: Dict[UUID4, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID4):
        try:
            await websocket.accept()
            self.active_connections[user_id] = websocket
        except (WebSocketException, Exception) as e:
            self._log_error(
                e,
                error_message="Cannot accept websocket connection"
            )

    async def disconnect(self, user_id: UUID4):
        try:
            websocket = self.active_connections.pop(user_id, None)
            if websocket:
                await websocket.close()
        except (WebSocketException, Exception) as e:
            self._log_error(
                e,
                error_message="Cannot close websocket connection"
            )

    async def send_personal_message(self, message: dict, recipient_id: UUID4):
        websocket = self.active_connections.get(recipient_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except (WebSocketException, Exception) as e:
                await self.disconnect(recipient_id)
                self._log_error(
                    e,
                    error_message=f"Cannot sending a message to the user {recipient_id}: {e}"
                )
        else:
            logger.info(f"Connection to user {recipient_id} not found")

    async def notify_user_about_new_message(self, message: SWebsocketMessage, sender_id: UUID4):
        message_data = {
            "sender_id": str(sender_id),
            "recipient_id": str(message.recipient_id),
            "message_text": message.message_text,
            "created_at": str(message.created_at)
        }
        await self.send_personal_message(message_data, message.recipient_id)

    async def notify_chat_list_update(self, current_user_id: UUID4, partner_id: UUID4, last_message_time: datetime):
        event_data = {
            "event": "new_message",
            "partner_id": str(partner_id),
            "last_message_time": str(last_message_time)
        }
        await self.send_personal_message(event_data, current_user_id)
        await self.send_personal_message(event_data, partner_id)

manager = ConnectionManager()