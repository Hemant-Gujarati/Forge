from pathlib import Path

from forge.safety import WorkspaceGuard
from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.registry import ToolRegistry


def test_unknown_tool_returns_serialized_error(tmp_path: Path) -> None:
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    registry = ToolRegistry(FileTools(guard), GitTools(guard))
    assert '"ok": false' in registry.execute("unknown", {})
