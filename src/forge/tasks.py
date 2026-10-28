"""Small background task runner for remote interfaces."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
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
    _tasks: dict[str, Task] = field(default_factory=dict)
    _futures: dict[str, object] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="forge-task")

    def submit(self, operation: callable, on_complete: callable) -> Task:
        task = Task(id=uuid4().hex[:8])
        with self._lock:
            self._tasks[task.id] = task

        def run() -> None:
            with self._lock:
                task.status = "running"
            try:
                result = operation()
                with self._lock:
                    task.result = result
                    task.status = "completed"
            except Exception as error:  # Remote errors must be returned, not crash polling.
                with self._lock:
                    task.error = str(error)
                    task.status = "failed"
            on_complete(task)

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
            if task is None or future is None or task.status != "queued" or not future.cancel():
                return None
            task.status = "cancelled"
            return task

