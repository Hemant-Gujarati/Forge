package com.hemantgujarati.forge

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ForgeApp() }
    }
}

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun ForgeApp() {
    var desktopAddress by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Not connected") }
    MaterialTheme {
        Scaffold(topBar = { TopAppBar(title = { Text("Forge") }) }) { padding ->
            Column(
                modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text("Your desktop coding assistant", style = MaterialTheme.typography.titleLarge)
                Text("Pair this app with Forge running on your PC. Telegram can continue to control the same Forge instance remotely.")
                OutlinedTextField(
                    value = desktopAddress,
                    onValueChange = { desktopAddress = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Desktop address") },
                    placeholder = { Text("https://forge-pc.local") },
                    singleLine = true,
                )
                Button(
                    onClick = { status = "Pairing will be enabled when the desktop API is ready." },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Pair with desktop") }
                Text(status, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun ForgeAppPreview() {
    ForgeApp()
}
