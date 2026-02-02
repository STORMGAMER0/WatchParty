from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message


class ChatService:
    """Handles chat-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_room_messages(
        self, room_id: int, limit: int = 50, before_id: int | None = None
    ) -> list[Message]:
        """
        Get messages for a room, ordered by newest first.

        Args:
            room_id: The room to fetch messages from
            limit: Maximum number of messages to return
            before_id: Only get messages with ID less than this (for pagination)
        """
        query = (
            select(Message)
            .where(Message.room_id == room_id)
            .options(selectinload(Message.user))
            .order_by(Message.id.desc())
            .limit(limit)
        )

        if before_id:
            query = query.where(Message.id < before_id)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))

    async def create_message(self, room_id: int, user_id: int, content: str) -> Message:
        """Create and save a new message."""
        message = Message(room_id=room_id, user_id=user_id, content=content)
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message
