package com.hemantgujarati.forge

import org.json.JSONObject
import java.net.URL
import javax.net.ssl.HttpsURLConnection

class ForgeApiClient {
    fun health(endpoint: String): Result<String> = request(endpoint, "/health", null, null) { response ->
        JSONObject(response).getString("status")
    }

    fun submitTask(endpoint: String, token: String, prompt: String): Result<String> =
        request(endpoint, "/v1/tasks", token, JSONObject(mapOf("prompt" to prompt)).toString()) { response ->
            JSONObject(response).getString("id")
        }

    fun taskStatus(endpoint: String, token: String, taskId: String): Result<String> =
        request(endpoint, "/v1/tasks/$taskId", token, null) { response ->
            JSONObject(response).getString("status")
        }

    private fun request(
        endpoint: String,
        path: String,
        token: String?,
        body: String?,
        parse: (String) -> String,
    ): Result<String> = runCatching {
        require(endpoint.startsWith("https://")) { "Forge desktop address must use HTTPS." }
        val connection = URL(endpoint.trimEnd('/') + path).openConnection() as HttpsURLConnection
        connection.requestMethod = if (body == null) "GET" else "POST"
        connection.connectTimeout = 10_000
        connection.readTimeout = 30_000
        connection.setRequestProperty("Accept", "application/json")
        if (token != null) connection.setRequestProperty("Authorization", "Bearer $token")
        if (body != null) {
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toByteArray()) }
        }
        val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
        val response = stream.bufferedReader().use { it.readText() }
        check(connection.responseCode in 200..299) { response }
        parse(response)
    }
}
