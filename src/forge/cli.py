"""Command-line entry point for Forge."""

from __future__ import annotations

import argparse
from pathlib import Path

from forge import __version__
from forge.config import load_config
from forge.runtime import ForgeRuntime
from forge.server import ForgeApiServer
from forge.tasks import Task
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
    subparsers.add_parser("serve", help="Run the local API for the native Android app")
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

        runtime = ForgeRuntime(config, Path.cwd())
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
                tasks = runtime.tasks.recent()
                if not tasks:
                    return "No tasks have run in this Forge session."
                return "\n".join(f"{task.id}: {task.status}" for task in tasks)
            if message.text == "/approvals":
                approvals = runtime.approvals.list()
                if not approvals:
                    return "No actions are waiting for approval."
                return "\n".join(f"{item.id}: {item.action} — {item.summary}" for item in approvals)
            if message.text.startswith("/approve ") or message.text.startswith("/reject "):
                approve = message.text.startswith("/approve ")
                approval_id = message.text.split(maxsplit=1)[1]
                _, result = runtime.resolve_approval(approval_id, approve)
                return result
            if message.text.startswith("/status"):
                _, *parts = message.text.split(maxsplit=1)
                if not parts:
                    return "Forge is online. Use /tasks or /status <task-id>."
                task = runtime.tasks.get(parts[0])
                if task is None:
                    return f"No task found with ID {parts[0]}."
                if task.status == "failed":
                    return f"Task {task.id}: failed — {task.error}"
                return f"Task {task.id}: {task.status}"
            task = runtime.submit(
                str(message.chat_id), message.text, lambda completed: complete(message.chat_id, completed)
            )
            return f"Task {task.id} queued. I will send the result here."

        print("Forge Telegram transport is running. Press Ctrl+C to stop.")
        bot.run(handler)
        return 0
    if args.command == "serve":
        if not config.server.access_token:
            parser.error("A server.access_token is required for the native-app API.")
        tls_paths = [config.server.tls_cert_path, config.server.tls_key_path]
        if any(tls_paths) and not all(tls_paths):
            parser.error("Set both server.tls_cert_path and server.tls_key_path, or neither.")
        if config.server.host not in {"127.0.0.1", "localhost", "::1"} and not all(tls_paths):
            parser.error("TLS certificate and key paths are required when listening beyond localhost.")
        runtime = ForgeRuntime(config, Path.cwd())
        protocol = "https" if all(tls_paths) else "http"
        print(f"Forge API listening on {protocol}://{config.server.host}:{config.server.port}")
        ForgeApiServer(
            runtime.tasks,
            config.server.access_token,
            lambda prompt: runtime.submit("android", prompt),
            runtime.approvals,
            runtime.resolve_approval,
        ).serve(
            config.server.host,
            config.server.port,
            config.server.tls_cert_path,
            config.server.tls_key_path,
        )
        return 0
    return 1

