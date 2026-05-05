import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from aetox.core.dispatcher import Dispatcher

@pytest.fixture
def mock_memory():
    memory = MagicMock()
    memory.get_active_context = AsyncMock(return_value={})
    memory.get_full_context_async = AsyncMock(return_value={})
    memory.add_step_result = AsyncMock()
    memory.update_context = AsyncMock()
    return memory

@pytest.fixture
def dispatcher(mock_memory):
    with patch("aetox.core.dispatcher.ExecutorAgent"), patch("aetox.core.dispatcher.CriticAgent"):
        return Dispatcher(mock_memory)

@pytest.mark.asyncio
async def test_run_direct_step_success(dispatcher, mock_memory):
    # Setup mocks
    dispatcher.executor.extract_action = AsyncMock(return_value={
        "tool": "test_tool",
        "action": "test_action",
        "confidence": 0.9
    })
    dispatcher.executor.run_action = AsyncMock(return_value={
        "status": "success",
        "output": "Test Output"
    })
    
    result = await dispatcher.run_direct_step("Test Goal")
    
    assert result["status"] == "success"
    assert result["output"] == "Test Output"
    mock_memory.add_step_result.assert_called_once()
    assert mock_memory.add_step_result.call_args[1]["output"] == "Test Output"

@pytest.mark.asyncio
async def test_run_direct_step_low_confidence(dispatcher, mock_memory):
    dispatcher.executor.extract_action = AsyncMock(return_value={
        "tool": "other",
        "confidence": 0.3
    })
    
    result = await dispatcher.run_direct_step("Complex Goal")
    
    assert result["status"] == "failure"
    assert result["needs_planning"] is True

@pytest.mark.asyncio
async def test_run_plan_success(dispatcher, mock_memory, mock_plan_response):
    # Setup mocks for plan execution
    dispatcher.executor.extract_action = AsyncMock(return_value={"tool": "t", "action": "a"})
    dispatcher.executor.run_action = AsyncMock(return_value={"status": "success", "output": "ok"})
    dispatcher.critic.evaluate = AsyncMock(return_value={"verdict": "pass"})
    
    result = await dispatcher.run_plan(mock_plan_response)
    
    assert result["status"] == "success"
    assert dispatcher.executor.run_action.call_count == 2
    assert mock_memory.add_step_result.call_count == 2

@pytest.mark.asyncio
async def test_run_plan_with_retry(dispatcher, mock_memory):
    plan = {
        "plan_id": "retry_plan",
        "steps": [{"step_id": 1, "description": "Retry Step"}]
    }
    
    dispatcher.executor.extract_action = AsyncMock(return_value={"tool": "t"})
    dispatcher.executor.run_action = AsyncMock(return_value={"status": "success", "output": "bad"})
    
    # First call fails critic, second passes
    dispatcher.critic.evaluate = AsyncMock()
    dispatcher.critic.evaluate.side_effect = [
        {"verdict": "fail", "suggestion": "Fix it"},
        {"verdict": "pass"}
    ]
    dispatcher.critic.analyze_failure = AsyncMock(return_value="Feedback")
    
    result = await dispatcher.run_plan(plan)
    
    assert result["status"] == "success"
    assert dispatcher.executor.run_action.call_count == 2
    assert dispatcher.critic.evaluate.call_count == 2

@pytest.mark.asyncio
async def test_callback_handling(dispatcher):
    mock_cb = MagicMock()
    dispatcher.progress_callback = mock_cb
    
    await dispatcher._safe_callback("Hello")
    mock_cb.assert_called_once_with("Hello")

@pytest.mark.asyncio
async def test_async_callback_handling(dispatcher):
    mock_cb = AsyncMock()
    dispatcher.progress_callback = mock_cb
    
    await dispatcher._safe_callback("Hello")
    mock_cb.assert_called_once_with("Hello")
