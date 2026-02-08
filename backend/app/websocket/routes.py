import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.browser.audio import audio_capture
from app.browser.manager import browser_manager
from app.core.security import decode_token
from app.models.message import Message
from app.services.auth_service import AuthService
from app.services.room_service import RoomService
from app.websocket.events import (
    BrowserAudioEvent,
    BrowserFrameEvent,
    ChatMessageEvent,
    ErrorEvent,
    EventType,
    RemoteChangedEvent,
    RemoteRequestEvent,
    UserJoinedEvent,
    UserLeftEvent,
)
from app.websocket.manager import manager

# Track screenshot streaming tasks per room
_screenshot_tasks: dict[str, asyncio.Task] = {}
# Track audio streaming tasks per room
_audio_tasks: dict[str, asyncio.Task] = {}
# Track which room is currently using audio (only one can use VB-Cable at a time)
_audio_room: str | None = None

router = APIRouter()


async def get_db_session():
    """Create a database session for WebSocket use."""
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        yield session


@router.websocket("/ws/{room_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_code: str,
    token: str,
):
    """
    WebSocket endpoint for real-time room communication.

    Connect with: ws://localhost:8000/ws/{room_code}?token={jwt_token}
    """
    # Get database session
    async with async_session_maker() as db:
        # Authenticate user from token
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Get user from database
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(int(user_id))

        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

        # Verify room exists and user is a participant
        room_service = RoomService(db)
        room = await room_service.get_room_by_code(room_code)

        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return

        if not room.is_active:
            await websocket.close(code=4004, reason="Room is closed")
            return

        participant = await room_service.get_participant(room.id, user.id)
        if not participant:
            await websocket.close(code=4003, reason="Not a participant")
            return

        # Accept connection and add to manager
        connection = await manager.connect(
            websocket=websocket,
            user_id=user.id,
            username=user.username,
            room_code=room_code,
        )

        # Notify others that user joined
        join_event = UserJoinedEvent(user_id=user.id, username=user.username)
        await manager.broadcast_to_room(room_code, join_event.model_dump(mode="json"))

        try:
            # Main message loop
            while True:
                data = await websocket.receive_json()
                await handle_message(db, connection, room, data)

        except WebSocketDisconnect:
            # User disconnected
            manager.disconnect(connection)

            # Notify others that user left
            leave_event = UserLeftEvent(user_id=user.id, username=user.username)
            await manager.broadcast_to_room(room_code, leave_event.model_dump(mode="json"))


