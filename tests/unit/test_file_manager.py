import pytest
import os
import shutil
from pathlib import Path
from aetox.tools.file_manager import MasterFileManager

class TestFileManager:
    @pytest.fixture
    def fm(self, tmp_path):
        # MasterFileManager uses PathNavigator which defaults to cwd if not specified.
        # We need to ensure it uses our tmp_path.
        tool = MasterFileManager()
        # Mock allowed roots to be our tmp_path
        tool.navigator.allowed_roots = [tmp_path.resolve()]
        tool.navigator.root = tmp_path.resolve()
        tool.navigator.cwd = tmp_path.resolve()
        return tool, tmp_path

    def test_create_folder(self, fm):
        tool, tmp = fm
        folder_path = "test_folder"
        result = tool.execute({"action": "create_folder", "path": folder_path})
        assert result["status"] == "success"
        assert (tmp / folder_path).is_dir()

    def test_create_and_read_file(self, fm):
        tool, tmp = fm
        file_path = "test.txt"
        content = "Hello AetoxClaw"
        
        # Create
        res_create = tool.execute({"action": "create_file", "path": file_path, "content": content})
        assert res_create["status"] == "success"
        
        # Read
        res_read = tool.execute({"action": "read_file", "path": file_path})
        assert res_read["status"] == "success"
        assert res_read["output"] == content

    def test_list_dir(self, fm):
        tool, tmp = fm
        (tmp / "file1.txt").write_text("1")
        (tmp / "file2.txt").write_text("2")
        (tmp / "sub").mkdir()
        
        result = tool.execute({"action": "list_dir", "path": "."})
        assert result["status"] == "success"
        assert "file1.txt" in result["output"]
        assert "sub" in result["output"]

    def test_delete_file(self, fm):
        tool, tmp = fm
        file_path = tmp / "to_delete.txt"
        file_path.write_text("delete me")
        
        result = tool.execute({"action": "delete", "path": "to_delete.txt"})
        assert result["status"] == "success"
        assert not file_path.exists()

    def test_move_file(self, fm):
        tool, tmp = fm
        src = tmp / "old.txt"
        src.write_text("move me")
        dest = "new.txt"
        
        result = tool.execute({"action": "move", "path": "old.txt", "destination": dest})
        assert result["status"] == "success"
        assert not src.exists()
        assert (tmp / dest).exists()

    def test_organize(self, fm):
        tool, tmp = fm
        (tmp / "photo.jpg").write_text("fake image")
        (tmp / "doc.pdf").write_text("fake doc")
        (tmp / "script.py").write_text("print(1)")
        
        result = tool.execute({"action": "organize", "path": "."})
        assert result["status"] == "success"
        assert (tmp / "Images" / "photo.jpg").exists()
        assert (tmp / "Documents" / "doc.pdf").exists()
        assert (tmp / "Code" / "script.py").exists()

    def test_safety_restriction(self, fm):
        tool, _ = fm
        # Try to navigate to a sensitive system path
        # Note: MasterFileManager uses PathNavigator.cd for 'navigate'
        result = tool.execute({"action": "navigate", "path": "C:/Windows"})
        assert result["status"] == "failure"
        assert "Access denied" in result["error"] or "Permission denied" in result["error"]
