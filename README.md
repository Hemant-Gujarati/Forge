# Forge

Forge is a local-first coding assistant for Windows and Linux. It has a terminal interface, a Telegram remote-control adapter, and a future native Android companion app.

## Principles

- Local models through Ollama by default; paid providers remain optional.
- Telegram only for remote control; no WhatsApp or Twilio integration.
- Tools are limited to explicitly approved workspace directories.
- Destructive actions require explicit approval by default.

## Status

Milestone 6 adds remote task visibility. In Telegram, `/tasks` lists recent jobs and `/status <task-id>` checks a specific one.

The native Kotlin/Compose Android module now includes its first pairing screen in [`android/`](android/). The desktop `forge serve` command exposes initial Android API endpoints, including remote task submission. Do not expose it publicly; use a private network, TLS certificate, and a non-empty `server.access_token`. Non-local API bindings require TLS.

Potentially destructive actions will use Forge's approval store. Telegram supports `/approvals`, `/approve <id>`, and `/reject <id>`; the Android API exposes the same pending approvals.

To make shell commands available to the agent, explicitly set `safety.allow_shell: true`; each individual command still requires approval.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
forge doctor
forge config show
forge telegram
```

Copy `forge.example.yaml` to `forge.yaml` to configure Forge locally. Never commit bot tokens or API keys.

GitHub Actions runs Ruff and pytest on every push and pull request.

To enable Telegram, set `telegram.enabled` to `true`, add the token from BotFather, and add your numeric Telegram chat ID to `allowed_chat_ids`.

