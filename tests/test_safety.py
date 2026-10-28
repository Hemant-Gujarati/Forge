from pathlib import Path

import pytest

from forge.safety import WorkspaceGuard


def test_allows_path_inside_root(tmp_path: Path) -> None:
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    assert guard.resolve(tmp_path / "project" / "file.py") == tmp_path / "project" / "file.py"


def test_rejects_path_outside_root(tmp_path: Path) -> None:
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    with pytest.raises(PermissionError):
        guard.resolve(tmp_path.parent / "outside.txt")
