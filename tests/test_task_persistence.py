from pathlib import Path

from forge.tasks import TaskQueue


def test_task_history_survives_restart(tmp_path: Path) -> None:
    database = tmp_path / "tasks.db"
    first = TaskQueue(database=database)
    task = first.submit(lambda: "saved result", lambda _: None)
    first._futures[task.id].result(timeout=2)
    second = TaskQueue(database=database)
    restored = second.get(task.id)
    assert restored is not None
    assert restored.status == "completed"
    assert restored.result == "saved result"
