import pytest
from aetox.tools.loader import create_default_registry, ToolRegistry
from aetox.tools.base import BaseTool

class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        return create_default_registry()

    def test_default_tools_loaded(self, registry):
        names = registry.list_names()
        # Verify based on actual tools in the directory
        assert "master_file_manager" in names
        assert "web_pulse_scraper" in names
        assert "system_control" in names
        assert "aetox_vision" in names

    def test_get_tool(self, registry):
        tool = registry.get("master_file_manager")
        assert isinstance(tool, BaseTool)
        assert tool.name == "master_file_manager"

    def test_get_non_existent_tool(self, registry):
        assert registry.get("ghost_tool") is None

    def test_execute_non_existent_tool(self, registry):
        result = registry.execute("ghost_tool", {})
        assert result["status"] == "failure"
        # Check for Thai keyword for "not found"
        assert "ไม่พบ" in result["error"]

    def test_build_prompt_doc(self, registry):
        doc = registry.build_prompt_doc()
        assert isinstance(doc, str)
        assert "master_file_manager" in doc
        assert "web_pulse_scraper" in doc
