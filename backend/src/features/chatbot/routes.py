"""Chatbot API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.base import get_session
from src.database.models import ChatMessage, ChatSession
from src.features.chatbot.retrieval import build_chat_prompt, retrieve_context
from src.features.chatbot.schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from src.features.post_analysis.openai_provider import get_llm_provider

router = APIRouter()

_CHAT_SYSTEM = (
    "You are a helpful Reddit trend analyst assistant. "
    "Answer questions concisely and accurately based on the provided Reddit data. "
    "If the data doesn't contain enough information to answer, say so clearly."
)


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    data: ChatSessionCreate,
    session: AsyncSession = Depends(get_session),
) -> ChatSession:
    """Create a new chat session."""
    chat_session = ChatSession(title=data.title or "New Conversation")
    session.add(chat_session)
    await session.flush()
    # Reload with messages eagerly loaded
    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.id == chat_session.id)
        .options(selectinload(ChatSession.messages))
    )
    return result.scalar_one()


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    session: AsyncSession = Depends(get_session),
    limit: int = 20,
) -> list[ChatSession]:
    """List all chat sessions."""
    result = await session.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session_detail(
    session_id: int,
    session: AsyncSession = Depends(get_session),
) -> ChatSession:
    """Get a specific chat session with all messages."""
    result = await session.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    chat_session = result.scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return chat_session


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse, status_code=201)
async def send_message(
    session_id: int,
    data: ChatMessageCreate,
    session: AsyncSession = Depends(get_session),
) -> ChatMessage:
    """Send a user message and get an AI response."""
    # Verify session exists
    session_result = await session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    chat_session = session_result.scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    # Store user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.content,
    )
    session.add(user_msg)
    await session.flush()

    # Retrieve relevant context
    context_items = await retrieve_context(data.content, session)
    prompt = build_chat_prompt(data.content, context_items)

    # Get LLM response
    llm = get_llm_provider()
    try:
        ai_response = await llm.complete(_CHAT_SYSTEM, prompt)
    except Exception as exc:
        ai_response = f"I'm sorry, I encountered an error: {exc}"

    # Store assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response,
        context_used=context_items,
    )
    session.add(assistant_msg)
    await session.flush()

    # Update session title if it's the first message
    if chat_session.title == "New Conversation":
        chat_session.title = data.content[:80] + ("..." if len(data.content) > 80 else "")
        await session.flush()

    return assistant_msg


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a chat session and all its messages."""
    result = await session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    chat_session = result.scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    # Delete messages first
    msgs = await session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    for msg in msgs.scalars().all():
        await session.delete(msg)

    await session.delete(chat_session)
    await session.flush()
