"""Command-line entry point for Forge."""

from __future__ import annotations

import argparse
from pathlib import Path

from forge import __version__
from forge.config import load_config
from forge.telegram import TelegramBot, TelegramMessage


def _config_path(value: str | None) -> Path:
    return Path(value) if value else Path.cwd() / "forge.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge", description="Local-first coding assistant")
    parser.add_argument("--config", help="Path to Forge YAML configuration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Check local prerequisites")
    config_parser = subparsers.add_parser("config", help="Inspect configuration")
    config_parser.add_argument("action", choices=["show"])
    subparsers.add_parser("telegram", help="Run the Telegram remote-control transport")
    args = parser.parse_args(argv)
    config = load_config(_config_path(args.config))

    if args.command == "doctor":
        ollama = config.providers.get("ollama", {}).get("base_url", "http://localhost:11434")
        print(f"Forge {__version__}")
        print(f"Default provider: {config.default_provider}")
        print(f"Ollama endpoint: {ollama}")
        print("Telegram: configured" if config.telegram.bot_token else "Telegram: not configured")
        return 0

    if args.command == "config":
        print(f"Provider: {config.default_provider}")
        print(f"Safety mode: {config.safety.mode}")
        print(f"Workspace roots: {', '.join(config.workspace_roots)}")
        return 0
    if args.command == "telegram":
        if not config.telegram.enabled:
            parser.error("Telegram is disabled. Set telegram.enabled: true in forge.yaml.")
        if not config.telegram.allowed_chat_ids:
            parser.error("Telegram needs at least one allowed_chat_ids entry.")

        def handler(message: TelegramMessage) -> str:
            if message.text == "/start":
                return "Forge is connected. Agent tasks will be available soon."
            if message.text == "/status":
                return "Forge transport is online. No task is currently running."
            return "Forge received your message. Agent execution is not enabled yet."

        print("Forge Telegram transport is running. Press Ctrl+C to stop.")
        TelegramBot(config.telegram).run(handler)
        return 0
    return 1

