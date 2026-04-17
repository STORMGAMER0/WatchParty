from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.browser.manager import browser_manager
from app.utils.logger import get_logger
from app.websocket.events import EventType, RemoteChangedEvent, RemoteRequestEvent
from app.websocket.manager import Connection, manager
from app.websocket.streaming import (
    start_audio_stream,
    start_screenshot_stream,
    stop_audio_stream,
    stop_screenshot_stream,
)

from .common import send_error

logger = get_logger(__name__)


async def handle_browser_event(
    db: AsyncSession,
    connection: Connection,
    room: Room,
    data: dict,
) -> None:
    """Handle browser session lifecycle and browser input events."""
    event_type = data.get("event")
    current_room = await _get_current_room(db, room.id)
    if current_room is None:
        await send_error(connection, "Room not found")
        return

    if event_type == EventType.BROWSER_START:
        await _handle_browser_start(connection, current_room)
    elif event_type == EventType.BROWSER_STOP:
        await _handle_browser_stop(connection, current_room)
    elif event_type == EventType.BROWSER_NAVIGATE:
        session = await _require_active_session(connection)
        if not session or not await _require_controller(connection):
            return

        url = data.get("url", "").strip()
        if url:
            await session.navigate(url)
    elif event_type == EventType.BROWSER_CLICK:
        session = await _require_active_session(connection)
        if not session or not await _require_controller(connection):
            return

        await session.click(int(data.get("x", 0)), int(data.get("y", 0)))
    elif event_type == EventType.BROWSER_TYPE:
        session = await _require_active_session(connection)
        if not session or not await _require_controller(connection):
            return

        text = data.get("text", "")
        if text:
            await session.type_text(text)
    elif event_type == EventType.BROWSER_KEYPRESS:
        session = await _require_active_session(connection)
        if not session or not await _require_controller(connection):
            return

        key = data.get("key", "")
        if key:
            await session.press_key(key)
    elif event_type == EventType.BROWSER_SCROLL:
        session = await _require_active_session(connection)
        if not session or not await _require_controller(connection):
            return

        await session.scroll(
            int(data.get("deltaX", 0)),
            int(data.get("deltaY", 0)),
        )


async def handle_remote_event(
    db: AsyncSession,
    connection: Connection,
    room: Room,
    data: dict,
) -> None:
    """Handle remote control request/pass/take events."""
    event_type = data.get("event")
    current_room = await _get_current_room(db, room.id)
    if current_room is None:
        await send_error(connection, "Room not found")
        return

    session = await _require_active_session(connection)
    if not session:
        return

    if event_type == EventType.REMOTE_REQUEST:
        if browser_manager.is_controller(connection.room_code, connection.user_id):
            await send_error(connection, "You already have control")
            return

        request_event = RemoteRequestEvent(
            user_id=connection.user_id,
            username=connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code,
            request_event.model_dump(mode="json"),
        )
    elif event_type == EventType.REMOTE_PASS:
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            await send_error(connection, "You don't have control to pass")
            return

        target_user_id = data.get("target_user_id")
        if not target_user_id:
            await send_error(connection, "No target user specified")
            return

        target_connection = manager.get_connection_by_user_id(
            connection.room_code,
            target_user_id,
        )
        if not target_connection:
            await send_error(connection, "User not found in room")
            return

        browser_manager.set_controller(
            connection.room_code,
            target_user_id,
            target_connection.username,
        )
        await _broadcast_controller_change(
            connection.room_code,
            target_user_id,
            target_connection.username,
        )
    elif event_type == EventType.REMOTE_TAKE:
        if connection.user_id != current_room.host_id:
            await send_error(connection, "Only the host can take control")
            return

        browser_manager.set_controller(
            connection.room_code,
            connection.user_id,
            connection.username,
        )
        await _broadcast_controller_change(
            connection.room_code,
            connection.user_id,
            connection.username,
        )


async def _handle_browser_start(connection: Connection, room) -> None:
    if connection.user_id != room.host_id:
        await send_error(connection, "Only the host can start the browser")
        return

    logger.info(
        "browser_start_requested",
        status="requested",
        room_code=connection.room_code,
        user_id=connection.user_id,
    )
    await browser_manager.create_session(connection.room_code)
    start_screenshot_stream(connection.room_code)
    start_audio_stream(connection.room_code)

    browser_manager.set_controller(
        connection.room_code,
        connection.user_id,
        connection.username,
    )
    await _broadcast_controller_change(
        connection.room_code,
        connection.user_id,
        connection.username,
    )


async def _handle_browser_stop(connection: Connection, room) -> None:
    if connection.user_id != room.host_id:
        await send_error(connection, "Only the host can stop the browser")
        return

    stop_screenshot_stream(connection.room_code)
    stop_audio_stream(connection.room_code)
    await browser_manager.close_session(connection.room_code)
    browser_manager.clear_controller(connection.room_code)


async def _require_active_session(connection: Connection):
    session = browser_manager.get_session(connection.room_code)
    if not session:
        await send_error(connection, "Browser not started")
        return None
    return session


async def _require_controller(connection: Connection) -> bool:
    if browser_manager.is_controller(connection.room_code, connection.user_id):
        return True

    await send_error(connection, "You don't have control of the browser")
    return False


async def _get_current_room(db: AsyncSession, room_id: int) -> Room | None:
    return await db.get(Room, room_id)


async def _broadcast_controller_change(
    room_code: str,
    controller_id: int,
    controller_username: str,
) -> None:
    remote_event = RemoteChangedEvent(
        controller_id=controller_id,
        controller_username=controller_username,
    )
    await manager.broadcast_to_room(room_code, remote_event.model_dump(mode="json"))
