from threading import Event

from forge.tasks import TaskQueue


def test_cancels_queued_task() -> None:
    queue = TaskQueue(workers=1)
    unblock = Event()
    queue.submit(lambda: unblock.wait(1), lambda task: None)
    queued = queue.submit(lambda: "never", lambda task: None)
    assert queue.cancel(queued.id) is not None
    assert queue.get(queued.id).status == "cancelled"
    unblock.set()
