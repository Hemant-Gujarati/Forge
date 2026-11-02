import pytest

from forge.server import ForgeApiServer
from forge.tasks import TaskQueue


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
