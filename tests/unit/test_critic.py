import pytest
from unittest.mock import AsyncMock, MagicMock
from aetox.agents.critic import CriticAgent

class TestCriticAgent:
    @pytest.fixture
    def critic(self, mock_ollama_client):
        # We need to ensure CriticAgent uses our mock_ollama_client
        agent = CriticAgent()
        agent.client = mock_ollama_client
        return agent

    async def test_evaluate_pass(self, critic, mock_ollama_client):
        # Mock LLM response for success
        mock_response = {
            "message": {
                "content": '{"verdict": "pass", "score": 1.0, "suggestion": "Looks good"}'
            }
        }
        mock_ollama_client.chat.return_value = mock_response
        
        step = {"description": "Create a file"}
        result = {"status": "success", "output": "File created successfully"}
        context = {}
        
        evaluation = await critic.evaluate(step, result, context)
        assert evaluation["verdict"] == "pass"
        assert evaluation["score"] == 1.0

    async def test_evaluate_fail(self, critic, mock_ollama_client):
        # Mock LLM response for failure
        mock_response = {
            "message": {
                "content": '{"verdict": "retry", "score": 0.3, "suggestion": "Try again with different name"}'
            }
        }
        mock_ollama_client.chat.return_value = mock_response
        
        step = {"description": "Create a file"}
        result = {"status": "failure", "error": "Disk full"}
        context = {}
        
        evaluation = await critic.evaluate(step, result, context)
        assert evaluation["verdict"] == "retry"
        assert evaluation["score"] < 0.5

    async def test_analyze_failure(self, critic, mock_ollama_client):
        mock_response = {
            "message": {
                "content": "You should check permissions first."
            }
        }
        mock_ollama_client.chat.return_value = mock_response
        
        feedback = await critic.analyze_failure({"desc": "test"}, {"error": "denied"})
        assert "permissions" in feedback
