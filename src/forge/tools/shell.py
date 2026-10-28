"""Explicitly enabled, workspace-bound shell execution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from forge.safety import WorkspaceGuard


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class ShellTools:
    def __init__(self, guard: WorkspaceGuard, enabled: bool, max_timeout_seconds: int = 60) -> None:
        self.guard = guard
        self.enabled = enabled
        self.max_timeout_seconds = max_timeout_seconds

    def run_command(self, command: str, path: str = ".", timeout: int = 60) -> CommandResult:
        if not self.enabled:
            raise PermissionError("Shell access is disabled. Set safety.allow_shell: true to enable it.")
        if not command.strip():
            raise ValueError("Command cannot be empty")
        cwd = self.guard.resolve(path)
        if not cwd.is_dir():
            raise NotADirectoryError(f"Working directory not found: {cwd}")
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=min(max(timeout, 1), self.max_timeout_seconds),
            check=False,
        )
        return CommandResult(
            exit_code=completed.returncode,
            stdout=completed.stdout[:20_000],
            stderr=completed.stderr[:20_000],
        )
