from datetime import datetime

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Schema for creating a new room."""

    title: str | None = Field(None, max_length=100)


class RoomResponse(BaseModel):
    """Schema for room data in responses."""

    id: int
    room_code: str
    title: str | None
    host_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomDetailResponse(RoomResponse):
    """Schema for detailed room info including host and participant count."""

    host_username: str
    participant_count: int


class ParticipantResponse(BaseModel):
    """Schema for participant data."""

    id: int
    user_id: int
    username: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class RoomWithParticipantsResponse(RoomResponse):
    """Schema for room with full participant list."""

    host_username: str
    participants: list[ParticipantResponse]
