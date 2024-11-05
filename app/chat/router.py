from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import UUID4, ValidationError

from app.auth.dependencies import get_current_user, get_current_user_websocket
from app.auth.models import User
from app.chat.services import ChatService
from app.chat.shemas import (
    IncomingWebSocketMessage,
    SChats,
    SGetMessagesBetweenUsersResponse,
    SSearchByUsernameResponse,
    SWebsocketMessage,
)
from app.chat.websocket import manager
from app.core.config import settings
from app.core.exceptions import (
    OneUserIdNotFoundException,
    UserMessagesBetweenYourselfException,
)
from app.core.logger import logger

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.get("/messages/", response_model=SChats)
async def get_chats(
    cursor_last_message_time: datetime = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """
    Получение списка чатов текущего пользователя.

    - **cursor_last_message_time**: (datetime, optional) Время последнего сообщения для пагинации.
    - **current_user**: (User, обязательный) Проверяет пользователя на аутентификацию.

    Возвращает список чатов с последними сообщениями.
    """
    return await ChatService.get_all_chats_for_user(
        current_user.id, cursor_last_message_time
    )


@router.get("/messages/{partner_id}/", response_model=SGetMessagesBetweenUsersResponse)
async def get_messages_between_users(
    partner_id: UUID4,
    cursor_time: datetime = Query(default=None),
    cursor_message_id: int = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """
    Получение списка сообщений между текущим пользователем и другим пользователем.

    - **partner_id**: (UUID4, обязательный) UUID другого пользователя.
    - **cursor_time**: (datetime, optional) Метка времени для пагинации сообщений.
    - **cursor_message_id**: (int, optional) ID сообщения для пагинации.
    - **current_user**: (User, обязательный) Проверяет пользователя на аутентификацию.

    Возвращает сообщения между пользователями и информацию о пагинации.
    """
    return await ChatService.get_messages_between_users(
        user_1_id=current_user.id,
        user_2_id=partner_id,
        cursor_time=cursor_time,
        cursor_message_id=cursor_message_id,
    )


@router.get("/users/", response_model=SSearchByUsernameResponse)
async def search_by_username(
    username: str = Query(min_length=1),
    limit: int = Query(settings.BASE_LIMIT_USERS_SEARCH, gt=0),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """
    Поиск пользователей по имени.

    - **username**: (str, обязательный) Имя пользователя для поиска, минимальная длина 1 символ.
    - **limit**: (int, optional) Лимит количества возвращаемых результатов.
    - **offset**: (int, optional) Смещение для пагинации.
    - **current_user**: (User, обязательный) Проверяет пользователя на аутентификацию.

    Возвращает список найденных пользователей и информацию о пагинации.
    """
    return await ChatService.find_users_by_username(
        username=username, limit=limit, offset=offset
    )


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    """
    Веб-сокет для связи в реальном времени.

    - **websocket**: объект WebSocket для подключения.
    """
    await websocket.accept()
    current_user = await get_current_user_websocket(websocket)

    try:

        # Подключение пользователя к менеджеру WebSocket
        await manager.connect(websocket=websocket, user_id=current_user.id)

        while True:
            data = await websocket.receive_json()

            try:
                incoming_message = IncomingWebSocketMessage(**data)
            except ValidationError as e:
                logger.error(f"WebSocket validation error: {e.errors()}")
                await websocket.send_json({"detail": e.errors()})
                continue
            except Exception as e:
                logger.error(f"Unexpected validation WebSocket error: {str(e)}")
                await websocket.send_json({"detail": "Incorrect data."})
                continue

            try:
                message_data = SWebsocketMessage(**incoming_message.dict())
                await ChatService.add_message(message_data, current_user.id)
            except UserMessagesBetweenYourselfException as e:
                await websocket.send_json({"detail": e.detail})
                continue
            except OneUserIdNotFoundException as e:
                await websocket.send_json({"detail": e.detail})
                continue

            # Добавление сообщения в базу данных через сервис
            await ChatService.add_message(message_data, current_user.id)

            # Уведомление получателя о новом сообщении
            await manager.notify_user_about_new_message(
                message_data, sender_id=current_user.id
            )

            # Уведомление об обновлении списка чатов
            await manager.notify_chat_list_update(
                current_user_id=current_user.id,
                partner_id=message_data.recipient_id,
                last_message_time=message_data.created_at,
            )

    except WebSocketDisconnect:
        await manager.disconnect(current_user.id)
