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

    # Browser events (client -> server)
    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_CLICK = "browser_click"
    BROWSER_TYPE = "browser_type"
    BROWSER_KEYPRESS = "browser_keypress"
    BROWSER_SCROLL = "browser_scroll"
    BROWSER_START = "browser_start"
    BROWSER_STOP = "browser_stop"

    # Browser events (server -> client)
    BROWSER_FRAME = "browser_frame"  # Screenshot frame
    BROWSER_URL_CHANGED = "browser_url_changed"

    # Remote control events
    REMOTE_REQUEST = "remote_request"  # User requests control
    REMOTE_PASS = "remote_pass"  # Pass control to someone
    REMOTE_TAKE = "remote_take"  # Host takes control back
    REMOTE_CHANGED = "remote_changed"  # Broadcast: controller changed

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


# Browser events (server -> client)
class BrowserFrameEvent(BaseEvent):
    """Sent periodically with a screenshot of the browser."""

    event: EventType = EventType.BROWSER_FRAME
    frame: str  # Base64 encoded JPEG image
    url: str  # Current page URL


class BrowserUrlChangedEvent(BaseEvent):
    """Sent when the browser navigates to a new URL."""

    event: EventType = EventType.BROWSER_URL_CHANGED
    url: str


# Remote control events
class RemoteRequestEvent(BaseEvent):
    """Sent when a user requests control of the browser."""

    event: EventType = EventType.REMOTE_REQUEST
    user_id: int
    username: str


class RemoteChangedEvent(BaseEvent):
    """Broadcast when the controller changes."""

    event: EventType = EventType.REMOTE_CHANGED
    controller_id: int
    controller_username: str
