from pathlib import Path

from forge.approvals import ApprovalStore
from forge.safety import WorkspaceGuard
from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.registry import ToolRegistry
from forge.tools.shell import ShellTools


def test_command_is_staged_for_approval(tmp_path: Path) -> None:
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    approvals = ApprovalStore(":memory:")
    registry = ToolRegistry(FileTools(guard), GitTools(guard), approvals, ShellTools(guard, enabled=True))
    response = registry.execute("run_command", {"command": "python --version"})
    assert "approval_id" in response
    assert approvals.list()[0].action == "run_command"
