import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.browser.manager import browser_manager
from app.core.security import decode_token
from app.models.message import Message
from app.services.auth_service import AuthService
from app.services.room_service import RoomService
from app.websocket.events import (
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

        # Create browser session and start screenshot streaming
        await browser_manager.create_session(connection.room_code)
        start_screenshot_stream(connection.room_code)

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

        # Stop screenshot streaming and close browser
        stop_screenshot_stream(connection.room_code)
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
# Screenshot Streaming
# ─────────────────────────────────────────────────────────────────────────────

def start_screenshot_stream(room_code: str) -> None:
    """Start sending screenshots to all clients in a room."""
    # Don't start if already running
    if room_code in _screenshot_tasks:
        return

    task = asyncio.create_task(_screenshot_loop(room_code))
    _screenshot_tasks[room_code] = task
    print(f"[Screenshot] Started streaming for room {room_code}")


def stop_screenshot_stream(room_code: str) -> None:
    """Stop sending screenshots for a room."""
    task = _screenshot_tasks.pop(room_code, None)
    if task:
        task.cancel()
        print(f"[Screenshot] Stopped streaming for room {room_code}")


async def _screenshot_loop(room_code: str) -> None:
    """
    Continuously capture and broadcast screenshots.

    Runs every ~42ms (24 FPS) for smoother video playback.
    """
    import time
    print(f"[Screenshot] Loop started for room {room_code} at 24 FPS")
    frame_count = 0
    total_capture_time = 0
    try:
        while True:
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Screenshot] Session not found or not running for room {room_code}")
                break

            try:
                # Capture screenshot and measure time
                start_time = time.time()
                frame = await session.screenshot()
                url = await session.get_current_url()
                capture_time = (time.time() - start_time) * 1000  # ms

                frame_count += 1
                total_capture_time += capture_time

                if frame_count % 120 == 0:  # Log every 120 frames (~5 seconds at target FPS)
                    avg_capture = total_capture_time / 120
                    actual_fps = 1000 / (avg_capture + 42)  # capture time + sleep time
                    print(f"[Screenshot] Frame {frame_count} | Avg capture: {avg_capture:.1f}ms | Actual FPS: ~{actual_fps:.1f}")
                    total_capture_time = 0

                # Broadcast to all clients in room
                frame_event = BrowserFrameEvent(frame=frame, url=url)
                await manager.broadcast_to_room(
                    room_code, frame_event.model_dump(mode="json")
                )
            except Exception as e:
                print(f"[Screenshot] Error capturing frame: {e}")

            # Wait before next frame (~42ms = 24 FPS)
            await asyncio.sleep(0.042)

    except asyncio.CancelledError:
        pass  # Task was cancelled, exit gracefully


# Import for the route file
from app.db.session import async_session_maker
