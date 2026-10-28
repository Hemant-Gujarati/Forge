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
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="forge-task")

    def submit(self, operation: callable, on_complete: callable) -> Task:
        task = Task(id=uuid4().hex[:8])
        with self._lock:
            self._tasks[task.id] = task

        def run() -> None:
            task.status = "running"
            try:
                task.result = operation()
                task.status = "completed"
            except Exception as error:  # Remote errors must be returned, not crash polling.
                task.error = str(error)
                task.status = "failed"
            on_complete(task)

        self._executor.submit(run)
        return task

