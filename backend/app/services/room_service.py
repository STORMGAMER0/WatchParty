from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.room import Room
from app.models.room_participant import RoomParticipant
from app.models.user import User


class RoomService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_room(self, host: User, title: str | None = None) -> Room:
        """Create a new room with the given user as host."""
        room = Room(host_id=host.id, title=title)

        self.db.add(room)
        await self.db.flush()

        # Automatically add host as first participant
        participant = RoomParticipant(room_id=room.id, user_id=host.id)
        self.db.add(participant)

        await self.db.flush()
        await self.db.refresh(room)

        return room

    async def get_room_by_id(self, room_id: int) -> Room | None:
        """Get a room by its ID."""
        query = select(Room).where(Room.id == room_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_room_by_code(self, room_code: str) -> Room | None:
        """Get a room by its shareable code (case-insensitive)."""
        query = select(Room).where(func.upper(Room.room_code) == room_code.upper())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_room_with_participants(self, room_code: str) -> Room | None:
        """Get a room with its participants eagerly loaded (case-insensitive)."""
        query = (
            select(Room)
            .where(func.upper(Room.room_code) == room_code.upper())
            .options(
                selectinload(Room.participants).selectinload(RoomParticipant.user),
                selectinload(Room.host),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def join_room(self, room: Room, user: User) -> RoomParticipant:
        """
        Add a user to a room.

        Raises:
            ValueError: If room is full, inactive, or user already joined
        """
        if not room.is_active:
            raise ValueError("Room is no longer active")

        # Check if already a participant
        existing = await self.get_participant(room.id, user.id)
        if existing:
            raise ValueError("Already in this room")

        # Check participant count
        count = await self.get_participant_count(room.id)
        if count >= settings.max_room_participants:
            raise ValueError("Room is full")

        participant = RoomParticipant(room_id=room.id, user_id=user.id)
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)

        return participant

    async def leave_room(self, room: Room, user: User) -> None:
        """Remove a user from a room."""
        participant = await self.get_participant(room.id, user.id)

        if not participant:
            raise ValueError("Not in this room")

        await self.db.delete(participant)

        # If host leaves, close the room
        if room.host_id == user.id:
            room.is_active = False

    async def close_room(self, room: Room, user: User) -> None:
        """Close a room (host only)."""
        if room.host_id != user.id:
            raise ValueError("Only the host can close the room")

        room.is_active = False

    async def get_participant(
        self, room_id: int, user_id: int
    ) -> RoomParticipant | None:
        """Get a specific participant record."""
        query = select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_participant_count(self, room_id: int) -> int:
        """Get the number of participants in a room."""
        query = select(func.count()).where(RoomParticipant.room_id == room_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_user_active_rooms(self, user: User) -> list[Room]:
        """Get all active rooms where user is a participant."""
        query = (
            select(Room)
            .join(RoomParticipant)
            .where(
                RoomParticipant.user_id == user.id,
                Room.is_active == True,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
