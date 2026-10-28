"""Safe, provider-neutral tool definitions and dispatch."""

from __future__ import annotations

import json
from typing import Any

from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.approvals import ApprovalStore


class ToolRegistry:
    def __init__(self, files: FileTools, git: GitTools, approvals: ApprovalStore) -> None:
        self.files = files
        self.git = git
        self.approvals = approvals

    def definitions(self) -> list[dict[str, Any]]:
        return [
            self._definition("read_file", {"path": {"type": "string"}}, ["path"]),
            self._definition("write_file", {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
            self._definition("edit_file", {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, ["path", "old_text", "new_text"]),
            self._definition("list_directory", {"path": {"type": "string"}}, []),
            self._definition("git_status", {}, []),
            self._definition("git_diff", {"staged": {"type": "boolean"}}, []),
            self._definition("git_log", {"count": {"type": "integer"}}, []),
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        try:
            if name == "read_file":
                result: Any = self.files.read_file(str(arguments["path"]))
            elif name in {"write_file", "edit_file"}:
                return self._request_file_approval(name, arguments)
            elif name == "list_directory":
                result = self.files.list_directory(str(arguments.get("path", ".")))
            elif name == "git_status":
                result = self.git.status()
            elif name == "git_diff":
                result = self.git.diff(staged=bool(arguments.get("staged", False)))
            elif name == "git_log":
                result = self.git.log(count=int(arguments.get("count", 10)))
            else:
                raise ValueError(f"Unknown tool: {name}")
            return json.dumps({"ok": True, "result": result})
        except (KeyError, OSError, PermissionError, RuntimeError, ValueError) as error:
            return json.dumps({"ok": False, "error": str(error)})

    def _request_file_approval(self, action: str, arguments: dict[str, Any]) -> str:
        path = str(arguments.get("path", ""))
        if not path:
            raise ValueError("A file path is required")
        summary = f"{action}: {path}"
        approval = self.approvals.request(action, summary, dict(arguments))
        return json.dumps({"ok": False, "approval_id": approval.id, "error": "Approval required before this file change."})

    @staticmethod
    def _definition(name: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": f"Forge safe tool: {name}",
                "parameters": {"type": "object", "properties": properties, "required": required},
            },
        }
