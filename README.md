# Forge

Forge is a local-first coding assistant for Windows and Linux. It includes a Python CLI, a Telegram bot for remote control, and a native Kotlin/Compose Android companion.

## What works now

- Local Ollama chat and model listing.
- Workspace-limited file reading, search, and discovery.
- Optional shell access, file writes, and Git commits behind explicit approval.
- Telegram long-polling with an allowed-chat-ID list; commands include `/tasks`, `/status`, `/cancel`, and approval controls.
- An authenticated HTTPS API for Android task submission, status, cancellation, and approvals.
- Android app pairing by entering the desktop HTTPS address and access token. The app stores them with AndroidX encrypted preferences.

No paid model provider is configured. Ollama runs models locally; Telegram requires an internet connection and a bot token.

## Run the CLI

Install Python 3.11 or newer and Ollama. From this repository, create a virtual environment and install Forge:

```sh
python -m venv .venv
```

Activate it with `\.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on Linux, then run:

```sh
python -m pip install -e .
ollama pull llama3.2
```

Copy `forge.example.yaml` to `forge.yaml` (`Copy-Item forge.example.yaml forge.yaml` in PowerShell or `cp forge.example.yaml forge.yaml` on Linux). Then run `forge doctor` and `forge chat`.

## Telegram

Create a bot with Telegram's BotFather. Set `telegram.enabled`, `telegram.bot_token`, and your numeric `allowed_chat_ids` in the local `forge.yaml`, then start `forge telegram`. Keep the bot token private; `forge.yaml` is ignored by Git.

## Android companion

Open the `android` folder in Android Studio and build or run the app. For pairing, start the desktop API with `forge serve`, then enter its HTTPS address and token in the app. Generate a token with `forge token` and save it as `server.access_token` in `forge.yaml`.

The desktop API requires TLS when bound beyond localhost, and the Android app accepts HTTPS only. Use a private network and a certificate trusted by Android; do not expose the API publicly. A self-signed certificate needs to be trusted on the phone before pairing.

## Safety and Git

Forge limits file tools to configured `workspace_roots`. It hides common local secret paths. File changes, shell commands, and Git commits require approval; every shell command still requires approval even when `safety.allow_shell: true`.

Forge's agent can request commits for approval. The project itself is committed and pushed at reviewed milestones; it does not automatically push each edit.

## Development checks

```sh
python -m pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pytest -q
```

GitHub Actions runs Python checks on pushes and pull requests. Android changes also build the debug app and instrumentation-test APKs.

To build Android APKs locally, run `gradlew :app:assembleDebug :app:assembleDebugAndroidTest` from `android` (use `gradlew.bat` on Windows). To run the UI test, start an emulator or connect a device and run `gradlew :app:connectedDebugAndroidTest`.
