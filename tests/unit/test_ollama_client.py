import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from aetox.core.ollama_client import OllamaClient

@pytest.fixture
def client():
    return OllamaClient()

@pytest.mark.asyncio
async def test_chat_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Hello"}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await client.chat("llama3", [{"role": "user", "content": "hi"}])
        
        assert result["message"]["content"] == "Hello"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "llama3"

@pytest.mark.asyncio
async def test_generate_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Generated text"}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await client.generate("llama3", "Tell me a story")
        
        assert result["response"] == "Generated text"
        assert mock_post.called

@pytest.mark.asyncio
async def test_check_health_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        assert await client.check_health() is True

@pytest.mark.asyncio
async def test_check_health_failure(client):
    with patch("httpx.AsyncClient.get", side_effect=Exception("Timeout")):
        assert await client.check_health() is False

@pytest.mark.asyncio
async def test_chat_stream(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Mock aiter_lines
    async def mock_aiter_lines():
        yield json.dumps({"message": {"content": "He"}})
        yield json.dumps({"message": {"content": "llo"}})
        yield json.dumps({"done": True})

    mock_response.aiter_lines = mock_aiter_lines
    mock_response.raise_for_status = MagicMock()

    # Mock context manager
    mock_context = MagicMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient.stream", return_value=mock_context):
        tokens = []
        async for token in client.chat_stream("llama3", [{"role": "user", "content": "hi"}]):
            tokens.append(token)
            
        assert tokens == ["He", "llo"]
