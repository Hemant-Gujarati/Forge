import re
from pathlib import Path

import pytest

from forge.cli import main


def test_malformed_yaml_shows_cli_error(tmp_path: Path) -> None:
    config = tmp_path / "forge.yaml"
    config.write_text("default_provider: [broken", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--config", str(config), "doctor"])
    assert error.value.code == 2


def test_token_command_generates_url_safe_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["token"]) == 0
    token = capsys.readouterr().out.strip()
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", token)
