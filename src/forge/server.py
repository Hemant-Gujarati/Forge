"""Small authenticated HTTP API for the native Android companion."""

from __future__ import annotations

import hmac
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from collections.abc import Callable

from forge.tasks import Task, TaskQueue
from forge.approvals import ApprovalStore


class ForgeApiServer:
    def __init__(
        self,
        tasks: TaskQueue,
        access_token: str,
        submit_task: Callable[[str], Task] | None = None,
        approvals: ApprovalStore | None = None,
        resolve_approval: Callable[[str, bool], tuple[object | None, str]] | None = None,
    ) -> None:
        self.tasks = tasks
        self.access_token = access_token
        self.submit_task = submit_task
        self.approvals = approvals
        self.resolve_approval = resolve_approval

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
                if self.path == "/v1/approvals":
                    if not api.is_authorized(self.headers.get("Authorization", "")):
                        return self.respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    approvals = [] if api.approvals is None else [approval.__dict__ for approval in api.approvals.list()]
                    return self.respond(HTTPStatus.OK, {"approvals": approvals})
                self.respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self) -> None:  # noqa: N802
                if self.path.startswith("/v1/approvals/"):
                    if not api.is_authorized(self.headers.get("Authorization", "")):
                        return self.respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    if api.approvals is None:
                        return self.respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "approvals_unavailable"})
                    parts = self.path.split("/")
                    if len(parts) != 5 or parts[-1] not in {"approve", "reject"}:
                        return self.respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                    if api.resolve_approval is None:
                        approval = api.approvals.decide(parts[-2], parts[-1] == "approve")
                        message = "Approval updated."
                    else:
                        approval, message = api.resolve_approval(parts[-2], parts[-1] == "approve")
                    if approval is None:
                        return self.respond(HTTPStatus.NOT_FOUND, {"error": "pending_approval_not_found"})
                    return self.respond(HTTPStatus.OK, {"approval": approval.__dict__, "message": message})
                if self.path != "/v1/tasks":
                    return self.respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                if not api.is_authorized(self.headers.get("Authorization", "")):
                    return self.respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                if api.submit_task is None:
                    return self.respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "tasks_unavailable"})
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 20_000:
                        raise ValueError("Request body is too large")
                    payload = json.loads(self.rfile.read(length))
                    prompt = payload.get("prompt", "")
                    if not isinstance(prompt, str) or not prompt.strip():
                        raise ValueError("A non-empty prompt is required")
                    task = api.submit_task(prompt.strip())
                except (ValueError, json.JSONDecodeError) as error:
                    return self.respond(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                self.respond(HTTPStatus.ACCEPTED, {"id": task.id, "status": task.status})

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
