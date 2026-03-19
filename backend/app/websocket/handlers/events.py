from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.events import EventType
from app.websocket.manager import Connection

from .chat import handle_chat_message
from .common import send_error
from .control import handle_browser_event, handle_remote_event
from .signaling import handle_voice_event


BROWSER_EVENTS = {
    EventType.BROWSER_START,
    EventType.BROWSER_STOP,
    EventType.BROWSER_NAVIGATE,
    EventType.BROWSER_CLICK,
    EventType.BROWSER_TYPE,
    EventType.BROWSER_KEYPRESS,
    EventType.BROWSER_SCROLL,
}

REMOTE_EVENTS = {
    EventType.REMOTE_REQUEST,
    EventType.REMOTE_PASS,
    EventType.REMOTE_TAKE,
}

VOICE_EVENTS = {
    EventType.VOICE_JOIN,
    EventType.VOICE_LEAVE,
    EventType.VOICE_OFFER,
    EventType.VOICE_ANSWER,
    EventType.VOICE_ICE_CANDIDATE,
}


async def dispatch_message(
    db: AsyncSession,
    connection: Connection,
    room,
    data: dict,
) -> None:
    """Route an incoming websocket event to its domain-specific handler."""
    event_type = data.get("event")

    if event_type == EventType.CHAT_MESSAGE:
        await handle_chat_message(db, connection, room, data)
        return

    if event_type in BROWSER_EVENTS:
        await handle_browser_event(connection, room, data)
        return

    if event_type in REMOTE_EVENTS:
        await handle_remote_event(connection, room, data)
        return

    if event_type in VOICE_EVENTS:
        await handle_voice_event(connection, data)
        return

    await send_error(connection, f"Unknown event type: {event_type}")
