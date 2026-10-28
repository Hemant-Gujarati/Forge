from forge.agent import ForgeAgent
from forge.providers.ollama import ProviderResponse
from forge.safety import WorkspaceGuard
from forge.sessions import SessionStore
from forge.tools.files import FileTools
from forge.tools.git import GitTools
from forge.tools.registry import ToolRegistry


class FakeProvider:
    def chat(self, messages, tools) -> ProviderResponse:
        assert messages[-1]["content"] == "Hello"
        return ProviderResponse("Hi from Forge", [])


def test_agent_persists_conversation(tmp_path) -> None:
    store = SessionStore(":memory:")
    guard = WorkspaceGuard([str(tmp_path)], tmp_path)
    tools = ToolRegistry(FileTools(guard), GitTools(guard))
    agent = ForgeAgent(FakeProvider(), store, tools)  # type: ignore[arg-type]
    assert agent.respond("chat-1", "Hello") == "Hi from Forge"
    assert store.history("chat-1")[-1]["content"] == "Hi from Forge"
