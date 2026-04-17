from contextvars import Token
from dataclasses import dataclass
from uuid import uuid4

from fastapi import WebSocket

from app.utils.logger import get_logger, reset_session_id, set_session_id

logger = get_logger(__name__)


@dataclass
class Connection:
    """Represents a single WebSocket connection."""

    websocket: WebSocket
    user_id: int
    username: str
    room_code: str
    session_id: str
    session_token: Token


class ConnectionManager:
    """
    Manages WebSocket connections across all rooms.

    This is a singleton - one instance handles all connections.
    """

    def __init__(self):
        # room_code -> list of connections in that room
        self.rooms: dict[str, list[Connection]] = {}

    async def connect(
        self, websocket: WebSocket, user_id: int, username: str, room_code: str
    ) -> Connection:
        """Accept a new WebSocket connection and add to room."""
        session_id = str(uuid4())
        session_token = set_session_id(session_id)
        try:
            await websocket.accept()
        except Exception:
            reset_session_id(session_token)
            raise

        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            username=username,
            room_code=room_code,
            session_id=session_id,
            session_token=session_token,
        )

        # Add to room (create room list if doesn't exist)
        if room_code not in self.rooms:
            self.rooms[room_code] = []
        self.rooms[room_code].append(connection)

        logger.info(
            "websocket_connected",
            status="connected",
            room_code=room_code,
            user_id=user_id,
            username=username,
        )

        return connection

    def disconnect(self, connection: Connection) -> None:
        """Remove a connection from its room."""
        room_code = connection.room_code

        if room_code in self.rooms:
            self.rooms[room_code] = [
                c for c in self.rooms[room_code] if c.user_id != connection.user_id
            ]
            # Clean up empty rooms
            if not self.rooms[room_code]:
                del self.rooms[room_code]

        logger.info(
            "websocket_disconnected",
            status="disconnected",
            room_code=room_code,
            user_id=connection.user_id,
            username=connection.username,
            session_id=connection.session_id,
        )

    async def broadcast_to_room(self, room_code: str, message: dict) -> None:
        """Send a message to all connections in a room."""
        if room_code not in self.rooms:
            return

        for connection in self.rooms[room_code]:
            try:
                await connection.websocket.send_json(message)
            except Exception:
                # Connection might be dead, ignore errors
                pass

    async def send_personal(self, connection: Connection, message: dict) -> None:
        """Send a message to a specific connection."""
        try:
            await connection.websocket.send_json(message)
        except Exception:
            pass

    def get_room_connections(self, room_code: str) -> list[Connection]:
        """Get all connections in a room."""
        return self.rooms.get(room_code, [])

    def get_room_user_ids(self, room_code: str) -> list[int]:
        """Get all user IDs currently connected to a room."""
        return [c.user_id for c in self.get_room_connections(room_code)]

    def is_user_in_room(self, room_code: str, user_id: int) -> bool:
        """Check if a user is currently connected to a room."""
        return user_id in self.get_room_user_ids(room_code)

    def get_connection_by_user_id(self, room_code: str, user_id: int) -> Connection | None:
        """Find a specific user's connection in a room."""
        for conn in self.get_room_connections(room_code):
            if conn.user_id == user_id:
                return conn
        return None



manager = ConnectionManager()
