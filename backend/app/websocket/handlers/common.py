from app.websocket.events import ErrorEvent
from app.websocket.manager import Connection, manager


async def send_error(connection: Connection, message: str) -> None:
    """Send a consistent websocket error payload to one user."""
    await manager.send_personal(
        connection,
        ErrorEvent(message=message).model_dump(mode="json"),
    )
