from forge.agent import ForgeAgent
from forge.sessions import SessionStore


class FakeProvider:
    def chat(self, messages: list[dict[str, str]]) -> str:
        assert messages[-1]["content"] == "Hello"
        return "Hi from Forge"


def test_agent_persists_conversation() -> None:
    store = SessionStore(":memory:")
    agent = ForgeAgent(FakeProvider(), store)  # type: ignore[arg-type]
    assert agent.respond("chat-1", "Hello") == "Hi from Forge"
    assert store.history("chat-1")[-1]["content"] == "Hi from Forge"
