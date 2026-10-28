from pathlib import Path

from forge.safety import WorkspaceGuard
from forge.tools.git import GitTools


def test_log_count_is_bounded(tmp_path: Path) -> None:
    tools = GitTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    assert tools.max_output_chars == 20_000
