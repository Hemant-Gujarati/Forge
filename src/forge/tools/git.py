"""Read-only Git inspection tools for approved workspaces."""

from __future__ import annotations

import subprocess
from pathlib import Path

from forge.safety import WorkspaceGuard


class GitTools:
    def __init__(self, guard: WorkspaceGuard, max_output_chars: int = 20_000) -> None:
        self.guard = guard
        self.max_output_chars = max_output_chars

    def _run(self, arguments: list[str], path: str = ".") -> str:
        cwd = self.guard.resolve(path)
        completed = subprocess.run(
            ["git", *arguments], cwd=cwd, text=True, capture_output=True, check=False
        )
        output = (completed.stdout + completed.stderr).strip()
        if completed.returncode != 0:
            raise RuntimeError(output or "Git command failed")
        return output[: self.max_output_chars]

    def status(self, path: str = ".") -> str:
        return self._run(["status", "--short", "--branch"], path)

    def diff(self, path: str = ".", staged: bool = False, file: str | None = None) -> str:
        arguments = ["diff"]
        if staged:
            arguments.append("--staged")
        if file:
            working_directory = self.guard.resolve(path)
            target = self.guard.resolve(file)
            try:
                arguments.extend(["--", str(target.relative_to(working_directory))])
            except ValueError as error:
                raise PermissionError("File must be inside the selected working directory") from error
        return self._run(arguments, path)

    def log(self, path: str = ".", count: int = 10) -> str:
        return self._run(["log", f"--max-count={min(max(count, 1), 50)}", "--oneline"], path)

    def commit(self, message: str, path: str = ".") -> str:
        if not message.strip():
            raise ValueError("Commit message cannot be empty")
        self._run(["add", "-A"], path)
        return self._run(["commit", "-m", message.strip()], path)
