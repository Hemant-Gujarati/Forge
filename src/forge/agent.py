"""Conversation agent. Tool execution is added in a later milestone."""

from __future__ import annotations

from typing import Any

from forge.providers.ollama import OllamaProvider
from forge.sessions import SessionStore
from forge.tools.registry import ToolRegistry


SYSTEM_PROMPT = (
    "You are Forge, a local-first coding assistant. Use available read-only tools to inspect a "
    "workspace when needed. Be concise and never claim to have changed files unless a tool confirmed it."
)


class ForgeAgent:
    def __init__(self, provider: OllamaProvider, sessions: SessionStore, tools: ToolRegistry) -> None:
        self.provider = provider
        self.sessions = sessions
        self.tools = tools

    def respond(self, session_id: str, prompt: str) -> str:
        self.sessions.add(session_id, "user", prompt)
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.sessions.history(session_id))
        for _ in range(8):
            response = self.provider.chat(messages, self.tools.definitions())
            if not response.tool_calls:
                self.sessions.add(session_id, "assistant", response.content)
                return response.content
            messages.append({"role": "assistant", "content": response.content, "tool_calls": [
                {"function": {"name": call.name, "arguments": call.arguments}} for call in response.tool_calls
            ]})
            for call in response.tool_calls:
                messages.append({"role": "tool", "content": self.tools.execute(call.name, call.arguments)})
        return "I stopped after reaching the safe tool-call limit. Please narrow the request."

