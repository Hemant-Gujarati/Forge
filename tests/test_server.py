from threading import Thread

import httpx
import pytest

from forge.approvals import ApprovalStore
from forge.server import ForgeApiServer
from forge.tasks import Task, TaskQueue


@pytest.fixture
def api_client():
    server_api = ForgeApiServer(
        TaskQueue(),
        "test-access-token",
        lambda prompt: Task(id="task-123", status="queued"),
        ApprovalStore(":memory:"),
    )
    server = server_api.create_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{server.server_address[1]}", trust_env=False
        ) as client:
            yield client
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_authorization_requires_matching_bearer_token() -> None:
    api = ForgeApiServer(TaskQueue(), "secret")
    assert api.is_authorized("Bearer secret")
    assert not api.is_authorized("Bearer wrong")
    assert not api.is_authorized("")


@pytest.mark.parametrize(
    "body",
    [b"not-json", b"[]", b'{"prompt": 42}', b'{"prompt": "  "}'],
)
def test_rejects_invalid_task_request_bodies(body: bytes) -> None:
    with pytest.raises((TypeError, ValueError)):
        ForgeApiServer.parse_task_prompt(body)


def test_task_prompt_is_trimmed() -> None:
    assert (
        ForgeApiServer.parse_task_prompt(b'{"prompt": "  fix tests  "}') == "fix tests"
    )


def test_api_requires_authorization(api_client: httpx.Client) -> None:
    response = api_client.get("/v1/tasks")

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}


def test_api_accepts_valid_task_prompt(api_client: httpx.Client) -> None:
    response = api_client.post(
        "/v1/tasks",
        json={"prompt": "Explain this project"},
        headers={"Authorization": "Bearer test-access-token"},
    )

    assert response.status_code == 202
    assert response.json() == {"id": "task-123", "status": "queued"}


def test_api_rejects_oversized_task_prompt(api_client: httpx.Client) -> None:
    response = api_client.post(
        "/v1/tasks",
        content=b" " * 20_001,
        headers={"Authorization": "Bearer test-access-token"},
    )

    assert response.status_code == 400
