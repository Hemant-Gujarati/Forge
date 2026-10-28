"""Minimal Ollama chat adapter using its local HTTP API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    tool_calls: list[ToolCall]


class OllamaProvider:
    def __init__(self, base_url: str, model: str, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = client or httpx.Client(timeout=120)

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        request: dict[str, Any] = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            request["tools"] = tools
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json=request,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        message = payload["message"]
        calls = [
            ToolCall(name=call["function"]["name"], arguments=call["function"].get("arguments", {}))
            for call in message.get("tool_calls", [])
        ]
        return ProviderResponse(content=str(message.get("content", "")), tool_calls=calls)

