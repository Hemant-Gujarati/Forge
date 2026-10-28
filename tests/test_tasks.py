from forge.tasks import TaskQueue


def test_recent_starts_with_no_tasks() -> None:
    queue = TaskQueue()
    assert queue.recent() == []
