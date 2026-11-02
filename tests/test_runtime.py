import subprocess
from pathlib import Path

import pytest

from forge.config import ForgeConfig, SafetyConfig
from forge.runtime import ForgeRuntime


def test_runtime_creates_a_task_queue(tmp_path: Path) -> None:
    runtime = ForgeRuntime(ForgeConfig(), tmp_path)
    assert runtime.tasks.recent() == []


@pytest.mark.parametrize(
    "error", [RuntimeError("git failed"), subprocess.TimeoutExpired("task", 1)]
)
def test_approved_command_failures_are_returned_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    runtime = ForgeRuntime(ForgeConfig(safety=SafetyConfig(allow_shell=True)), tmp_path)
    approval = runtime.approvals.request(
        "run_command", "run_command: test", {"command": "test"}
    )

    def fail_command(*args, **kwargs):
        raise error

    monkeypatch.setattr(runtime.shell, "run_command", fail_command)
    resolved, message = runtime.resolve_approval(approval.id, approve=True)

    assert resolved is not None
    assert "approved but failed" in message
