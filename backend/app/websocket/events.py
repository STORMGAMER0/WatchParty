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
    BROWSER_AUDIO = "browser_audio"  # Audio chunk
    BROWSER_URL_CHANGED = "browser_url_changed"

    # Remote control events
    REMOTE_REQUEST = "remote_request"  # User requests control
    REMOTE_PASS = "remote_pass"  # Pass control to someone
    REMOTE_TAKE = "remote_take"  # Host takes control back
    REMOTE_CHANGED = "remote_changed"  # Broadcast: controller changed

    # Voice chat events (WebRTC signaling)
    VOICE_JOIN = "voice_join"  # User wants to join voice chat
    VOICE_LEAVE = "voice_leave"  # User leaves voice chat
    VOICE_OFFER = "voice_offer"  # SDP offer (peer A -> peer B)
    VOICE_ANSWER = "voice_answer"  # SDP answer (peer B -> peer A)
    VOICE_ICE_CANDIDATE = "voice_ice_candidate"  # ICE candidate exchange

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


class BrowserAudioEvent(BaseEvent):
    """Sent periodically with audio data from the browser."""

    event: EventType = EventType.BROWSER_AUDIO
    audio: str  # Base64 encoded MP3 audio chunk


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


# ─────────────────────────────────────────────────────────────────────────────
# Voice Chat Events (WebRTC Signaling)
# ─────────────────────────────────────────────────────────────────────────────


class VoiceJoinEvent(BaseEvent):
    """Broadcast when a user joins voice chat.

    All other users in voice chat will receive this and should
    create a new RTCPeerConnection + send an offer to this user.
    """

    event: EventType = EventType.VOICE_JOIN
    user_id: int
    username: str


class VoiceLeaveEvent(BaseEvent):
    """Broadcast when a user leaves voice chat.

    All other users should close their RTCPeerConnection to this user.
    """

    event: EventType = EventType.VOICE_LEAVE
    user_id: int
    username: str


class VoiceOfferEvent(BaseEvent):
    """Sent from one peer to another with an SDP offer.

    Contains the WebRTC session description that describes
    what media the sender wants to transmit (audio codec, etc).
    """

    event: EventType = EventType.VOICE_OFFER
    from_user_id: int
    to_user_id: int
    sdp: str  # The Session Description Protocol offer


class VoiceAnswerEvent(BaseEvent):
    """Sent from one peer to another with an SDP answer.

    The receiver of an offer responds with this answer,
    confirming they accept the proposed media session.
    """

    event: EventType = EventType.VOICE_ANSWER
    from_user_id: int
    to_user_id: int
    sdp: str  # The Session Description Protocol answer


class VoiceIceCandidateEvent(BaseEvent):
    """Sent between peers to exchange ICE candidates.

    ICE candidates are potential network paths (IP:port combinations)
    that peers can use to connect directly to each other.
    """

    event: EventType = EventType.VOICE_ICE_CANDIDATE
    from_user_id: int
    to_user_id: int
    candidate: str  # The ICE candidate (JSON stringified)
