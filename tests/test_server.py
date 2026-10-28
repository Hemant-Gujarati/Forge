from forge.server import ForgeApiServer
from forge.tasks import TaskQueue


def test_authorization_requires_matching_bearer_token() -> None:
    api = ForgeApiServer(TaskQueue(), "secret")
    assert api.is_authorized("Bearer secret")
    assert not api.is_authorized("Bearer wrong")
    assert not api.is_authorized("")
