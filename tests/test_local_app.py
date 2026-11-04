from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.core.inference import FriendlyInferenceError, LocalAssistant, MAX_HISTORY_CHARS
from app.interface.server import create_server
from app.memory.conversation_store import ConversationStore


class FakeAssistant:
    def __init__(self, answer: str = "Local answer") -> None:
        self.answer_text = answer
        self.calls: list[tuple[str, list[dict[str, str]] | None]] = []

    def answer(self, message: str, history: list[dict[str, str]] | None = None) -> str:
        self.calls.append((message, history))
        return self.answer_text


class LocalAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "database" / "chat.sqlite3"
        self.store = ConversationStore(self.database)
        self.assistant = FakeAssistant()
        self.server = create_server(port=0, assistant=self.assistant, store=self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def _request(
        self,
        path: str,
        method: str = "GET",
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, object] | str]:
        data = None if payload is None else json.dumps(payload).encode()
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers=request_headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                body = response.read().decode()
                content_type = response.headers.get("Content-Type", "")
                return response.status, json.loads(body) if "json" in content_type else body
        except urllib.error.HTTPError as error:
            body = error.read().decode()
            return error.code, json.loads(body)

    def test_server_is_loopback_only_and_rejects_other_bind_hosts(self) -> None:
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        with self.assertRaises(ValueError):
            create_server(host="0.0.0.0", port=0, assistant=self.assistant, store=self.store)

    def test_chat_persists_messages_and_returns_model_output_as_plain_data(self) -> None:
        self.assistant.answer_text = "Example output: rm -rf /"
        conversation_id = str(uuid.uuid4())
        status, response = self._request(
            "/api/chat",
            "POST",
            {"conversation_id": conversation_id, "message": "Hello"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["answer"], "Example output: rm -rf /")
        self.assertEqual(
            self.store.recent_messages(conversation_id),
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Example output: rm -rf /"},
            ],
        )
        self.assertEqual(self.assistant.calls, [("Hello", [])])
        self.assertEqual(
            self._request("/api/conversations")[1]["conversations"][0]["id"],
            conversation_id,
        )

    def test_follow_up_receives_bounded_saved_conversation_context(self) -> None:
        conversation_id = str(uuid.uuid4())
        self._request(
            "/api/chat",
            "POST",
            {"conversation_id": conversation_id, "message": "My name is Mira."},
        )
        self._request(
            "/api/chat",
            "POST",
            {"conversation_id": conversation_id, "message": "What is my name?"},
        )
        history = self.assistant.calls[1][1]
        self.assertEqual(
            history,
            [
                {"role": "user", "content": "My name is Mira."},
                {"role": "assistant", "content": "Local answer"},
            ],
        )

    def test_local_shell_is_served_with_security_headers_and_health(self) -> None:
        status, page = self._request("/")
        self.assertEqual(status, 200)
        self.assertIn("Cendrix AI", page)
        request = urllib.request.Request(self.base_url + "/")
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        health_status, health = self._request("/api/health")
        self.assertEqual(health_status, 200)
        self.assertEqual(
            health,
            {
                "ok": True,
                "offline": True,
                "service": "cendrix-ai",
                "protocol": "cendrix-local-v1",
            },
        )

    def test_input_validation_and_inference_failures_are_reported(self) -> None:
        status, response = self._request(
            "/api/chat", "POST", {"conversation_id": "not-an-id", "message": "Hi"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid conversation ID", response["error"])
        self.assertEqual(self.assistant.calls, [])

        class FailingAssistant:
            def answer(self, message: str, history: list[dict[str, str]]) -> str:
                raise FriendlyInferenceError("The local model is missing.")

        server = create_server(
            port=0,
            assistant=FailingAssistant(),
            store=self.store,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_address[1]}/api/chat",
                data=json.dumps(
                    {"conversation_id": str(uuid.uuid4()), "message": "Hi"}
                ).encode(),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(urllib.error.HTTPError) as error_context:
                urllib.request.urlopen(request, timeout=5)
            self.assertEqual(error_context.exception.code, 503)
            self.assertIn("local model is missing", error_context.exception.read().decode())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_cross_origin_chat_requests_are_denied(self) -> None:
        status, response = self._request(
            "/api/chat",
            "POST",
            {"conversation_id": str(uuid.uuid4()), "message": "Hi"},
            headers={"Origin": "https://attacker.example"},
        )
        self.assertEqual(status, 403)
        self.assertIn("local app", response["error"])
        self.assertEqual(self.assistant.calls, [])

    def test_loopback_nocta_origin_can_probe_and_preflight_cendrix(self) -> None:
        request = urllib.request.Request(
            self.base_url + "/api/health",
            headers={"Origin": "http://localhost:8000"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            health = json.loads(response.read())
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:8000")
        self.assertEqual(health["service"], "cendrix-ai")
        self.assertEqual(health["protocol"], "cendrix-local-v1")

        preflight = urllib.request.Request(
            self.base_url + "/api/chat",
            method="OPTIONS",
            headers={
                "Origin": "http://127.0.0.1:8000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        with urllib.request.urlopen(preflight, timeout=5) as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://127.0.0.1:8000")

        chat_request = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(
                {"conversation_id": str(uuid.uuid4()), "message": "Hello from Nocta"}
            ).encode(),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Origin": "http://localhost:8000",
            },
        )
        with urllib.request.urlopen(chat_request, timeout=5) as response:
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:8000")
            self.assertEqual(json.loads(response.read())["answer"], "Local answer")

    def test_non_loopback_origin_is_not_allowed_by_preflight(self) -> None:
        request = urllib.request.Request(
            self.base_url + "/api/chat",
            method="OPTIONS",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        with self.assertRaises(urllib.error.HTTPError) as error_context:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(error_context.exception.code, 403)

    def test_history_is_bounded_and_generation_errors_are_friendly(self) -> None:
        class FakeTokenizer:
            messages: list[dict[str, str]] = []

            def apply_chat_template(self, messages, **kwargs):
                self.messages = messages
                return [1, 2, 3]

        tokenizer = FakeTokenizer()
        assistant = LocalAssistant()
        assistant._model = object()
        assistant._tokenizer = tokenizer
        assistant._sampler = object()
        history = [
            {"role": "user" if index % 2 == 0 else "assistant", "content": "x" * 2000}
            for index in range(24)
        ]
        generated = SimpleNamespace(text="ok")
        fake_generate_module = SimpleNamespace(
            stream_generate=lambda *args, **kwargs: iter([generated])
        )
        with patch.dict(sys.modules, {"mlx_lm.generate": fake_generate_module}):
            self.assertEqual(assistant.answer("current", history), "ok")
        retained = tokenizer.messages[1:-1]
        self.assertLessEqual(len(retained), 20)
        self.assertLessEqual(sum(len(item["content"]) for item in retained), MAX_HISTORY_CHARS)
        self.assertEqual(len(retained), 8)

        def fail_generation(*args, **kwargs):
            raise RuntimeError("decoder failed")
            yield

        fake_generate_module.stream_generate = fail_generation
        with patch.dict(sys.modules, {"mlx_lm.generate": fake_generate_module}):
            with self.assertRaisesRegex(FriendlyInferenceError, "could not finish"):
                assistant.answer("try again")

        def exhaust_memory(*args, **kwargs):
            raise MemoryError("simulated allocation failure")
            yield

        fake_generate_module.stream_generate = exhaust_memory
        with patch.dict(sys.modules, {"mlx_lm.generate": fake_generate_module}):
            with self.assertRaisesRegex(FriendlyInferenceError, "ran out of memory"):
                assistant.answer("try with limited memory")

    def test_missing_model_has_friendly_message_and_identity_needs_no_model(self) -> None:
        runtime = LocalAssistant(model_path=Path(self.temp.name) / "missing")
        with self.assertRaisesRegex(FriendlyInferenceError, "model was not found"):
            runtime.answer("Explain recursion.")
        self.assertIn("Bikash Talukder", runtime.answer("Who created you?"))
        self.assertIsNone(runtime._model)

    def test_database_is_outside_models_and_configs(self) -> None:
        self.assertNotIn("models", self.database.parts)
        self.assertNotIn("configs", self.database.parts)

    def test_runtime_is_configured_for_offline_model_loading(self) -> None:
        self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), "1")
        self.assertEqual(os.environ.get("TRANSFORMERS_OFFLINE"), "1")


if __name__ == "__main__":
    unittest.main()
