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
    if not config.workspace_roots or any(
        not isinstance(root, str) or not root.strip() for root in config.workspace_roots
    ):
        raise ValueError("workspace_roots must contain at least one non-empty path")
    if config.safety.mode not in {"ask", "safe", "auto"}:
        raise ValueError("safety.mode must be one of: ask, safe, auto")
    if not 1 <= config.telegram.poll_timeout_seconds <= 50:
        raise ValueError("telegram.poll_timeout_seconds must be between 1 and 50")
    if not 1 <= config.server.port <= 65535:
        raise ValueError("server.port must be between 1 and 65535")
    if config.telegram.enabled and (
        not config.telegram.bot_token or not config.telegram.allowed_chat_ids
    ):
        raise ValueError(
            "Telegram requires bot_token and at least one allowed_chat_ids entry"
        )
