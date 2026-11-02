"""Small background task runner for remote interfaces."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from uuid import uuid4


@dataclass
class Task:
    id: str
    status: str = "queued"
    result: str | None = None
    error: str | None = None


@dataclass
class TaskQueue:
    workers: int = 1
    database: Path | str | None = None
    _tasks: dict[str, Task] = field(default_factory=dict)
    _futures: dict[str, object] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        if self.database is not None:
            self.connection = sqlite3.connect(self.database, check_same_thread=False)
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL, result TEXT, error TEXT)"
            )
            self.connection.commit()
            for row in self.connection.execute(
                "SELECT id, status, result, error FROM tasks"
            ):
                task = Task(*row)
                if task.status in {"queued", "running"}:
                    task.status = "interrupted"
                self._tasks[task.id] = task
                self._save(task)
        self._executor = ThreadPoolExecutor(
            max_workers=self.workers, thread_name_prefix="forge-task"
        )

    def _save(self, task: Task) -> None:
        if self.database is None:
            return
        self.connection.execute(
            "INSERT OR REPLACE INTO tasks(id, status, result, error) VALUES (?, ?, ?, ?)",
            (task.id, task.status, task.result, task.error),
        )
        self.connection.commit()

    def submit(
        self, operation: Callable[[], str], on_complete: Callable[[Task], None]
    ) -> Task:
        task = Task(id=uuid4().hex[:8])
        with self._lock:
            self._tasks[task.id] = task
            self._save(task)

        def run() -> None:
            with self._lock:
                task.status = "running"
                self._save(task)
            try:
                result = operation()
                with self._lock:
                    task.result = result
                    task.status = "completed"
                    self._save(task)
            except Exception as error:  # noqa: BLE001 - task failures must remain visible to remote clients.
                with self._lock:
                    task.error = str(error)
                    task.status = "failed"
                    self._save(task)
            try:
                on_complete(task)
            except Exception:  # noqa: BLE001 - notification failures do not change task outcome.
                # A failed notification must not corrupt the recorded task result.
                return

        future = self._executor.submit(run)
        with self._lock:
            self._futures[task.id] = future
        return task

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def recent(self, limit: int = 10) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())[-max(1, limit) :]

    def cancel(self, task_id: str) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
            future = self._futures.get(task_id)
            if (
                task is None
                or future is None
                or task.status != "queued"
                or not future.cancel()
            ):
                return None
            task.status = "cancelled"
            self._save(task)
            return task
