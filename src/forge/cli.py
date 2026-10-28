"""Command-line entry point for Forge."""

from __future__ import annotations

import argparse
from pathlib import Path

from forge.agent import ForgeAgent
from forge import __version__
from forge.config import load_config
from forge.providers import OllamaProvider
from forge.sessions import SessionStore
from forge.tasks import Task, TaskQueue
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

        ollama = config.providers.get("ollama", {})
        provider = OllamaProvider(
            base_url=ollama.get("base_url", "http://localhost:11434"),
            model=ollama.get("default_model", "llama3.2"),
        )
        forge_dir = Path.cwd() / ".forge"
        forge_dir.mkdir(exist_ok=True)
        agent = ForgeAgent(provider, SessionStore(forge_dir / "sessions.db"))
        queue = TaskQueue()
        bot = TelegramBot(config.telegram)

        def complete(chat_id: int, task: Task) -> None:
            if task.status == "completed":
                bot.send_message(chat_id, task.result or "Task completed with no response.")
            else:
                bot.send_message(chat_id, f"Task {task.id} failed: {task.error}")

        def handler(message: TelegramMessage) -> str:
            if message.text == "/start":
                return "Forge is connected. Send a coding question to begin."
            if message.text == "/tasks":
                tasks = queue.recent()
                if not tasks:
                    return "No tasks have run in this Forge session."
                return "\n".join(f"{task.id}: {task.status}" for task in tasks)
            if message.text.startswith("/status"):
                _, *parts = message.text.split(maxsplit=1)
                if not parts:
                    return "Forge is online. Use /tasks or /status <task-id>."
                task = queue.get(parts[0])
                if task is None:
                    return f"No task found with ID {parts[0]}."
                if task.status == "failed":
                    return f"Task {task.id}: failed — {task.error}"
                return f"Task {task.id}: {task.status}"
            task = queue.submit(
                lambda: agent.respond(str(message.chat_id), message.text),
                lambda completed: complete(message.chat_id, completed),
            )
            return f"Task {task.id} queued. I will send the result here."

        print("Forge Telegram transport is running. Press Ctrl+C to stop.")
        bot.run(handler)
        return 0
    return 1

