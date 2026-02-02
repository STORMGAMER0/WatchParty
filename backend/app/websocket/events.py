from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EventType(str, Enum):
    """Types of WebSocket events."""

    # Connection events
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"

    # Chat events
    CHAT_MESSAGE = "chat_message"

    # System events
    ERROR = "error"
    ROOM_CLOSED = "room_closed"


class BaseEvent(BaseModel):
    """Base class for all WebSocket events."""

    event: EventType
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class UserJoinedEvent(BaseEvent):
    """Sent when a user joins the room."""

    event: EventType = EventType.USER_JOINED
    user_id: int
    username: str


class UserLeftEvent(BaseEvent):
    """Sent when a user leaves the room."""

    event: EventType = EventType.USER_LEFT
    user_id: int
    username: str


class ChatMessageEvent(BaseEvent):
    """Sent when a user sends a chat message."""

    event: EventType = EventType.CHAT_MESSAGE
    user_id: int
    username: str
    content: str
    message_id: int | None = None


class ErrorEvent(BaseEvent):
    """Sent when an error occurs."""

    event: EventType = EventType.ERROR
    message: str


class RoomClosedEvent(BaseEvent):
    """Sent when the room is closed by the host."""

    event: EventType = EventType.ROOM_CLOSED
    reason: str = "Host closed the room"
