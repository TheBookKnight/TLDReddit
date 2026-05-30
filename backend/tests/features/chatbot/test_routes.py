"""Tests for the chatbot API routes."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_create_chat_session(client):
    """Test creating a new chat session."""
    response = await client.post("/api/v1/chat/sessions", json={"title": "My Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Session"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_chat_sessions(client):
    """Test listing chat sessions."""
    await client.post("/api/v1/chat/sessions", json={"title": "Session 1"})
    await client.post("/api/v1/chat/sessions", json={"title": "Session 2"})

    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_chat_session_detail(client):
    """Test getting a specific chat session."""
    create_resp = await client.post("/api/v1/chat/sessions", json={"title": "Detail Test"})
    session_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/chat/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["title"] == "Detail Test"


@pytest.mark.asyncio
async def test_get_chat_session_not_found(client):
    """Test getting a non-existent chat session."""
    response = await client.get("/api/v1/chat/sessions/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message(client):
    """Test sending a message to a chat session."""
    create_resp = await client.post("/api/v1/chat/sessions", json={})
    session_id = create_resp.json()["id"]

    with patch(
        "src.features.chatbot.routes.get_llm_provider"
    ) as mock_provider_factory:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "Here is my analysis of your question."
        mock_provider_factory.return_value = mock_provider

        response = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "What is r/stocks discussing?"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "assistant"
    assert data["content"] == "Here is my analysis of your question."


@pytest.mark.asyncio
async def test_send_message_session_not_found(client):
    """Test sending a message to a non-existent session."""
    response = await client.post(
        "/api/v1/chat/sessions/99999/messages",
        json={"content": "Hello?"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_chat_session(client):
    """Test deleting a chat session."""
    create_resp = await client.post("/api/v1/chat/sessions", json={"title": "Delete Me"})
    session_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/chat/sessions/{session_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/chat/sessions/{session_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_updates_session_title(client):
    """Test that sending a message auto-titles a 'New Conversation' session."""
    create_resp = await client.post("/api/v1/chat/sessions", json={})
    session_id = create_resp.json()["id"]

    with patch("src.features.chatbot.routes.get_llm_provider") as mock_factory:
        mock_provider = AsyncMock()
        mock_provider.complete.return_value = "Great question!"
        mock_factory.return_value = mock_provider

        await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "Tell me about r/Python trends"},
        )

    get_resp = await client.get(f"/api/v1/chat/sessions/{session_id}")
    assert get_resp.json()["title"] != "New Conversation"
