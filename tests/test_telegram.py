import httpx
import pytest

from forge.config import TelegramConfig
from forge.telegram import TelegramBot


def test_accepts_text_message() -> None:
    config = TelegramConfig(bot_token="test-token", allowed_chat_ids=[42])
    bot = TelegramBot(
        config, client=httpx.Client(transport=httpx.MockTransport(lambda request: None))
    )
    messages = bot.messages(
        [{"message": {"message_id": 5, "chat": {"id": 42}, "text": "/status"}}]
    )
    assert messages[0].chat_id == 42
    assert messages[0].text == "/status"


def test_ignores_non_text_update() -> None:
    config = TelegramConfig(bot_token="test-token")
    bot = TelegramBot(
        config, client=httpx.Client(transport=httpx.MockTransport(lambda request: None))
    )
    assert bot.messages([{"message": {"chat": {"id": 42}, "photo": []}}]) == []


def test_splits_telegram_messages_by_utf16_size() -> None:
    text = "🙂" * 2500
    chunks = TelegramBot._split_message(text)

    assert len(chunks) == 2
    assert "".join(chunks) == text
    assert all(len(chunk.encode("utf-16-le")) // 2 <= 4000 for chunk in chunks)


def test_ignores_malformed_updates() -> None:
    config = TelegramConfig(bot_token="test-token", allowed_chat_ids=[42])
    bot = TelegramBot(config)
    updates = [
        None,
        {"message": []},
        {"message": {"chat": None, "text": "hello", "message_id": 1}},
        {"message": {"chat": {"id": 42}, "text": "hello"}},
    ]

    assert bot.messages(updates) == []


def test_rejects_invalid_telegram_json_response() -> None:
    def invalid_response(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    config = TelegramConfig(bot_token="test-token")
    bot = TelegramBot(
        config, client=httpx.Client(transport=httpx.MockTransport(invalid_response))
    )

    with pytest.raises(RuntimeError, match="invalid JSON"):
        bot.get_updates()


def test_rejects_unexpected_telegram_response_shape() -> None:
    def invalid_shape(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    config = TelegramConfig(bot_token="test-token")
    bot = TelegramBot(
        config, client=httpx.Client(transport=httpx.MockTransport(invalid_shape))
    )

    with pytest.raises(TypeError, match="invalid response"):
        bot.get_updates()
