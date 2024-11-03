from typing import List, Optional

from pydantic import BaseModel, UUID4
from datetime import datetime

class SLimitOffsetPagination(BaseModel):
    limit: int
    current_offset: int
    new_offset: int
    is_end: bool

class SWebsocketMessage(BaseModel):
    message_text: str
    recipient_id: UUID4
    created_at: datetime

class SWebsocketPersonalMessage(BaseModel):
    sender_id: UUID4
    recipient_id: UUID4
    message_text: str
    created_at: datetime

class SWebsocketEventMessage(BaseModel):
    event: str
    partner_id: UUID4
    last_message_time: datetime

class SMessageCreateResponse(BaseModel):
    status: str
    sender_id: UUID4
    recipient_id: UUID4
    message_text: str
    created_at: datetime

class SChat(BaseModel):
    partner_id: UUID4
    partner_username: str
    last_message_time: datetime

class SChats(BaseModel):
    chats: List[SChat]
    cursor_last_message_time: datetime | None

class SSearchByUsernameUsers(BaseModel):
    id: UUID4
    username: str

class SSearchByUsernameResponse(BaseModel):
    users: List[SSearchByUsernameUsers]
    pagination: SLimitOffsetPagination

class SGetMessage(BaseModel):
    sender_id: UUID4
    username: str
    message_text: str
    created_at: datetime

class SParticipiant(BaseModel):
    participant_id: UUID4
    is_current_user: bool

class SGetMessagesBetweenUsersResponse(BaseModel):
    participants: List[SParticipiant]
    messages: List[SGetMessage]
    cursor_time: Optional[datetime]
    cursor_message_id: Optional[int]