"""Small authenticated HTTP API for the native Android companion."""

from __future__ import annotations

import hmac
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from forge.tasks import TaskQueue


class ForgeApiServer:
    def __init__(self, tasks: TaskQueue, access_token: str) -> None:
        self.tasks = tasks
        self.access_token = access_token

    def create_server(self, host: str, port: int) -> ThreadingHTTPServer:
        api = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/health":
                    return self.respond(HTTPStatus.OK, {"status": "ok"})
                if self.path == "/v1/tasks":
                    if not api.is_authorized(self.headers.get("Authorization", "")):
                        return self.respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    tasks = [{"id": task.id, "status": task.status} for task in api.tasks.recent()]
                    return self.respond(HTTPStatus.OK, {"tasks": tasks})
                self.respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def respond(self, status: HTTPStatus, body: dict[str, object]) -> None:
                encoded = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format: str, *args: object) -> None:
                return

        return ThreadingHTTPServer((host, port), Handler)

    def is_authorized(self, header: str) -> bool:
        expected = f"Bearer {self.access_token}"
        return bool(self.access_token) and hmac.compare_digest(header, expected)

    def serve(self, host: str, port: int) -> None:
        self.create_server(host, port).serve_forever()
