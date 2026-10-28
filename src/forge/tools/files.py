"""Workspace-limited file operations."""

from __future__ import annotations

from pathlib import Path

from forge.safety import WorkspaceGuard


class FileTools:
    def __init__(self, guard: WorkspaceGuard, max_read_bytes: int = 1_000_000) -> None:
        self.guard = guard
        self.max_read_bytes = max_read_bytes

    def read_file(self, path: str) -> str:
        target = self.guard.resolve(path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")
        if target.stat().st_size > self.max_read_bytes:
            raise ValueError(f"File exceeds {self.max_read_bytes} byte read limit")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        target = self.guard.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {target}"

    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        target = self.guard.resolve(path)
        content = self.read_file(str(target))
        matches = content.count(old_text)
        if matches != 1:
            raise ValueError(f"Expected exactly one matching text block; found {matches}")
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {target}"

    def list_directory(self, path: str = ".") -> list[str]:
        target = self.guard.resolve(path)
        if not target.is_dir():
            raise NotADirectoryError(f"Directory not found: {target}")
        return [entry.name for entry in sorted(target.iterdir(), key=lambda item: item.name.lower())]
