from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.session import async_session_maker
from app.services.auth_service import AuthService
from app.services.room_service import RoomService
from app.utils.logger import get_logger, reset_session_id
from app.websocket.events import UserJoinedEvent, UserLeftEvent
from app.websocket.handlers.events import dispatch_message
from app.websocket.manager import manager

router = APIRouter()
logger = get_logger(__name__)


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
    connection = None

    async with async_session_maker() as db:
        payload = decode_token(token)
        if not payload:
            logger.warning(
                "websocket_rejected",
                status="invalid_token",
                room_code=room_code,
            )
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            logger.warning(
                "websocket_rejected",
                status="invalid_token",
                room_code=room_code,
            )
            await websocket.close(code=4001, reason="Invalid token")
            return

        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(int(user_id))
        if not user:
            logger.warning(
                "websocket_rejected",
                status="user_not_found",
                room_code=room_code,
                user_id=user_id,
            )
            await websocket.close(code=4001, reason="User not found")
            return

        room_service = RoomService(db)
        room = await room_service.get_room_by_code(room_code)
        if not room:
            logger.warning(
                "websocket_rejected",
                status="room_not_found",
                room_code=room_code,
                user_id=user.id,
            )
            await websocket.close(code=4004, reason="Room not found")
            return

        if not room.is_active:
            logger.warning(
                "websocket_rejected",
                status="room_closed",
                room_code=room_code,
                user_id=user.id,
            )
            await websocket.close(code=4004, reason="Room is closed")
            return

        participant = await room_service.get_participant(room.id, user.id)
        if not participant:
            logger.warning(
                "websocket_rejected",
                status="not_participant",
                room_code=room_code,
                user_id=user.id,
            )
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
        except Exception as exc:
            logger.exception(
                "websocket_error",
                status="error",
                room_code=room_code,
                user_id=user.id,
                error=str(exc),
            )
            raise
        finally:
            if connection is not None:
                reset_session_id(connection.session_token)
