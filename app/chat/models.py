from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_text: Mapped[str] = mapped_column(String(4096))
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Связь с отправителем
    sender: Mapped["User"] = relationship(
        "User", back_populates="sender_messages", foreign_keys=[sender_id]
    )

    # Связь с получателем
    recipient: Mapped["User"] = relationship(
        "User", back_populates="recipient_messages", foreign_keys=[recipient_id]
    )

    def __repr__(self):
        return f"Message(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id})"
