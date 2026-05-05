import pytest
import os
import yaml
from aetox.core.prompt_engine import PromptEngine

class TestPromptEngine:
    @pytest.fixture
    def engine(self, tmp_path):
        # Create a dummy template file
        template_dir = tmp_path / "config" / "prompts"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "test.yaml"
        template_file.write_text("""
intent_extraction:
  system_template: "System: {tools} {history}"
  user_input_template: "User: {description}"
""")
        return PromptEngine(), template_file

    def test_get_external_template_success(self, engine):
        pe, template_path = engine
        template = pe.get_external_template(str(template_path), "intent_extraction")
        assert "system_template" in template
        assert "{tools}" in template["system_template"]

    def test_get_external_template_missing_file(self, engine):
        pe, _ = engine
        template = pe.get_external_template("non_existent.yaml", "intent_extraction")
        assert template == {}

    def test_build_chat_messages(self, engine):
        pe, _ = engine
        # Match the actual signature: build_chat_messages(role, user_input, context, json_schema)
        messages = pe.build_chat_messages(
            role="planner",
            user_input="Hello",
            context={"last_file": "test.txt"}
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        # Use "Strategic Planner" based on actual SYSTEM_PROMPTS
        assert "Strategic Planner" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert "Hello" in messages[1]["content"]
        assert "test.txt" in messages[1]["content"]
