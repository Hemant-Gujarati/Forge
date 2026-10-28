# Forge Android

Native Android companion for Forge, built with Kotlin and Jetpack Compose.

The first screen is a local pairing shell. The desktop API supports authenticated health, task status, task submission, and approvals. Pair the app only with a private-network HTTPS Forge server; Telegram remains a separate remote-control channel to the same desktop Forge instance.

The app currently checks a desktop connection, submits a coding task, and refreshes that task's status. It intentionally accepts HTTPS endpoints only and does not persist the access token yet.

## Open

Open the `android` folder in Android Studio. Use JDK 17 and install Android SDK Platform 36 when prompted. This module uses the Compose setup recommended by Android's official documentation.

