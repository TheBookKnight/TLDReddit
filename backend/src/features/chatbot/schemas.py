"""Chatbot schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Schema for sending a chat message."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's question or prompt for the Reddit trend assistant.",
        examples=["What are people in r/stocks saying about semiconductor demand this week?"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Summarize the latest community sentiment for r/technology."
            }
        }
    }


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    title: str | None = Field(
        default=None,
        description="Optional title shown in the saved conversation list.",
        examples=["NVIDIA earnings follow-up"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "AI investing themes"
            }
        }
    }


class ChatMessageResponse(BaseModel):
    """Single chat message response."""

    id: int = Field(description="Internal identifier for the stored message.", examples=[42])
    session_id: int = Field(description="Chat session that owns this message.", examples=[7])
    role: str = Field(
        description="Who produced the message.",
        examples=["assistant"],
    )
    content: str = Field(
        description="Message text returned to the client.",
        examples=["Community sentiment is mildly bullish, driven by recent product launches."],
    )
    created_at: datetime = Field(
        description="When the message was created in UTC.",
        examples=["2026-05-31T14:22:00Z"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 42,
                "session_id": 7,
                "role": "assistant",
                "content": "Community sentiment is mildly bullish, driven by recent product launches.",
                "created_at": "2026-05-31T14:22:00Z",
            }
        },
    }


class ChatSessionResponse(BaseModel):
    """Chat session response."""

    id: int = Field(description="Internal identifier for the chat session.", examples=[7])
    title: str | None = Field(
        description="Display title for the conversation.",
        examples=["AI investing themes"],
    )
    created_at: datetime = Field(
        description="When the session was created in UTC.",
        examples=["2026-05-31T14:20:00Z"],
    )
    messages: list[ChatMessageResponse] = Field(
        default_factory=list,
        description="Messages already stored for the session, oldest to newest.",
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 7,
                "title": "AI investing themes",
                "created_at": "2026-05-31T14:20:00Z",
                "messages": [
                    {
                        "id": 42,
                        "session_id": 7,
                        "role": "assistant",
                        "content": "Community sentiment is mildly bullish, driven by recent product launches.",
                        "created_at": "2026-05-31T14:22:00Z",
                    }
                ],
            }
        },
    }
