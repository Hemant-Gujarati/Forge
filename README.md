# Forge

Forge is a local-first coding assistant for Windows and Linux. It has a terminal interface, a Telegram remote-control adapter, and a future native Android companion app.

## Principles

- Local models through Ollama by default; paid providers remain optional.
- Telegram only for remote control; no WhatsApp or Twilio integration.
- Tools are limited to explicitly approved workspace directories.
- Destructive actions require explicit approval by default.

## Status

Milestone 5 adds read-only Git tools for safe remote inspection: status, diff, and recent history. Forge will require an explicit approval flow before it can create commits.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
forge doctor
forge config show
forge telegram
```

Copy `forge.example.yaml` to `forge.yaml` to configure Forge locally. Never commit bot tokens or API keys.

To enable Telegram, set `telegram.enabled` to `true`, add the token from BotFather, and add your numeric Telegram chat ID to `allowed_chat_ids`.

