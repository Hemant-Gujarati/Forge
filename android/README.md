# Forge Android

Native Android companion for Forge, built with Kotlin and Jetpack Compose.

The first screen is a local pairing shell. The desktop API supports authenticated health, task status, task submission, and approvals. Pair the app only with a private-network HTTPS Forge server; Telegram remains a separate remote-control channel to the same desktop Forge instance.

The app currently checks a desktop connection, submits coding tasks, lists recent tasks and results, refreshes task status, and approves or rejects pending Forge actions. It encrypts the pairing token and desktop address with AndroidX Security and provides a control to forget the paired desktop.

## Open

Open the `android` folder in Android Studio. Use JDK 17 and install Android SDK Platform 36 when prompted. This module uses the Compose setup recommended by Android's official documentation.

Run Android UI tests from Android Studio or with `gradlew :app:connectedDebugAndroidTest` after connecting an emulator/device.

