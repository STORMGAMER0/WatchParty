from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.message import MessageResponse
from app.schemas.room import (
    ParticipantResponse,
    RoomCreate,
    RoomResponse,
    RoomWithParticipantsResponse,
)
from app.services.chat_service import ChatService
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new room. The current user becomes the host."""
    room_service = RoomService(db)
    room = await room_service.create_room(current_user, room_data.title)
    return room


@router.get("", response_model=list[RoomResponse])
async def get_my_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active rooms where the current user is a participant."""
    room_service = RoomService(db)
    rooms = await room_service.get_user_active_rooms(current_user)
    return rooms


@router.get("/{room_code}", response_model=RoomWithParticipantsResponse)
async def get_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get room details including participants."""
    room_service = RoomService(db)
    room = await room_service.get_room_with_participants(room_code)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    # Build response with participant details
    participants = [
        ParticipantResponse(
            id=p.id,
            user_id=p.user_id,
            username=p.user.username,
            joined_at=p.joined_at,
        )
        for p in room.participants
    ]

    return RoomWithParticipantsResponse(
        id=room.id,
        room_code=room.room_code,
        title=room.title,
        host_id=room.host_id,
        is_active=room.is_active,
        created_at=room.created_at,
        host_username=room.host.username,
        participants=participants,
    )


@router.post("/{room_code}/join", response_model=RoomWithParticipantsResponse)
async def join_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join an existing room."""
    room_service = RoomService(db)
    room = await room_service.get_room_with_participants(room_code)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    try:
        await room_service.join_room(room, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Refresh to get updated participants
    room = await room_service.get_room_with_participants(room_code)

    participants = [
        ParticipantResponse(
            id=p.id,
            user_id=p.user_id,
            username=p.user.username,
            joined_at=p.joined_at,
        )
        for p in room.participants
    ]

    return RoomWithParticipantsResponse(
        id=room.id,
        room_code=room.room_code,
        title=room.title,
        host_id=room.host_id,
        is_active=room.is_active,
        created_at=room.created_at,
        host_username=room.host.username,
        participants=participants,
    )


@router.post("/{room_code}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a room. If the host leaves, the room closes."""
    room_service = RoomService(db)
    room = await room_service.get_room_by_code(room_code)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    try:
        await room_service.leave_room(room, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{room_code}", status_code=status.HTTP_204_NO_CONTENT)
async def close_room(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a room (host only)."""
    room_service = RoomService(db)
    room = await room_service.get_room_by_code(room_code)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    try:
        await room_service.close_room(room, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{room_code}/messages", response_model=list[MessageResponse])
async def get_room_messages(
    room_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = Query(None),
):
    """
    Get chat message history for a room.

    - limit: Number of messages to return (1-100, default 50)
    - before_id: Get messages older than this ID (for pagination)
    """
    room_service = RoomService(db)
    room = await room_service.get_room_by_code(room_code)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    # Verify user is a participant
    participant = await room_service.get_participant(room.id, current_user.id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant of this room",
        )

    chat_service = ChatService(db)
    messages = await chat_service.get_room_messages(room.id, limit, before_id)

    return [
        MessageResponse(
            id=msg.id,
            room_id=msg.room_id,
            user_id=msg.user_id,
            username=msg.user.username,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]
