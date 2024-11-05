import uuid
from typing import List

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chat.models import Message
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    refresh_token: Mapped[str | None] = mapped_column(String())
    is_moderator: Mapped[bool] = mapped_column(default=False)

    # Связь с отправленными сообщениями
    sender_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender", foreign_keys="[Message.sender_id]"
    )

    # Связь с полученными сообщениями
    recipient_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="recipient", foreign_keys="[Message.recipient_id]"
    )

    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"


class Blocked(Base):
    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    blocked_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(256))
    moderator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
