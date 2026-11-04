"""Loopback-only HTTP interface for Cendrix AI."""

from __future__ import annotations

import json
import logging
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from app.core.inference import FriendlyInferenceError, LocalAssistant
from app.memory.conversation_store import ConversationStore


ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "app" / "interface" / "static"
MAX_REQUEST_BYTES = 16_384
logger = logging.getLogger(__name__)
LOCAL_ORIGIN_HOSTS = {"localhost", "127.0.0.1"}


def _is_local_browser_origin(origin: str | None) -> bool:
    if not origin or origin == "null":
        return False
    try:
        parsed = urlsplit(origin)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname in LOCAL_ORIGIN_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.path == ""
            and parsed.query == ""
            and parsed.fragment == ""
            and (parsed.port is None or 1 <= parsed.port <= 65535)
            and bool(re.fullmatch(r"https?://[^/]+", origin))
        )
    except ValueError:
        return False


def create_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    assistant: LocalAssistant | None = None,
    store: ConversationStore | None = None,
) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("Cendrix can only bind to 127.0.0.1")
    runtime = assistant or LocalAssistant()
    conversations = store or ConversationStore()

    class Handler(BaseHTTPRequestHandler):
        server_version = "CendrixLocal/1.0"

        def log_message(self, format_string: str, *args: Any) -> None:
            logger.info("%s - %s", self.address_string(), format_string % args)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
                "style-src 'self'; script-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )
            origin = self.headers.get("Origin")
            if _is_local_browser_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            origin = self.headers.get("Origin")
            if (
                urlsplit(self.path).path not in {"/api/health", "/api/chat"}
                or not _is_local_browser_origin(origin)
            ):
                self.send_error(403)
                return
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Vary", "Origin")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _send_static(self, filename: str) -> None:
            allowed = {
                "index.html",
                "app.js",
                "styles.css",
                "manifest.webmanifest",
                "sw.js",
                "cendrix.svg",
            }
            if filename not in allowed:
                self.send_error(404)
                return
            path = STATIC_DIR / filename
            try:
                content = path.read_bytes()
            except FileNotFoundError:
                self.send_error(404)
                return
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".webmanifest": "application/manifest+json",
                ".svg": "image/svg+xml",
            }.get(path.suffix, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
                "style-src 'self'; script-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(content)

        def _read_json(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("Invalid request length.") from error
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("Request must be between 1 byte and 16 KB.")
            try:
                payload = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError("Request body must be valid JSON.") from error
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")
            return payload

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send_static("index.html")
            elif path in {"/app.js", "/styles.css", "/manifest.webmanifest", "/sw.js"}:
                self._send_static(path[1:])
            elif path == "/api/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "offline": True,
                        "service": "cendrix-ai",
                        "protocol": "cendrix-local-v1",
                    },
                )
            elif path == "/api/conversations":
                self._send_json(200, {"conversations": conversations.list_conversations()})
            elif path.startswith("/api/conversations/") and path.endswith("/messages"):
                raw_id = unquote(path[len("/api/conversations/") : -len("/messages")].strip("/"))
                try:
                    conversation_id = str(uuid.UUID(raw_id))
                except ValueError:
                    self._send_json(400, {"error": "Invalid conversation ID."})
                    return
                self._send_json(
                    200,
                    {"messages": conversations.recent_messages(conversation_id, limit=500)},
                )
            else:
                self.send_error(404)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/chat":
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin is not None and not _is_local_browser_origin(origin):
                self._send_json(403, {"error": "Requests must come from this local app."})
                return
            content_type = self.headers.get_content_type()
            if content_type != "application/json":
                self._send_json(415, {"error": "Request must use application/json."})
                return
            try:
                payload = self._read_json()
                message = payload.get("message")
                raw_id = payload.get("conversation_id")
                if not isinstance(message, str) or not message.strip():
                    raise ValueError("Message must not be empty.")
                if len(message) > 8000:
                    raise ValueError("Message is too long. Please keep it under 8,000 characters.")
                if not isinstance(raw_id, str):
                    raise ValueError("A conversation ID is required.")
                try:
                    conversation_id = str(uuid.UUID(raw_id))
                except ValueError as error:
                    raise ValueError("Invalid conversation ID.") from error
                history = conversations.recent_messages(conversation_id)
                answer = runtime.answer(message, history)
                conversations.add_turn(conversation_id, message, answer)
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            except FriendlyInferenceError as error:
                self._send_json(503, {"error": str(error)})
                return
            except Exception:
                logger.exception("Unexpected local chat request failure")
                self._send_json(
                    500,
                    {"error": "Cendrix encountered a local error. Please try again."},
                )
                return
            self._send_json(
                200,
                {"conversation_id": conversation_id, "answer": answer},
            )

    return ThreadingHTTPServer((host, port), Handler)
