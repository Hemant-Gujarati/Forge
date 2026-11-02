"""Workspace boundaries used by all filesystem tools."""

from __future__ import annotations

from pathlib import Path


class WorkspaceGuard:
    def __init__(self, roots: list[str], base_dir: Path) -> None:
        self.base_dir = base_dir.resolve()
        self.roots = [(self.base_dir / root).resolve() for root in roots]

    def resolve(self, candidate: str | Path) -> Path:
        path = Path(candidate)
        resolved = (path if path.is_absolute() else self.base_dir / path).resolve()
        if not any(resolved.is_relative_to(root) for root in self.roots):
            raise PermissionError(f"Path outside approved workspace: {resolved}")
        return resolved

