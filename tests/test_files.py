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
