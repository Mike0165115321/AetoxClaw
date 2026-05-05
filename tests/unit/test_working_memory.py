import pytest
import os
import json
from pathlib import Path
from aetox.memory.working import WorkingMemory

class TestWorkingMemory:
    @pytest.fixture
    def memory(self, mock_memory_config, tmp_path):
        # Update config to use tmp_path
        cfg = mock_memory_config.copy()
        cfg["episodic_path"] = str(tmp_path / "episodes.jsonl")
        cfg["vector_db_path"] = str(tmp_path / "vector_db")
        return WorkingMemory(cfg)

    async def test_update_context(self, memory):
        task_id = "test_task"
        await memory.update_context(task_id, {"user": "tester"})
        
        # Verify in task_context dict
        assert task_id in memory.task_context
        assert memory.task_context[task_id]["state"]["user"] == "tester"

    async def test_add_step_result(self, memory):
        step_id = 1
        output = "Done"
        await memory.add_step_result(step_id, output, status="success")
        
        assert len(memory.active_chunks) == 1
        assert memory.active_chunks[0].source == f"step_{step_id}"
        assert memory.active_chunks[0].content == output

    async def test_persistence(self, memory, tmp_path):
        # WorkingMemory.save_to_disk creates 'working_snapshot.json' in the same dir as episodic_path
        await memory.update_context("persistent_task", {"key": "val"})
        await memory.add_step_result(1, "ok")
        
        snapshot_path = tmp_path / "working_snapshot.json"
        assert snapshot_path.exists()
        
        with open(snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["active_chunks"][0]["source"] == "step_1"

    def test_auto_summarize(self, memory):
        # Test the internal _auto_summarize helper
        long_text = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5."
        summarized = memory._auto_summarize(long_text, 20)
        assert len(summarized) < len(long_text)
        assert "Sentence 1" in summarized
        assert "Sentence 5" in summarized
