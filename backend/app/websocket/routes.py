from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.message import Message
from app.services.auth_service import AuthService
from app.services.room_service import RoomService
from app.websocket.events import (
    ChatMessageEvent,
    ErrorEvent,
    EventType,
    RoomClosedEvent,
    UserJoinedEvent,
    UserLeftEvent,
)
from app.websocket.manager import manager

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

    else:
        error = ErrorEvent(message=f"Unknown event type: {event_type}")
        await manager.send_personal(connection, error.model_dump(mode="json"))


# Import for the route file
from app.db.session import async_session_maker
