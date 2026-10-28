from pathlib import Path

from forge.approvals import ApprovalStore
from forge.safety import WorkspaceGuard
from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.registry import ToolRegistry


def test_commit_is_staged_for_approval(tmp_path: Path) -> None:
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    approvals = ApprovalStore(":memory:")
    registry = ToolRegistry(FileTools(guard), GitTools(guard), approvals)
    response = registry.execute("git_commit", {"message": "feat: safe change"})
    assert "approval_id" in response
    assert approvals.list()[0].action == "git_commit"
