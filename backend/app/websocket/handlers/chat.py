from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.websocket.events import ChatMessageEvent
from app.websocket.manager import Connection, manager

from .common import send_error


async def handle_chat_message(
    db: AsyncSession,
    connection: Connection,
    room,
    data: dict,
) -> None:
    """Validate, persist, and broadcast a chat message."""
    content = data.get("content", "").strip()

    if not content:
        await send_error(connection, "Message cannot be empty")
        return

    if len(content) > 1000:
        await send_error(connection, "Message too long (max 1000 characters)")
        return

    message = Message(
        room_id=room.id,
        user_id=connection.user_id,
        content=content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    chat_event = ChatMessageEvent(
        user_id=connection.user_id,
        username=connection.username,
        content=content,
        message_id=message.id,
    )
    await manager.broadcast_to_room(
        connection.room_code,
        chat_event.model_dump(mode="json"),
    )
