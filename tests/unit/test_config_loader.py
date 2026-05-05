import pytest
from aetox.core.config_loader import ConfigLoader

class TestConfigLoader:
    @pytest.fixture
    def loader(self):
        return ConfigLoader()

    def test_singleton(self, loader):
        loader2 = ConfigLoader()
        assert loader is loader2

    def test_get_model(self, loader):
        model = loader.get_model("main")
        assert isinstance(model, str)
        assert len(model) > 0

    def test_memory_config(self, loader):
        mem_cfg = loader.get_memory_config()
        assert isinstance(mem_cfg, dict)
        assert "max_context_tokens" in mem_cfg
        assert "chunk_size" in mem_cfg
        assert "history_truncate_chars" in mem_cfg

    def test_get_options(self, loader):
        options = loader.get_options("main")
        assert isinstance(options, dict)
        assert "temperature" in options
