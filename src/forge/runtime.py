"""Shared task runtime used by Telegram and the native-app API."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from forge.agent import ForgeAgent
from forge.approvals import Approval, ApprovalStore
from forge.config import ForgeConfig
from forge.providers import OllamaProvider
from forge.sessions import SessionStore
from forge.tasks import Task, TaskQueue
from forge.safety import WorkspaceGuard
from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.registry import ToolRegistry


class ForgeRuntime:
    def __init__(self, config: ForgeConfig, working_directory: Path) -> None:
        ollama = config.providers.get("ollama", {})
        provider = OllamaProvider(
            base_url=ollama.get("base_url", "http://localhost:11434"),
            model=ollama.get("default_model", "llama3.2"),
        )
        state_directory = working_directory / ".forge"
        state_directory.mkdir(exist_ok=True)
        self.approvals = ApprovalStore(state_directory / "forge.db")
        guard = WorkspaceGuard(config.workspace_roots, working_directory)
        self.files = FileTools(guard)
        tools = ToolRegistry(self.files, GitTools(guard), self.approvals)
        self.agent = ForgeAgent(provider, SessionStore(state_directory / "sessions.db"), tools)
        self.tasks = TaskQueue()

    def submit(self, session_id: str, prompt: str, on_complete: Callable[[Task], None] | None = None) -> Task:
        return self.tasks.submit(
            lambda: self.agent.respond(session_id, prompt),
            on_complete or (lambda task: None),
        )

    def resolve_approval(self, approval_id: str, approve: bool) -> tuple[Approval | None, str]:
        approval = self.approvals.decide(approval_id, approve)
        if approval is None:
            return None, "No pending approval found with that ID."
        if not approve:
            return approval, f"{approval.action} rejected."
        try:
            if approval.action == "write_file":
                result = self.files.write_file(str(approval.payload["path"]), str(approval.payload["content"]))
            elif approval.action == "edit_file":
                result = self.files.edit_file(
                    str(approval.payload["path"]),
                    str(approval.payload["old_text"]),
                    str(approval.payload["new_text"]),
                )
            else:
                return approval, f"{approval.action} approved. No executor is available yet."
            return approval, result
        except (KeyError, OSError, PermissionError, ValueError) as error:
            return approval, f"{approval.action} was approved but failed: {error}"
