import pytest
from unittest.mock import MagicMock, patch
from aetox.safety.permission import PermissionManager

@pytest.fixture
def permission_manager(tmp_path):
    config_file = tmp_path / "permissions.yaml"
    config_file.write_text("risk_rules:\n  high:\n    - delete_file\n  medium:\n    - write_file\n")
    return PermissionManager(config_path=str(config_file))

def test_get_risk_level_high(permission_manager):
    assert permission_manager.get_risk_level("delete_file", {}) == "high"

def test_get_risk_level_medium(permission_manager):
    assert permission_manager.get_risk_level("write_file", {"path": "test.txt"}) == "medium"

def test_get_risk_level_low(permission_manager):
    assert permission_manager.get_risk_level("list_dir", {}) == "low"

def test_write_file_external_path(permission_manager):
    # Action write_file outside project folder (starts with / or has / and doesn't start with .)
    assert permission_manager.get_risk_level("write_file", {"path": "/etc/passwd"}) == "high"
    assert permission_manager.get_risk_level("write_file", {"path": "subfolder/test.txt"}) == "high"
    assert permission_manager.get_risk_level("write_file", {"path": "./test.txt"}) == "medium"

def test_request_permission_cli_approve(permission_manager):
    with patch("builtins.input", return_value="y"):
        assert permission_manager.request_permission("delete_file", "Deleting a file") is True

def test_request_permission_cli_deny(permission_manager):
    with patch("builtins.input", return_value="n"):
        assert permission_manager.request_permission("delete_file", "Deleting a file") is False

def test_request_permission_callback(permission_manager):
    mock_callback = MagicMock(return_value=True)
    permission_manager.approval_callback = mock_callback
    
    assert permission_manager.request_permission("delete_file", "Deleting a file") is True
    mock_callback.assert_called_once_with("delete_file", "Deleting a file")

def test_load_config_fallback():
    # Test fallback when config file doesn't exist
    pm = PermissionManager(config_path="non_existent.yaml")
    assert pm.risk_rules == {"high": ["delete_file"], "medium": ["write_file"]}
