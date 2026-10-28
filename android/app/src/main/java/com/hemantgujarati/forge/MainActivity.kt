package com.hemantgujarati.forge

import android.os.Bundle
import android.os.Handler
import android.os.Looper
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
    var accessToken by remember { mutableStateOf("") }
    var prompt by remember { mutableStateOf("") }
    var latestTaskId by remember { mutableStateOf("") }
    var approvals by remember { mutableStateOf(emptyList<ForgeApiClient.ApprovalItem>()) }
    var status by remember { mutableStateOf("Not connected") }
    val api = remember { ForgeApiClient() }
    val mainThread = remember { Handler(Looper.getMainLooper()) }
    MaterialTheme {
        Scaffold(topBar = { TopAppBar(title = { Text("Forge") }) }) { padding ->
            Column(
                modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text("Your desktop coding assistant", style = MaterialTheme.typography.titleLarge)
                Text("Pair this app with Forge running on your PC. Telegram can control the same Forge instance remotely.")
                OutlinedTextField(
                    value = desktopAddress,
                    onValueChange = { desktopAddress = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Desktop address") },
                    placeholder = { Text("https://forge-pc.example") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = accessToken,
                    onValueChange = { accessToken = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Access token") },
                    singleLine = true,
                )
                Button(
                    onClick = {
                        status = "Checking desktop…"
                        Thread {
                            val result = api.health(desktopAddress)
                            mainThread.post {
                                status = result.fold(
                                    onSuccess = { "Connected to Forge." },
                                    onFailure = { "Connection failed: ${it.message}" },
                                )
                            }
                        }.start()
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Check connection") }
                OutlinedTextField(
                    value = prompt,
                    onValueChange = { prompt = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Coding task") },
                    placeholder = { Text("Explain this project") },
                )
                Button(
                    onClick = {
                        status = "Submitting task…"
                        Thread {
                            val result = api.submitTask(desktopAddress, accessToken, prompt)
                            mainThread.post {
                                status = result.fold(
                                    onSuccess = {
                                        latestTaskId = it
                                        "Task $it queued."
                                    },
                                    onFailure = { "Task failed: ${it.message}" },
                                )
                            }
                        }.start()
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = desktopAddress.isNotBlank() && accessToken.isNotBlank() && prompt.isNotBlank(),
                ) { Text("Run task") }
                if (latestTaskId.isNotBlank()) {
                    Button(
                        onClick = {
                            status = "Checking task…"
                            Thread {
                                val result = api.taskStatus(desktopAddress, accessToken, latestTaskId)
                                mainThread.post {
                                    status = result.fold(
                                        onSuccess = { "Task $latestTaskId: $it" },
                                        onFailure = { "Status failed: ${it.message}" },
                                    )
                                }
                            }.start()
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Refresh task status") }
                }
                Button(
                    onClick = {
                        status = "Loading approvals…"
                        Thread {
                            val result = api.pendingApprovals(desktopAddress, accessToken)
                            mainThread.post {
                                result.fold(
                                    onSuccess = {
                                        approvals = it
                                        status = if (it.isEmpty()) "No pending approvals." else "${it.size} approval(s) pending."
                                    },
                                    onFailure = { status = "Approval refresh failed: ${it.message}" },
                                )
                            }
                        }.start()
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = desktopAddress.isNotBlank() && accessToken.isNotBlank(),
                ) { Text("Refresh approvals") }
                approvals.forEach { approval ->
                    Text("${approval.action}: ${approval.summary}")
                    Button(
                        onClick = {
                            Thread {
                                val result = api.resolveApproval(desktopAddress, accessToken, approval.id, true)
                                mainThread.post {
                                    status = result.fold(
                                        onSuccess = {
                                            approvals = approvals.filterNot { item -> item.id == approval.id }
                                            it
                                        },
                                        onFailure = { "Approval failed: ${it.message}" },
                                    )
                                }
                            }.start()
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Approve ${approval.id}") }
                    Button(
                        onClick = {
                            Thread {
                                val result = api.resolveApproval(desktopAddress, accessToken, approval.id, false)
                                mainThread.post {
                                    status = result.fold(
                                        onSuccess = {
                                            approvals = approvals.filterNot { item -> item.id == approval.id }
                                            it
                                        },
                                        onFailure = { "Rejection failed: ${it.message}" },
                                    )
                                }
                            }.start()
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Reject ${approval.id}") }
                }
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
