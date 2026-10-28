"""Minimal Ollama chat adapter using its local HTTP API."""

from __future__ import annotations

from typing import Any

import httpx


class OllamaProvider:
    def __init__(self, base_url: str, model: str, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = client or httpx.Client(timeout=120)

    def chat(self, messages: list[dict[str, str]]) -> str:
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return str(payload["message"]["content"])

