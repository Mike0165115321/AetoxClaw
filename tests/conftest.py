import pytest
import os
import json
import shutil
from unittest.mock import MagicMock, AsyncMock
from aetox.core.ollama_client import OllamaClient

@pytest.fixture
def mock_ollama_client():
    """Fixture to provide a mocked OllamaClient."""
    client = MagicMock(spec=OllamaClient)
    client.check_health = AsyncMock(return_value=True)
    client.chat = AsyncMock()
    client.chat_stream = AsyncMock()
    return client

@pytest.fixture
def mock_plan_response():
    """Returns a valid plan JSON structure."""
    return {
        "plan_id": "test_plan_001",
        "goal": "Test Goal",
        "steps": [
            {"step_id": 1, "description": "Step 1", "tool": "test_tool", "action": "test_action"},
            {"step_id": 2, "description": "Step 2", "tool": "test_tool", "action": "test_action"}
        ]
    }

@pytest.fixture
def mock_extraction_response():
    """Returns a valid intent extraction JSON."""
    return {
        "tool": "master_file_manager",
        "action": "list_dir",
        "params": {"path": "."},
        "confidence": 0.95,
        "analysis": "Listing current directory"
    }

@pytest.fixture
def temp_workspace(tmp_path):
    """Creates a temporary workspace directory structure."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "docs").mkdir()
    (workspace / "data").mkdir()
    (workspace / "logs").mkdir()
    
    # Create a dummy config for testing
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    return workspace

@pytest.fixture
def mock_memory_config():
    """Returns a memory configuration that disables heavy RAG components."""
    return {
        "max_context_tokens": 2000,
        "chunk_size": 256,
        "summary_ratio": 0.1,
        "episodic_path": "data/test_episodes.jsonl",
        "vector_db_path": "data/test_vector_db",
        "history_truncate_chars": 100,
        "embedder": {
            "model": "none", # Disable BGE-M3
            "device": "cpu"
        }
    }

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure environment variables are set correctly for tests."""
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setenv("DISCORD_TOKEN", "fake_token")
