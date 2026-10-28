# Forge

Forge is a local-first coding assistant for Windows and Linux. It has a terminal interface, a Telegram remote-control adapter, and a future native Android companion app.

## Principles

- Local models through Ollama by default; paid providers remain optional.
- Telegram only for remote control; no WhatsApp or Twilio integration.
- Tools are limited to explicitly approved workspace directories.
- Destructive actions require explicit approval by default.

## Status

Milestone 1 establishes the Python package, configuration, workspace guard, local session store, and command-line interface. The agent loop and Telegram polling follow next.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
forge doctor
forge config show
```

Copy `forge.example.yaml` to `forge.yaml` to configure Forge locally. Never commit bot tokens or API keys.

