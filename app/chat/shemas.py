from datetime import datetime
from typing import List, Optional

from pydantic import UUID4, BaseModel, Field


class SLimitOffsetPagination(BaseModel):
    """
    Модель для представления информации о пагинации.
    """

    limit: int = Field(
        ..., description="Максимальное количество записей за раз", example=10
    )
    current_offset: int = Field(..., description="Текущее смещение данных", example=0)
    new_offset: int = Field(
        ..., description="Новое смещение данных после загрузки", example=10
    )
    is_end: bool = Field(..., description="Флаг окончания данных", example=False)


class IncomingWebSocketMessage(BaseModel):
    """
    Модель для представления сообщения, отправляемого через WebSocket.
    """

    message_text: str = Field(
        ..., description="Текст сообщения", example="Hello, how are you?"
    )
    recipient_id: UUID4 = Field(
        ...,
        description="UUID получателя",
        example="d9b9f719-5e5e-4b49-8f00-d8f9f19e5e50",
    )


class SWebsocketMessage(IncomingWebSocketMessage):
    """
    Модель для представления сообщения, отправляемого через WebSocket.
    """

    created_at: datetime = Field(
        ...,
        default_factory=datetime.utcnow,
        description="Время создания сообщения",
        example="2024-11-03T14:25:43.511Z",
    )


class SMessageCreateResponse(BaseModel):
    """
    Модель для ответа при успешном создании сообщения.
    """

    status: str = Field(
        ..., description="Статус операции (например, 'success')", example="success"
    )
    sender_id: UUID4 = Field(
        ...,
        description="UUID отправителя",
        example="a123b456-c789-0123-d456-789e0f123456",
    )
    recipient_id: UUID4 = Field(
        ...,
        description="UUID получателя",
        example="d9b9f719-5e5e-4b49-8f00-d8f9f19e5e50",
    )
    message_text: str = Field(
        ..., description="Текст сообщения", example="Message sent successfully."
    )
    created_at: datetime = Field(
        ..., description="Время создания сообщения", example="2024-11-03T17:05:45.000Z"
    )


class SChat(BaseModel):
    """
    Модель для представления чата с пользователем.
    """

    partner_id: UUID4 = Field(
        ...,
        description="UUID партнера по чату",
        example="f456e789-0123-4567-89ab-0123456789ab",
    )
    partner_username: str = Field(
        ..., description="Имя пользователя партнера", example="chat_partner"
    )
    last_message_time: datetime = Field(
        ...,
        description="Время последнего сообщения в чате",
        example="2024-11-03T18:00:00.000Z",
    )


class SChats(BaseModel):
    """
    Модель для представления списка чатов пользователя.
    """

    chats: List[SChat] = Field(..., description="Список чатов")
    cursor_last_message_time: Optional[datetime] = Field(
        None,
        description="Время последнего сообщения для пагинации",
        example="2024-11-03T18:00:00.000Z",
    )


class SSearchByUsernameUsers(BaseModel):
    """
    Модель для представления пользователя при поиске по имени.
    """

    id: UUID4 = Field(
        ...,
        description="UUID пользователя",
        example="f456e789-0123-4567-89ab-0123456789ab",
    )
    username: str = Field(..., description="Имя пользователя", example="searched_user")


class SSearchByUsernameResponse(BaseModel):
    """
    Модель для ответа при поиске пользователей по имени.
    """

    users: List[SSearchByUsernameUsers] = Field(
        ..., description="Список найденных пользователей"
    )
    pagination: SLimitOffsetPagination = Field(..., description="Данные пагинации")


class SGetMessage(BaseModel):
    """
    Модель для представления полученного сообщения.
    """

    sender_id: UUID4 = Field(
        ...,
        description="UUID отправителя сообщения",
        example="a123b456-c789-0123-d456-789e0f123456",
    )
    username: str = Field(
        ..., description="Имя пользователя отправителя", example="sender_user"
    )
    message_text: str = Field(
        ..., description="Текст сообщения", example="This is a message."
    )
    created_at: datetime = Field(
        ..., description="Время создания сообщения", example="2024-11-03T19:30:45.123Z"
    )


class SParticipiant(BaseModel):
    """
    Модель для представления участника переписки.
    """

    participant_id: UUID4 = Field(
        ...,
        description="UUID участника",
        example="f456e789-0123-4567-89ab-0123456789ab",
    )
    is_current_user: bool = Field(
        ...,
        description="Флаг, указывающий, является ли участник текущим пользователем",
        example=True,
    )


class SGetMessagesBetweenUsersResponse(BaseModel):
    """
    Модель для ответа при получении сообщений между пользователями.
    """

    participants: List[SParticipiant] = Field(
        ..., description="Список участников переписки"
    )
    messages: List[SGetMessage] = Field(..., description="Список сообщений")
    cursor_time: Optional[datetime] = Field(
        None,
        description="Метка времени для пагинации",
        example="2024-11-03T20:00:00.000Z",
    )
    cursor_message_id: Optional[int] = Field(
        None, description="ID сообщения для пагинации", example=123
    )
