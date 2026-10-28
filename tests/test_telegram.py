import httpx

from forge.config import TelegramConfig
from forge.telegram import TelegramBot


def test_accepts_text_message() -> None:
    config = TelegramConfig(bot_token="test-token", allowed_chat_ids=[42])
    bot = TelegramBot(config, client=httpx.Client(transport=httpx.MockTransport(lambda request: None)))
    messages = bot.messages([{"message": {"message_id": 5, "chat": {"id": 42}, "text": "/status"}}])
    assert messages[0].chat_id == 42
    assert messages[0].text == "/status"


def test_ignores_non_text_update() -> None:
    config = TelegramConfig(bot_token="test-token")
    bot = TelegramBot(config, client=httpx.Client(transport=httpx.MockTransport(lambda request: None)))
    assert bot.messages([{"message": {"chat": {"id": 42}, "photo": []}}]) == []
