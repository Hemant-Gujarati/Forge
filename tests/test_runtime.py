from pathlib import Path

from forge.config import ForgeConfig
from forge.runtime import ForgeRuntime


def test_runtime_creates_a_task_queue(tmp_path: Path) -> None:
    runtime = ForgeRuntime(ForgeConfig(), tmp_path)
    assert runtime.tasks.recent() == []
