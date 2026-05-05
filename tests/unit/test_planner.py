import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from aetox.planner.agent import AetoxPlanner

@pytest.mark.asyncio
async def test_create_plan_success(mock_ollama_client, mock_plan_response):
    # Setup mock client to return the plan response
    mock_ollama_client.chat.return_value = {
        "message": {
            "content": json.dumps(mock_plan_response)
        }
    }
    
    planner = AetoxPlanner(client=mock_ollama_client)
    plan = await planner.create_plan("Test Goal")
    
    assert plan["plan_id"] == "test_plan_001"
    assert len(plan["steps"]) == 2
    assert plan["goal"] == "Test Goal"
    
    # Verify client call
    mock_ollama_client.chat.assert_called_once()
    args, kwargs = mock_ollama_client.chat.call_args
    assert kwargs["format"] == "json"

@pytest.mark.asyncio
async def test_create_plan_failure(mock_ollama_client):
    # Setup mock client to raise exception
    mock_ollama_client.chat.side_effect = Exception("Model Timeout")
    
    planner = AetoxPlanner(client=mock_ollama_client)
    plan = await planner.create_plan("Test Goal")
    
    assert plan["plan_id"] == "error"
    assert "Model Timeout" in plan["error"]
    assert plan["steps"] == []

@pytest.mark.asyncio
async def test_planner_tool_awareness(mock_ollama_client):
    # Verify that build_prompt_doc is called on the registry
    mock_registry = MagicMock()
    mock_registry.build_prompt_doc.return_value = "Mocked Tools Info"
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aetox.planner.agent.create_default_registry", lambda: mock_registry)
        
        # Setup mock client
        mock_ollama_client.chat.return_value = {"message": {"content": "{}"}}
        
        planner = AetoxPlanner(client=mock_ollama_client)
        await planner.create_plan("Test Goal")
        
        mock_registry.build_prompt_doc.assert_called_once()
