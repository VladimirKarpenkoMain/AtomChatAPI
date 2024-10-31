import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocketDisconnect, WebSocket, Depends, Query, Path
from pydantic import UUID4
from fastapi import status
from sqlalchemy.sql.functions import current_user

from app.chat.services import ChatService
from app.auth.models import User
from app.auth.dependencies import get_current_user, get_current_user_websocket
from app.chat.shemas import SMessageCreate, SChats, SMessageCreateResponse, SSearchByUsernameResponse, \
    SGetMessagesBetweenUsersResponse

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


@router.post("/messages", status_code=status.HTTP_201_CREATED, response_model=SMessageCreateResponse)
async def send_message(message: SMessageCreate, current_user: User = Depends(get_current_user)):
    return await ChatService.add_message(message, current_user_id=current_user.id)


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
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(current_user.id)
