from pathlib import Path

import pytest

from forge.safety import WorkspaceGuard
from forge.tools.shell import ShellTools


def test_blocks_commands_when_disabled(tmp_path: Path) -> None:
    tools = ShellTools(WorkspaceGuard([str(tmp_path)], tmp_path), enabled=False)
    with pytest.raises(PermissionError):
        tools.run_command("echo should-not-run", str(tmp_path))


def test_caps_timeout() -> None:
    assert ShellTools(WorkspaceGuard(["."], Path.cwd()), enabled=True, max_timeout_seconds=20).max_timeout_seconds == 20
