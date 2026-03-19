from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.session import async_session_maker
from app.services.auth_service import AuthService
from app.services.room_service import RoomService
from app.websocket.events import UserJoinedEvent, UserLeftEvent
from app.websocket.handlers.events import dispatch_message
from app.websocket.manager import manager

router = APIRouter()


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
    async with async_session_maker() as db:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return

        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(int(user_id))
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return

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

        connection = await manager.connect(
            websocket=websocket,
            user_id=user.id,
            username=user.username,
            room_code=room_code,
        )

        join_event = UserJoinedEvent(user_id=user.id, username=user.username)
        await manager.broadcast_to_room(room_code, join_event.model_dump(mode="json"))

        try:
            while True:
                data = await websocket.receive_json()
                await dispatch_message(db, connection, room, data)
        except WebSocketDisconnect:
            manager.disconnect(connection)

            leave_event = UserLeftEvent(user_id=user.id, username=user.username)
            await manager.broadcast_to_room(
                room_code,
                leave_event.model_dump(mode="json"),
            )
