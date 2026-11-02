"""Workspace-limited file operations."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import ClassVar

from forge.safety import WorkspaceGuard


class FileTools:
    PRIVATE_NAMES: ClassVar[set[str]] = {
        ".env",
        ".env.local",
        "forge.yaml",
        "config.yaml",
    }
    PRIVATE_DIRECTORIES: ClassVar[set[str]] = {".git", ".forge"}

    def __init__(self, guard: WorkspaceGuard, max_read_bytes: int = 1_000_000) -> None:
        self.guard = guard
        self.max_read_bytes = max_read_bytes

    def read_file(self, path: str) -> str:
        target = self.guard.resolve(path)
        self._ensure_not_private(target)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")
        if target.stat().st_size > self.max_read_bytes:
            raise ValueError(f"File exceeds {self.max_read_bytes} byte read limit")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        target = self.guard.resolve(path)
        self._ensure_not_private(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {target}"

    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        target = self.guard.resolve(path)
        self._ensure_not_private(target)
        content = self.read_file(str(target))
        matches = content.count(old_text)
        if matches != 1:
            raise ValueError(
                f"Expected exactly one matching text block; found {matches}"
            )
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {target}"

    def list_directory(self, path: str = ".") -> list[str]:
        target = self.guard.resolve(path)
        if not target.is_dir():
            raise NotADirectoryError(f"Directory not found: {target}")
        return [
            entry.name
            for entry in sorted(target.iterdir(), key=lambda item: item.name.lower())
            if entry.name.lower() not in self.PRIVATE_NAMES
            and entry.name.lower() not in self.PRIVATE_DIRECTORIES
        ]

    def find_files(self, pattern: str, path: str = ".", limit: int = 200) -> list[str]:
        root = self.guard.resolve(path)
        if not root.is_dir():
            raise NotADirectoryError(f"Directory not found: {root}")
        matches: list[str] = []
        for candidate in root.rglob("*"):
            if candidate.is_symlink() or self._is_private_path(candidate):
                continue
            if candidate.is_file() and fnmatch.fnmatch(candidate.name, pattern):
                matches.append(str(candidate))
                if len(matches) >= min(max(limit, 1), 1000):
                    break
        return matches

    def search_text(
        self, pattern: str, path: str = ".", file_pattern: str = "*", limit: int = 100
    ) -> list[str]:
        root = self.guard.resolve(path)
        if not root.is_dir():
            raise NotADirectoryError(f"Directory not found: {root}")
        regex = re.compile(pattern)
        results: list[str] = []
        for candidate in root.rglob("*"):
            if candidate.is_symlink() or self._is_private_path(candidate):
                continue
            if not candidate.is_file() or not fnmatch.fnmatch(
                candidate.name, file_pattern
            ):
                continue
            if candidate.stat().st_size > self.max_read_bytes:
                continue
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if regex.search(line):
                    results.append(f"{candidate}:{line_number}:{line[:500]}")
                    if len(results) >= min(max(limit, 1), 1000):
                        return results
        return results

    def _ensure_not_private(self, target: Path) -> None:
        if self._is_private_path(target):
            raise PermissionError(
                f"Forge file tools cannot access private path: {target.name}"
            )

    def _is_private_path(self, path: Path) -> bool:
        try:
            resolved = self.guard.resolve(path)
        except (OSError, PermissionError):
            return True
        return any(
            part.lower() in self.PRIVATE_NAMES | self.PRIVATE_DIRECTORIES
            for part in resolved.parts
        )
