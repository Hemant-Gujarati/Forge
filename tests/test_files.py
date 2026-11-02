from pathlib import Path

import pytest

from forge.safety import WorkspaceGuard
from forge.tools import FileTools


def test_write_read_and_edit_file(tmp_path: Path) -> None:
    files = FileTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    files.write_file(str(tmp_path / "notes" / "todo.txt"), "first item")
    assert files.read_file(str(tmp_path / "notes" / "todo.txt")) == "first item"
    files.edit_file(str(tmp_path / "notes" / "todo.txt"), "first", "second")
    assert files.read_file(str(tmp_path / "notes" / "todo.txt")) == "second item"


def test_rejects_outside_workspace(tmp_path: Path) -> None:
    files = FileTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    with pytest.raises(PermissionError):
        files.write_file(str(tmp_path.parent / "outside.txt"), "no")


def test_blocks_private_config_and_state(tmp_path: Path) -> None:
    files = FileTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    with pytest.raises(PermissionError):
        files.read_file(str(tmp_path / "forge.yaml"))
    with pytest.raises(PermissionError):
        files.read_file(str(tmp_path / ".forge" / "sessions.db"))


def test_hides_private_items_from_directory_listing(tmp_path: Path) -> None:
    (tmp_path / "forge.yaml").write_text("secret: value", encoding="utf-8")
    (tmp_path / ".forge").mkdir()
    (tmp_path / "app.py").write_text("pass", encoding="utf-8")
    files = FileTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    assert files.list_directory(".") == ["app.py"]


def test_search_and_discovery_skip_private_paths(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("needle here", encoding="utf-8")
    (tmp_path / "forge.yaml").write_text("needle secret", encoding="utf-8")
    state = tmp_path / ".forge"
    state.mkdir()
    (state / "secret.py").write_text("needle secret", encoding="utf-8")
    files = FileTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    assert files.find_files("*.py") == [str(tmp_path / "src" / "app.py")]
    assert files.search_text("needle", file_pattern="*.py") == [
        f"{tmp_path / 'src' / 'app.py'}:1:needle here"
    ]
