"""Telegram long-polling transport for a personal Forge instance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from forge.config import TelegramConfig


@dataclass(frozen=True)
class TelegramMessage:
    chat_id: int
    message_id: int
    text: str


class TelegramBot:
    """Small Telegram Bot API wrapper using outbound HTTPS polling only."""

    def __init__(self, config: TelegramConfig, client: httpx.Client | None = None) -> None:
        if not config.bot_token:
            raise ValueError("Telegram bot_token is required")
        self.config = config
        self.client = client or httpx.Client(timeout=config.poll_timeout_seconds + 10)
        self.base_url = f"https://api.telegram.org/bot{config.bot_token}"

    def _request(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        response = self.client.post(f"{self.base_url}/{method}", json=payload or {})
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram API request failed"))
        return data["result"]

    def get_updates(self, offset: int | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": self.config.poll_timeout_seconds,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        return self._request("getUpdates", payload)

    def send_message(self, chat_id: int, text: str) -> None:
        self._request("sendMessage", {"chat_id": chat_id, "text": text})

    def messages(self, updates: list[dict[str, Any]]) -> list[TelegramMessage]:
        result: list[TelegramMessage] = []
        for update in updates:
            message = update.get("message") or {}
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text")
            if isinstance(chat_id, int) and isinstance(text, str):
                result.append(TelegramMessage(chat_id, message["message_id"], text))
        return result

    def run(self, handler: Callable[[TelegramMessage], str]) -> None:
        """Poll forever, delivering only allowlisted text messages to the handler."""
        offset: int | None = None
        allowed = set(self.config.allowed_chat_ids)
        while True:
            updates = self.get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
            for message in self.messages(updates):
                if message.chat_id not in allowed:
                    continue
                reply = handler(message)
                if reply:
                    self.send_message(message.chat_id, reply)

