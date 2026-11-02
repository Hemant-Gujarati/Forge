from pathlib import Path

import pytest

from forge.config import load_config


def test_rejects_invalid_server_port(tmp_path: Path) -> None:
    config_file = tmp_path / "forge.yaml"
    config_file.write_text("server:\n  port: 70000\n", encoding="utf-8")
    with pytest.raises(ValueError, match="server.port"):
        load_config(config_file)


def test_rejects_enabled_telegram_without_allowlist(tmp_path: Path) -> None:
    config_file = tmp_path / "forge.yaml"
    config_file.write_text(
        "telegram:\n  enabled: true\n  bot_token: test\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="allowed_chat_ids"):
        load_config(config_file)


def test_rejects_provider_without_an_implemented_adapter(tmp_path: Path) -> None:
    config_file = tmp_path / "forge.yaml"
    config_file.write_text("default_provider: openai\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Only the local Ollama provider"):
        load_config(config_file)


@pytest.mark.parametrize("mode", ["safe", "auto"])
def test_rejects_unimplemented_safety_modes(tmp_path: Path, mode: str) -> None:
    config_file = tmp_path / "forge.yaml"
    config_file.write_text(f"safety:\n  mode: {mode}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="safety.mode currently supports only: ask"):
        load_config(config_file)
