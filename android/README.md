# Forge Android

Native Android companion for Forge, built with Kotlin and Jetpack Compose.

The first screen is a local pairing shell. The desktop API supports authenticated health, task status, task submission, and approvals. Pair the app only with a private-network HTTPS Forge server; Telegram remains a separate remote-control channel to the same desktop Forge instance.

The app currently checks a desktop connection, submits coding tasks, lists recent tasks and results, refreshes task status, and approves or rejects pending Forge actions. It encrypts the pairing token and desktop address with AndroidX Security and provides a control to forget the paired desktop.

## Open

Open the `android` folder in Android Studio. The app compiles against Android SDK Platform 37 and uses JDK 17 or newer. Android Studio may use its bundled JDK. The Gradle Wrapper downloads the free Gradle 9.6 distribution as needed.

Build the debug APK with `gradlew :app:assembleDebug`. Compile the Android UI test APK with `gradlew :app:assembleDebugAndroidTest`. Run UI tests with `gradlew :app:connectedDebugAndroidTest` after starting an emulator or connecting a device.

