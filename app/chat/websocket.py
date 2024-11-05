from datetime import datetime
from typing import Dict

from fastapi import WebSocket
from fastapi.exceptions import WebSocketException
from pydantic import UUID4

from app.chat.shemas import SWebsocketMessage
from app.core.exceptions import ErrorHandler
from app.core.logger import logger


class ConnectionManager(ErrorHandler):
    """
    ConnectionManager - Класс, предназначенный для управления активными WebSocket-соединениями и отправки сообщений пользователям.

    Атрибуты:
        active_connections (Dict[UUID4, WebSocket]): Словарь для хранения активных соединений, где ключом является UUID пользователя, а значением - объект WebSocket.

    Методы:
        connect(websocket: WebSocket, user_id: UUID4): Подключает пользователя по WebSocket и добавляет соединение в активные.
        disconnect(user_id: UUID4): Отключает пользователя и удаляет соединение из активных.
        send_personal_message(message: dict, recipient_id: UUID4): Отправляет личное сообщение пользователю через WebSocket.
        notify_user_about_new_message(message: SWebsocketMessage, sender_id: UUID4): Уведомляет пользователя о новом сообщении.
        notify_chat_list_update(current_user_id: UUID4, partner_id: UUID4, last_message_time: datetime): Уведомляет двух пользователей об обновлении списка чатов.
    """

    _type_error_message = "Websocket Error"
    _type_error = WebSocketException

    def __init__(self):
        """
        Инициализация объекта ConnectionManager с пустым списком активных соединений.
        """
        # Словарь для хранения активных соединений с пользователями, где ключ - UUID пользователя, значение - WebSocket-соединение.
        self.active_connections: Dict[UUID4, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID4):
        """
        Подключает пользователя по WebSocket и добавляет соединение в активные.

        Параметры:
            websocket (WebSocket): Объект WebSocket для подключения.
            user_id (UUID4): Уникальный идентификатор пользователя.
        """
        try:
            # Добавляем соединение в список активных соединений.
            self.active_connections[user_id] = websocket
        except (WebSocketException, Exception) as e:
            # Логируем ошибку, если не удалось принять соединение.
            self._log_error(e, error_message="Cannot accept websocket connection")

    async def disconnect(self, user_id: UUID4):
        """
        Отключает пользователя и удаляет соединение из активных.

        Параметры:
            user_id (UUID4): Уникальный идентификатор пользователя.
        """
        try:
            # Удаляем соединение пользователя из списка активных.
            websocket = self.active_connections.pop(user_id, None)
            if websocket:
                # Закрываем соединение, если оно найдено.
                await websocket.close()
        except (WebSocketException, Exception) as e:
            # Логируем ошибку, если не удалось закрыть соединение.
            self._log_error(e, error_message="Cannot close websocket connection")

    async def send_personal_message(self, message: dict, recipient_id: UUID4):
        """
        Отправляет личное сообщение пользователю через WebSocket.

        Параметры:
            message (dict): Словарь с данными сообщения.
            recipient_id (UUID4): Уникальный идентификатор получателя сообщения.
        """
        # Получаем соединение пользователя по идентификатору.
        websocket = self.active_connections.get(recipient_id)
        if websocket:
            try:
                # Отправляем сообщение в формате JSON.
                await websocket.send_json(message)
            except (WebSocketException, Exception) as e:
                # При ошибке отправки сообщения разрываем соединение и логируем ошибку.
                await self.disconnect(recipient_id)
                self._log_error(
                    e,
                    error_message=f"Cannot sending a message to the user {recipient_id}: {e}",
                )
        else:
            # Логируем информацию, если соединение не найдено.
            logger.info(f"Connection to user {recipient_id} not found")

    async def notify_user_about_new_message(
        self, message: SWebsocketMessage, sender_id: UUID4
    ):
        """
        Уведомляет пользователя о новом сообщении.

        Параметры:
            message (SWebsocketMessage): Объект сообщения для уведомления.
            sender_id (UUID4): Уникальный идентификатор отправителя сообщения.
        """
        # Формируем данные сообщения для отправки.
        message_data = {
            "type": "new_message",
            "data": {
                "sender_id": str(sender_id),
                "recipient_id": str(message.recipient_id),
                "message_text": message.message_text,
                "created_at": str(message.created_at)
            }
        }
        # Отправляем сообщение получателю.
        await self.send_personal_message(message_data, message.recipient_id)

    async def notify_chat_list_update(
        self, current_user_id: UUID4, partner_id: UUID4, last_message_time: datetime
    ):
        """
        Уведомляет пользователей об обновлении списка чатов.

        Параметры:
            current_user_id (UUID4): Уникальный идентификатор текущего пользователя.
            partner_id (UUID4): Уникальный идентификатор партнера по чату.
            last_message_time (datetime): Время последнего сообщения.
        """
        # Формируем данные события об обновлении чата.
        message_data = {
            "type": "chat_list_update",
            "data": {
                "partner_id": str(partner_id),
                "last_message_time": str(last_message_time)
            }
        }
        # Отправляем уведомление текущему пользователю.
        await self.send_personal_message(message_data, current_user_id)
        # Отправляем уведомление партнеру.
        await self.send_personal_message(message_data, partner_id)


# Создаем экземпляр менеджера соединений.
manager = ConnectionManager()
