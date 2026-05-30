"""Chatbot schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Schema for sending a chat message."""

    content: str = Field(..., min_length=1, max_length=4000)


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    title: str | None = None


class ChatMessageResponse(BaseModel):
    """Single chat message response."""

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    """Chat session response."""

    id: int
    title: str | None
    created_at: datetime
    messages: list[ChatMessageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
