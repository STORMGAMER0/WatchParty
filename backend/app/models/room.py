import secrets
import string

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


def generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_code: Mapped[str] = mapped_column(
        String(10), unique=True, index=True, default=generate_room_code
    )
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Foreign key to the host (User who created the room)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="hosted_rooms")
    participants: Mapped[list["RoomParticipant"]] = relationship(
        "RoomParticipant", back_populates="room", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="room", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Room(id={self.id}, code={self.room_code}, host_id={self.host_id})>"
