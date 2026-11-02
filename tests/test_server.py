import socket
from collections.abc import Iterator
from threading import Thread

import httpx
import pytest

from forge.approvals import ApprovalStore
from forge.server import ForgeApiServer
from forge.tasks import Task, TaskQueue


@pytest.fixture
def api_client() -> Iterator[tuple[httpx.Client, ApprovalStore]]:
    approvals = ApprovalStore(":memory:")
    server_api = ForgeApiServer(
        TaskQueue(),
        "test-access-token",
        lambda prompt: Task(id="task-123", status="queued"),
        approvals,
    )
    server = server_api.create_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{server.server_address[1]}", trust_env=False
        ) as client:
            yield client, approvals
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_authorization_requires_matching_bearer_token() -> None:
    api = ForgeApiServer(TaskQueue(), "secret")
    assert api.is_authorized("Bearer secret")
    assert not api.is_authorized("Bearer wrong")
    assert not api.is_authorized("")


def test_api_server_uses_ipv6_for_ipv6_localhost() -> None:
    server = ForgeApiServer(TaskQueue(), "secret").create_server("::1", 0)
    try:
        assert server.address_family == socket.AF_INET6
    finally:
        server.server_close()


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


def test_api_requires_authorization(
    api_client: tuple[httpx.Client, ApprovalStore],
) -> None:
    client, _ = api_client
    response = client.get("/v1/tasks")

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_api_accepts_valid_task_prompt(
    api_client: tuple[httpx.Client, ApprovalStore],
) -> None:
    client, _ = api_client
    response = client.post(
        "/v1/tasks",
        json={"prompt": "Explain this project"},
        headers={"Authorization": "Bearer test-access-token"},
    )

    assert response.status_code == 202
    assert response.json() == {"id": "task-123", "status": "queued"}


def test_api_rejects_oversized_task_prompt(
    api_client: tuple[httpx.Client, ApprovalStore],
) -> None:
    client, _ = api_client
    response = client.post(
        "/v1/tasks",
        content=b" " * 20_001,
        headers={"Authorization": "Bearer test-access-token"},
    )

    assert response.status_code == 400


def test_approval_api_hides_action_payload(
    api_client: tuple[httpx.Client, ApprovalStore],
) -> None:
    client, approvals = api_client
    approvals.request(
        "write_file",
        "write_file: notes.txt",
        {"path": "notes.txt", "content": "private draft"},
    )

    response = client.get(
        "/v1/approvals", headers={"Authorization": "Bearer test-access-token"}
    )

    assert response.status_code == 200
    approval = response.json()["approvals"][0]
    assert set(approval) == {"id", "action", "summary"}
    assert approval["action"] == "write_file"
    assert approval["summary"] == "write_file: notes.txt"