async def handle_message(db: AsyncSession, connection, room, data: dict):
    """Handle incoming WebSocket messages."""
    event_type = data.get("event")

    # ─────────────────────────────────────────────────────────────
    # Chat Events
    # ─────────────────────────────────────────────────────────────
    if event_type == EventType.CHAT_MESSAGE:
        content = data.get("content", "").strip()

        if not content:
            error = ErrorEvent(message="Message cannot be empty")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        if len(content) > 1000:
            error = ErrorEvent(message="Message too long (max 1000 characters)")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Save message to database
        message = Message(
            room_id=room.id,
            user_id=connection.user_id,
            content=content,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Broadcast to room
        chat_event = ChatMessageEvent(
            user_id=connection.user_id,
            username=connection.username,
            content=content,
            message_id=message.id,
        )
        await manager.broadcast_to_room(
            connection.room_code, chat_event.model_dump(mode="json")
        )

    # ─────────────────────────────────────────────────────────────
    # Browser Events
    # ─────────────────────────────────────────────────────────────
    elif event_type == EventType.BROWSER_START or event_type == "browser_start":
        print(f"[DEBUG] Received browser_start from user {connection.user_id}")
        # Only host can start the browser
        if connection.user_id != room.host_id:
            error = ErrorEvent(message="Only the host can start the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Create browser session and start screenshot + audio streaming
        await browser_manager.create_session(connection.room_code)
        start_screenshot_stream(connection.room_code)
        start_audio_stream(connection.room_code)

        # Host starts with control
        browser_manager.set_controller(connection.room_code, connection.user_id, connection.username)

        # Broadcast who has control
        remote_event = RemoteChangedEvent(
            controller_id=connection.user_id,
            controller_username=connection.username,
        )
        await manager.broadcast_to_room(connection.room_code, remote_event.model_dump(mode="json"))

    elif event_type == EventType.BROWSER_STOP or event_type == "browser_stop":
        # Only host can stop the browser
        if connection.user_id != room.host_id:
            error = ErrorEvent(message="Only the host can stop the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Stop screenshot + audio streaming and close browser
        stop_screenshot_stream(connection.room_code)
        stop_audio_stream(connection.room_code)
        await browser_manager.close_session(connection.room_code)
        browser_manager.clear_controller(connection.room_code)

    elif event_type == EventType.BROWSER_NAVIGATE:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only controller can navigate
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control of the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        url = data.get("url", "").strip()
        if url:
            await session.navigate(url)

    elif event_type == EventType.BROWSER_CLICK:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only controller can click
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control of the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        x = data.get("x", 0)
        y = data.get("y", 0)

        # With Playwright screenshots, coordinates map directly to viewport
        # (image is 1280x720, viewport is 1280x720 - no scaling needed)
        await session.click(int(x), int(y))

    elif event_type == EventType.BROWSER_TYPE:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only controller can type
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control of the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        text = data.get("text", "")
        if text:
            await session.type_text(text)

    elif event_type == EventType.BROWSER_KEYPRESS:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only controller can press keys
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control of the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        key = data.get("key", "")
        if key:
            await session.press_key(key)

    elif event_type == EventType.BROWSER_SCROLL:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only controller can scroll
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control of the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        delta_x = data.get("deltaX", 0)
        delta_y = data.get("deltaY", 0)
        await session.scroll(int(delta_x), int(delta_y))

    # ─────────────────────────────────────────────────────────────
    # Remote Control Events
    # ─────────────────────────────────────────────────────────────
    elif event_type == EventType.REMOTE_REQUEST:
        # Any user can request control - broadcast to everyone
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Don't let the current controller request control (they already have it)
        if browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You already have control")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Broadcast the request to everyone in the room
        request_event = RemoteRequestEvent(
            user_id=connection.user_id,
            username=connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code, request_event.model_dump(mode="json")
        )

    elif event_type == EventType.REMOTE_PASS:
        # Current controller passes control to another user
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only the current controller can pass control
        if not browser_manager.is_controller(connection.room_code, connection.user_id):
            error = ErrorEvent(message="You don't have control to pass")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Get target user ID from the message
        target_user_id = data.get("target_user_id")

        if not target_user_id:
            error = ErrorEvent(message="No target user specified")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Look up the target user from active connections (don't trust client!)
        target_connection = manager.get_connection_by_user_id(
            connection.room_code, target_user_id
        )

        if not target_connection:
            error = ErrorEvent(message="User not found in room")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Transfer control (using verified username from server)
        browser_manager.set_controller(
            connection.room_code, target_user_id, target_connection.username
        )

        # Broadcast the change to everyone
        remote_event = RemoteChangedEvent(
            controller_id=target_user_id,
            controller_username=target_connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code, remote_event.model_dump(mode="json")
        )

    elif event_type == EventType.REMOTE_TAKE:
        # Host forcefully takes control
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Only the host can take control
        if connection.user_id != room.host_id:
            error = ErrorEvent(message="Only the host can take control")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Host takes control
        browser_manager.set_controller(
            connection.room_code, connection.user_id, connection.username
        )

        # Broadcast the change to everyone
        remote_event = RemoteChangedEvent(
            controller_id=connection.user_id,
            controller_username=connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code, remote_event.model_dump(mode="json")
        )

    else:
        error = ErrorEvent(message=f"Unknown event type: {event_type}")
        await manager.send_personal(connection, error.model_dump(mode="json"))


# ─────────────────────────────────────────────────────────────────────────────
# Screenshot Streaming (using Playwright's native CDP-based screenshot)
# ─────────────────────────────────────────────────────────────────────────────

def start_screenshot_stream(room_code: str) -> None:
    """Start sending screenshots to all clients in a room using Playwright."""
    # Don't start if already running
    if room_code in _screenshot_tasks:
        return

    # Start the broadcast loop - Playwright's screenshot works without extra setup
    task = asyncio.create_task(_screenshot_loop(room_code))
    _screenshot_tasks[room_code] = task
    print(f"[Screenshot] Started Playwright screenshot streaming for room {room_code}")


def stop_screenshot_stream(room_code: str) -> None:
    """Stop sending screenshots for a room."""
    # Stop the broadcast task
    task = _screenshot_tasks.pop(room_code, None)
    if task:
        task.cancel()
        print(f"[Screenshot] Stopped streaming for room {room_code}")


async def _screenshot_loop(room_code: str) -> None:
    """
    Continuously capture and broadcast screenshots using Playwright.

    Playwright's screenshot() uses Chrome DevTools Protocol (CDP) to capture
    the page content directly from Chrome's renderer - this works regardless
    of window position (off-screen, minimized, etc.) and avoids Windows API
    rendering artifacts.

    Target ~20 FPS for smooth video while balancing CPU/network load.
    """
    print(f"[Screenshot] Broadcast loop started for room {room_code}")
    frame_count = 0
    target_fps = 20
    frame_interval = 1.0 / target_fps

    try:
        while True:
            loop_start = asyncio.get_event_loop().time()

            # Check if browser session is still running
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Screenshot] Session not running for room {room_code}")
                break

            try:
                # Use Playwright's native screenshot (CDP-based, very reliable)
                frame = await session.screenshot()
                url = await session.get_current_url()

                frame_count += 1

                # Broadcast to all clients in room
                frame_event = BrowserFrameEvent(frame=frame, url=url)
                await manager.broadcast_to_room(
                    room_code, frame_event.model_dump(mode="json")
                )

                if frame_count % 100 == 0:
                    print(f"[Screenshot] Broadcast {frame_count} frames for room {room_code}")

            except Exception as e:
                print(f"[Screenshot] Error: {e}")

            # Maintain target FPS
            elapsed = asyncio.get_event_loop().time() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                # If we're behind, yield briefly to prevent blocking
                await asyncio.sleep(0.001)

    except asyncio.CancelledError:
        pass  # Task was cancelled, exit gracefully


# ─────────────────────────────────────────────────────────────────────────────
# Audio Streaming
# ─────────────────────────────────────────────────────────────────────────────

def start_audio_stream(room_code: str) -> None:
    """Start sending audio to all clients in a room."""
    global _audio_room

    # Only one room can use VB-Cable audio at a time
    if _audio_room is not None:
        print(f"[Audio] Cannot start for {room_code} - audio already in use by {_audio_room}")
        return

    # Don't start if already running for this room
    if room_code in _audio_tasks:
        return

    _audio_room = room_code
    audio_capture.start()

    task = asyncio.create_task(_audio_loop(room_code))
    _audio_tasks[room_code] = task
    print(f"[Audio] Started streaming for room {room_code}")


def stop_audio_stream(room_code: str) -> None:
    """Stop sending audio for a room."""
    global _audio_room

    task = _audio_tasks.pop(room_code, None)
    if task:
        task.cancel()

    if _audio_room == room_code:
        audio_capture.stop()
        _audio_room = None
        print(f"[Audio] Stopped streaming for room {room_code}")


async def _audio_loop(room_code: str) -> None:
    """
    Continuously capture and broadcast audio chunks.
    """
    print(f"[Audio] Loop started for room {room_code}")
    chunk_count = 0

    try:
        async for chunk in audio_capture.stream_chunks(chunk_size=4096):
            # Check if session is still active
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Audio] Session ended for room {room_code}")
                break

            chunk_count += 1
            if chunk_count % 100 == 0:
                print(f"[Audio] Sent {chunk_count} chunks for room {room_code}")

            # Broadcast audio to all clients in room
            audio_event = BrowserAudioEvent(audio=chunk)
            await manager.broadcast_to_room(
                room_code, audio_event.model_dump(mode="json")
            )

    except asyncio.CancelledError:
        pass  # Task was cancelled, exit gracefully


# Import for the route file
from app.db.session import async_session_maker
