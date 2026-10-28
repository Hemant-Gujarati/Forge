"""Safe, provider-neutral tool definitions and dispatch."""

from __future__ import annotations

import json
from typing import Any

from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.shell import ShellTools
from forge.approvals import ApprovalStore


class ToolRegistry:
    def __init__(
        self, files: FileTools, git: GitTools, approvals: ApprovalStore, shell: ShellTools | None = None
    ) -> None:
        self.files = files
        self.git = git
        self.approvals = approvals
        self.shell = shell

    def definitions(self) -> list[dict[str, Any]]:
        tools = [
            self._definition("read_file", {"path": {"type": "string"}}, ["path"]),
            self._definition("write_file", {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
            self._definition("edit_file", {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, ["path", "old_text", "new_text"]),
            self._definition("list_directory", {"path": {"type": "string"}}, []),
            self._definition("git_status", {}, []),
            self._definition("git_diff", {"staged": {"type": "boolean"}}, []),
            self._definition("git_log", {"count": {"type": "integer"}}, []),
            self._definition("git_commit", {"message": {"type": "string"}}, ["message"]),
        ]
        if self.shell is not None and self.shell.enabled:
            tools.append(self._definition("run_command", {"command": {"type": "string"}, "path": {"type": "string"}, "timeout": {"type": "integer"}}, ["command"]))
        return tools

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        try:
            if name == "read_file":
                result: Any = self.files.read_file(str(arguments["path"]))
            elif name in {"write_file", "edit_file"}:
                return self._request_file_approval(name, arguments)
            elif name == "run_command" and self.shell is not None and self.shell.enabled:
                approval = self.approvals.request(
                    "run_command",
                    f"run_command: {arguments.get('command', '')}",
                    dict(arguments),
                )
                return json.dumps({"ok": False, "approval_id": approval.id, "error": "Approval required before running this command."})
            elif name == "git_commit":
                message = str(arguments.get("message", ""))
                if not message.strip():
                    raise ValueError("A commit message is required")
                approval = self.approvals.request("git_commit", f"git_commit: {message}", {"message": message})
                return json.dumps({"ok": False, "approval_id": approval.id, "error": "Approval required before creating a Git commit."})
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
