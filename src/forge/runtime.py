"""Shared task runtime used by Telegram and the native-app API."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from forge.agent import ForgeAgent
from forge.config import ForgeConfig
from forge.providers import OllamaProvider
from forge.sessions import SessionStore
from forge.tasks import Task, TaskQueue


class ForgeRuntime:
    def __init__(self, config: ForgeConfig, working_directory: Path) -> None:
        ollama = config.providers.get("ollama", {})
        provider = OllamaProvider(
            base_url=ollama.get("base_url", "http://localhost:11434"),
            model=ollama.get("default_model", "llama3.2"),
        )
        state_directory = working_directory / ".forge"
        state_directory.mkdir(exist_ok=True)
        self.agent = ForgeAgent(provider, SessionStore(state_directory / "sessions.db"))
        self.tasks = TaskQueue()

    def submit(self, session_id: str, prompt: str, on_complete: Callable[[Task], None] | None = None) -> Task:
        return self.tasks.submit(
            lambda: self.agent.respond(session_id, prompt),
            on_complete or (lambda task: None),
        )
