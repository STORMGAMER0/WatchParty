from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message (used internally)."""

    content: str = Field(min_length=1, max_length=1000)


class MessageResponse(BaseModel):
    """Schema for message data in responses."""

    id: int
    room_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
