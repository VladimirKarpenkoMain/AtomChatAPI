from datetime import datetime
from typing import List
from pydantic import BaseModel, UUID4, Field

from app.chat.shemas import SLimitOffsetPagination


class SModerUserInfoChat(BaseModel):
    user_id: UUID4
    username: str

class SModerBaseInfoChat(BaseModel):
    participants: List[SModerUserInfoChat]
    last_message_time: datetime

class SModerChat(BaseModel):
    chat: SModerBaseInfoChat

class SModerChatsResponse(BaseModel):
    chats: List[SModerChat]
    pagination: SLimitOffsetPagination

class SModerBlockResponse(BaseModel):
    detail: str = Field("The user has been blocked")
    blocked_user_id: UUID4 = Field(examples=["0949c72e-ae06-4740-9496-b8fe180016f3"])