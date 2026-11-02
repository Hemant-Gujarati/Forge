"""Telegram long-polling transport for a personal Forge instance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
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

    def __init__(
        self, config: TelegramConfig, client: httpx.Client | None = None
    ) -> None:
        if not config.bot_token:
            raise ValueError("Telegram bot_token is required")
        self.config = config
        self.client = client or httpx.Client(timeout=config.poll_timeout_seconds + 10)
        self.base_url = f"https://api.telegram.org/bot{config.bot_token}"

    def _request(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        response = self.client.post(f"{self.base_url}/{method}", json=payload or {})
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as error:
            raise RuntimeError("Telegram API returned invalid JSON") from error
        if not isinstance(data, dict):
            raise TypeError("Telegram API returned an invalid response")
        if data.get("ok") is not True:
            description = data.get("description")
            raise RuntimeError(
                description
                if isinstance(description, str)
                else "Telegram API request failed"
            )
        if "result" not in data:
            raise RuntimeError("Telegram API response is missing its result")
        return data["result"]

    def get_updates(self, offset: int | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": self.config.poll_timeout_seconds,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        result = self._request("getUpdates", payload)
        if not isinstance(result, list):
            raise TypeError("Telegram API returned an invalid updates list")
        return result

    def send_message(self, chat_id: int, text: str) -> None:
        for chunk in self._split_message(text):
            self._request("sendMessage", {"chat_id": chat_id, "text": chunk})

    @staticmethod
    def _split_message(text: str, max_utf16_units: int = 4000) -> list[str]:
        """Split messages within Telegram's UTF-16 code-unit size limit."""
        if max_utf16_units < 2:
            raise ValueError("max_utf16_units must be at least 2")
        chunks: list[str] = []
        current: list[str] = []
        units = 0
        for character in text:
            character_units = 2 if ord(character) > 0xFFFF else 1
            if units + character_units > max_utf16_units:
                chunks.append("".join(current))
                current = []
                units = 0
            current.append(character)
            units += character_units
        if current or not chunks:
            chunks.append("".join(current))
        return chunks

    def messages(self, updates: list[dict[str, Any]]) -> list[TelegramMessage]:
        result: list[TelegramMessage] = []
        for update in updates:
            if not isinstance(update, dict):
                continue
            message = update.get("message") or {}
            if not isinstance(message, dict):
                continue
            chat = message.get("chat")
            if not isinstance(chat, dict):
                continue
            chat_id = chat.get("id")
            text = message.get("text")
            message_id = message.get("message_id")
            if (
                isinstance(chat_id, int)
                and isinstance(message_id, int)
                and isinstance(text, str)
            ):
                result.append(TelegramMessage(chat_id, message_id, text))
        return result

    def run(self, handler: Callable[[TelegramMessage], str]) -> None:
        """Poll forever, delivering only allowlisted text messages to the handler."""
        offset: int | None = None
        allowed = set(self.config.allowed_chat_ids)
        while True:
            try:
                updates = self.get_updates(offset)
            except (httpx.HTTPError, RuntimeError, TypeError):
                sleep(2)
                continue
            for update in updates:
                update_id = (
                    update.get("update_id") if isinstance(update, dict) else None
                )
                if isinstance(update_id, int):
                    offset = max(offset or 0, update_id + 1)
            for message in self.messages(updates):
                if message.chat_id not in allowed:
                    continue
                try:
                    reply = handler(message)
                    if reply:
                        self.send_message(message.chat_id, reply)
                except (httpx.HTTPError, RuntimeError, TypeError):
                    continue
