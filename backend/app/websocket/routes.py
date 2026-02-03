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

    elif event_type == EventType.BROWSER_STOP:
        # Only host can stop the browser
        if connection.user_id != room.host_id:
            error = ErrorEvent(message="Only the host can stop the browser")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        # Stop screenshot streaming and close browser
        stop_screenshot_stream(connection.room_code)
        await browser_manager.close_session(connection.room_code)

    elif event_type == EventType.BROWSER_NAVIGATE:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            error = ErrorEvent(message="Browser not started")
            await manager.send_personal(connection, error.model_dump(mode="json"))
            return

        url = data.get("url", "").strip()
        if url:
            await session.navigate(url)

    elif event_type == EventType.BROWSER_CLICK:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            return

        x = data.get("x", 0)
        y = data.get("y", 0)
        await session.click(int(x), int(y))

    elif event_type == EventType.BROWSER_TYPE:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            return

        text = data.get("text", "")
        if text:
            await session.type_text(text)

    elif event_type == EventType.BROWSER_KEYPRESS:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            return

        key = data.get("key", "")
        if key:
            await session.press_key(key)

    elif event_type == EventType.BROWSER_SCROLL:
        session = browser_manager.get_session(connection.room_code)
        if not session:
            return

        delta_x = data.get("deltaX", 0)
        delta_y = data.get("deltaY", 0)
        await session.scroll(int(delta_x), int(delta_y))

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

    Runs every 100ms (10 FPS) to balance smoothness and bandwidth.
    """
    print(f"[Screenshot] Loop started for room {room_code}")
    frame_count = 0
    try:
        while True:
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Screenshot] Session not found or not running for room {room_code}")
                break

            try:
                # Capture screenshot
                frame = await session.screenshot()
                url = await session.get_current_url()
                frame_count += 1
                if frame_count % 50 == 1:  # Log every 50 frames
                    print(f"[Screenshot] Sent frame {frame_count} for room {room_code}")

                # Broadcast to all clients in room
                frame_event = BrowserFrameEvent(frame=frame, url=url)
                await manager.broadcast_to_room(
                    room_code, frame_event.model_dump(mode="json")
                )
            except Exception as e:
                print(f"[Screenshot] Error capturing frame: {e}")

            # Wait before next frame (100ms = 10 FPS)
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        pass  # Task was cancelled, exit gracefully


# Import for the route file
from app.db.session import async_session_maker
