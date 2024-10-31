from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.params import Depends
from fastapi import status
from pydantic import UUID4

from app.auth.dependencies import get_moderator_user
from app.auth.models import User
from app.auth.shemas import SBlock
from app.auth.services import BlockService
from app.chat.services import ChatService
from app.chat.shemas import SGetMessagesBetweenUsersResponse
from app.core.config import settings
from app.moderation.shemas import SModerChatsResponse, SModerBlockResponse

router = APIRouter(
    prefix='/moderation',
    tags=["Moderation"],
)

@router.get("/chats", response_model=SModerChatsResponse)
async def get_all_chats(
        limit: int = Query(settings.BASE_LIMIT_MESSAGES_FOR_MODERATOR, gt=0),
        offset: int = Query(0, ge=0),
        moderator: User = Depends(get_moderator_user)
):
    return await ChatService.get_all_chats(limit, offset)

@router.get("/chats/messages", response_model=SGetMessagesBetweenUsersResponse)
async def get_messages_between_users(
        participant_1_id: UUID4 = Query(),
        participant_2_id: UUID4 = Query(),
        cursor_time: datetime = Query(default=None),
        cursor_message_id: int = Query(default=None),
        moderator: User = Depends(get_moderator_user)
):
    return await ChatService.get_messages_between_users(user_1_id=participant_1_id, user_2_id=participant_2_id,
                                                        cursor_time=cursor_time, cursor_message_id=cursor_message_id, moder_flag=True)

@router.post('/block', status_code=status.HTTP_201_CREATED, response_model=SModerBlockResponse)
async def block_user(block: SBlock, moderator: User = Depends(get_moderator_user)):
    return await BlockService.block_user(user_id=block.user_id, moderator_id=moderator.id, reason=block.reason_of_block)
