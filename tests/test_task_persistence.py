import sqlite3
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


def test_unfinished_tasks_are_marked_interrupted_on_restart(tmp_path: Path) -> None:
    database = tmp_path / "tasks.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL, result TEXT, error TEXT)"
    )
    connection.execute("INSERT INTO tasks(id, status) VALUES ('stale-task', 'running')")
    connection.commit()
    connection.close()

    queue = TaskQueue(database=database)
    task = queue.get("stale-task")
    assert task is not None
    assert task.status == "interrupted"
