import httpx

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
