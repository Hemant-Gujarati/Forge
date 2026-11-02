"""Configuration loading with safe defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SafetyConfig:
    mode: str = "ask"
    allow_shell: bool = False


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    allowed_chat_ids: list[int] = field(default_factory=list)
    poll_timeout_seconds: int = 30


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 7777
    access_token: str = ""
    tls_cert_path: str = ""
    tls_key_path: str = ""


@dataclass
class ForgeConfig:
    default_provider: str = "ollama"
    workspace_roots: list[str] = field(default_factory=lambda: ["."])
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)


def load_config(path: Path) -> ForgeConfig:
    if not path.exists():
        return ForgeConfig()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise TypeError("Configuration root must be a YAML mapping")
    config = ForgeConfig(
        default_provider=raw.get("default_provider", "ollama"),
        workspace_roots=raw.get("workspace_roots", ["."]),
        providers=raw.get("providers", {}),
        telegram=TelegramConfig(**raw.get("telegram", {})),
        server=ServerConfig(**raw.get("server", {})),
        safety=SafetyConfig(**raw.get("safety", {})),
    )
    validate_config(config)
    return config


def validate_config(config: ForgeConfig) -> None:
    if config.default_provider != "ollama":
        raise ValueError(
            "Only the local Ollama provider is currently supported; paid providers are not configured."
        )
    if (
        not isinstance(config.workspace_roots, list)
        or not config.workspace_roots
        or any(
            not isinstance(root, str) or not root.strip()
            for root in config.workspace_roots
        )
    ):
        raise ValueError("workspace_roots must contain at least one non-empty path")
    if not isinstance(config.providers, dict):
        raise TypeError("providers must be a mapping")
    ollama = config.providers.get("ollama", {})
    if not isinstance(ollama, dict):
        raise TypeError("providers.ollama must be a mapping")
    for key, default in (
        ("base_url", "http://localhost:11434"),
        ("default_model", "llama3.2"),
    ):
        value = ollama.get(key, default)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"providers.ollama.{key} must be a non-empty string")
    if config.safety.mode != "ask":
        raise ValueError("safety.mode currently supports only: ask")
    if not isinstance(config.safety.allow_shell, bool):
        raise TypeError("safety.allow_shell must be a boolean")
    if not isinstance(config.telegram.enabled, bool):
        raise TypeError("telegram.enabled must be a boolean")
    if not isinstance(config.telegram.bot_token, str):
        raise TypeError("telegram.bot_token must be a string")
    if not isinstance(config.telegram.allowed_chat_ids, list) or any(
        isinstance(chat_id, bool) or not isinstance(chat_id, int)
        for chat_id in config.telegram.allowed_chat_ids
    ):
        raise ValueError("telegram.allowed_chat_ids must be a list of integer IDs")
    if (
        isinstance(config.telegram.poll_timeout_seconds, bool)
        or not isinstance(config.telegram.poll_timeout_seconds, int)
        or not 1 <= config.telegram.poll_timeout_seconds <= 50
    ):
        raise ValueError("telegram.poll_timeout_seconds must be between 1 and 50")
    if not isinstance(config.server.host, str) or not config.server.host.strip():
        raise ValueError("server.host must be a non-empty string")
    if (
        isinstance(config.server.port, bool)
        or not isinstance(config.server.port, int)
        or not 1 <= config.server.port <= 65535
    ):
        raise ValueError("server.port must be between 1 and 65535")
    if not isinstance(config.server.access_token, str):
        raise TypeError("server.access_token must be a string")
    if config.server.access_token and len(config.server.access_token) < 32:
        raise ValueError(
            "server.access_token must be at least 32 characters; use `forge token` to generate one"
        )
    if not isinstance(config.server.tls_cert_path, str) or not isinstance(
        config.server.tls_key_path, str
    ):
        raise TypeError("server TLS paths must be strings")
    if bool(config.server.tls_cert_path) != bool(config.server.tls_key_path):
        raise ValueError("Set both server TLS certificate and key paths, or neither")
    if config.telegram.enabled and (
        not config.telegram.bot_token.strip() or not config.telegram.allowed_chat_ids
    ):
        raise ValueError(
            "Telegram requires bot_token and at least one allowed_chat_ids entry"
        )
