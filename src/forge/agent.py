"""Conversation agent. Tool execution is added in a later milestone."""

from __future__ import annotations

from forge.providers.ollama import OllamaProvider
from forge.sessions import SessionStore


SYSTEM_PROMPT = (
    "You are Forge, a local-first coding assistant. Be concise, explain planned file or command "
    "changes before executing them, and never claim to have changed files unless a tool confirmed it."
)


class ForgeAgent:
    def __init__(self, provider: OllamaProvider, sessions: SessionStore) -> None:
        self.provider = provider
        self.sessions = sessions

    def respond(self, session_id: str, prompt: str) -> str:
        self.sessions.add(session_id, "user", prompt)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.sessions.history(session_id))
        answer = self.provider.chat(messages)
        self.sessions.add(session_id, "assistant", answer)
        return answer

