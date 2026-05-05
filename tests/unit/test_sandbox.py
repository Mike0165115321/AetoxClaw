import pytest
import os
from pathlib import Path
from aetox.safety.sandbox import Sandbox, SafetyViolation

class TestSandbox:
    @pytest.fixture
    def sandbox(self, tmp_path):
        # Create a dummy permission config
        # Use .as_posix() to avoid backslash issues in YAML f-string
        allowed_root = tmp_path / "allowed"
        allowed_root.mkdir()
        forbidden_root = tmp_path / "forbidden"
        forbidden_root.mkdir()
        
        config_file = tmp_path / "permissions.yaml"
        config_file.write_text(f"""
allowed_paths:
  - "{allowed_root.as_posix()}"
forbidden_paths:
  - "{forbidden_root.as_posix()}"
""")
        return Sandbox(config_path=str(config_file)), allowed_root, forbidden_root

    def test_logger_initialized(self, sandbox):
        sb, _, _ = sandbox
        assert hasattr(sb, "logger")
        assert sb.logger is not None

    def test_allowed_path(self, sandbox):
        sb, allowed, _ = sandbox
        test_file = allowed / "file.txt"
        # validate_path returns a Path object if successful
        result = sb.validate_path(str(test_file))
        assert isinstance(result, Path)
        # Compare resolved lowercase paths to be safe on Windows
        assert str(result).lower() == str(test_file.resolve()).lower()

    def test_forbidden_path(self, sandbox):
        sb, _, forbidden = sandbox
        test_file = forbidden / "secret.txt"
        with pytest.raises(SafetyViolation) as excinfo:
            sb.validate_path(str(test_file))
        # Now it should be an explicit ACCESS DENIED because config loaded successfully
        assert "ACCESS DENIED" in str(excinfo.value)

    def test_path_traversal(self, sandbox):
        sb, allowed, _ = sandbox
        # Try to escape the allowed directory
        traversal_path = str(allowed) + "/../../etc/passwd"
        with pytest.raises(SafetyViolation):
            sb.validate_path(traversal_path)

    def test_empty_or_none(self, sandbox):
        sb, _, _ = sandbox
        with pytest.raises(SafetyViolation) as excinfo:
            sb.validate_path("")
        assert "Empty path" in str(excinfo.value)
        
        with pytest.raises(SafetyViolation):
            sb.validate_path(None)
