"""Integration tests for the HTTP service using only the Python standard library."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from service import NotesStore, StoreError, build_server  # noqa: E402


class ServiceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data" / "notes.json"
        self.server = build_server("127.0.0.1", 0, self.data_file, "test-version")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def request(
        self,
        path: str,
        method: str = "GET",
        payload: object | None = None,
        content_type: str = "application/json",
    ) -> tuple[int, dict[str, object], dict[str, str]]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": content_type} if body is not None else {},
        )
        try:
            with urlopen(request, timeout=2) as response:
                result = json.loads(response.read())
                return response.status, result, dict(response.headers.items())
        except HTTPError as response:
            result = json.loads(response.read())
            return response.code, result, dict(response.headers.items())

    def test_root_returns_service_metadata(self) -> None:
        status, payload, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertEqual(payload["service"], "ops-notes-api")
        self.assertEqual(payload["version"], "test-version")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")

    def test_liveness_and_readiness_are_healthy(self) -> None:
        self.assertEqual(self.request("/healthz")[0], 200)
        self.assertEqual(self.request("/readyz")[0], 200)

    def test_create_note_and_read_it_back(self) -> None:
        status, note, _ = self.request(
            "/api/notes", method="POST", payload={"text": "restore drill"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(note["text"], "restore drill")
        self.assertTrue(note["id"])
        self.assertTrue(note["created_at"])
        status, collection, _ = self.request("/api/notes")
        self.assertEqual(status, 200)
        self.assertEqual(collection["items"], [note])

    def test_note_survives_store_reinitialization(self) -> None:
        self.request("/api/notes", method="POST", payload={"text": "persistent"})
        restored_store = NotesStore(self.data_file)
        self.assertEqual(restored_store.list_notes()[0]["text"], "persistent")

    def test_invalid_json_is_rejected(self) -> None:
        request = Request(
            self.base_url + "/api/notes",
            data=b"{not-json}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urlopen(request, timeout=2)
        except HTTPError as response:
            self.assertEqual(response.code, 400)
            self.assertEqual(json.loads(response.read())["error"], "invalid_json")
        else:
            self.fail("Expected invalid JSON to be rejected")

    def test_empty_text_is_rejected(self) -> None:
        status, payload, _ = self.request(
            "/api/notes", method="POST", payload={"text": "   "}
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "text_required")

    def test_oversized_body_is_rejected(self) -> None:
        connection = HTTPConnection(*self.server.server_address, timeout=2)
        connection.request(
            "POST",
            "/api/notes",
            body=b"x" * 16_385,
            headers={"Content-Type": "application/json", "Content-Length": "16385"},
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 413)
        connection.close()

    def test_unsupported_method_is_rejected(self) -> None:
        status, payload, headers = self.request(
            "/api/notes", method="PUT", payload={"text": "ignored"}
        )
        self.assertEqual(status, 405)
        self.assertEqual(payload["error"], "method_not_allowed")
        self.assertIn("GET", headers["Allow"])

    def test_unknown_route_is_not_found(self) -> None:
        status, payload, _ = self.request("/does-not-exist")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "not_found")

    def test_missing_content_type_is_rejected(self) -> None:
        request = Request(
            self.base_url + "/api/notes",
            data=b'{"text":"test"}',
            method="POST",
        )
        try:
            urlopen(request, timeout=2)
        except HTTPError as response:
            self.assertEqual(response.code, 415)
        else:
            self.fail("Expected missing Content-Type to be rejected")

    def test_store_reports_corrupt_json(self) -> None:
        self.data_file.write_text("{broken", encoding="utf-8")
        with self.assertRaises(StoreError):
            NotesStore(self.data_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
