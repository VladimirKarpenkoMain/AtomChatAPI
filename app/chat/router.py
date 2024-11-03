import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocketDisconnect, WebSocket, Depends, Query
from pydantic import UUID4
from fastapi import status

from app.chat.services import ChatService
from app.auth.models import User
from app.auth.dependencies import get_current_user, get_current_user_websocket
from app.chat.shemas import SChats, SSearchByUsernameResponse, \
    SGetMessagesBetweenUsersResponse, SWebsocketMessage

from app.chat.websocket import manager
from app.core.config import settings

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.get("/messages", response_model=SChats)
async def get_chats(
        cursor_last_message_time: datetime = Query(default=None),
        current_user: User = Depends(get_current_user)
):
    return await ChatService.get_all_chats_for_user(current_user.id, cursor_last_message_time)


@router.get("/messages/{partner_id}", response_model=SGetMessagesBetweenUsersResponse)
async def get_messages_between_users(
        partner_id: UUID4,
        cursor_time: datetime = Query(default=None),
        cursor_message_id: int = Query(default=None),
        current_user: User = Depends(get_current_user)
):
    return await ChatService.get_messages_between_users(user_1_id=current_user.id, user_2_id=partner_id,
                                                        cursor_time=cursor_time, cursor_message_id=cursor_message_id)


@router.get("/users", response_model=SSearchByUsernameResponse)
async def search_by_username(
        username: str = Query(min_length=1),
        limit: int = Query(settings.BASE_LIMIT_USERS_SEARCH, gt=0),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user)
):
    return await ChatService.find_users_by_username(username=username, limit=limit, offset=offset)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    current_user = await get_current_user_websocket(websocket)
    await manager.connect(websocket=websocket, user_id=current_user.id)
    try:
        while True:
            data = await websocket.receive_json()
            message = SWebsocketMessage(
                message_text=data.get('message_text'),
                recipient_id=data.get('recipient_id'),
                created_at=datetime.utcnow()
            )
            await ChatService.add_message(message, current_user.id)
            await manager.notify_user_about_new_message(message, sender_id=current_user.id)
            await manager.notify_chat_list_update(current_user_id=current_user.id, partner_id=message.recipient_id, last_message_time=message.created_at)

    except WebSocketDisconnect:
        manager.disconnect(current_user.id)
