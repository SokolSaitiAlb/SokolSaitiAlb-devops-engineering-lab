"""Small, dependency-free HTTP service for the DevOps engineering lab."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import uuid
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

MAX_BODY_BYTES = 16_384
MAX_NOTE_LENGTH = 500
SERVICE_NAME = "ops-notes-api"


class StoreError(RuntimeError):
    """Raised when the persisted notes file cannot be safely read or written."""


class NotesStore:
    """A single-process, JSON-file-backed store with atomic file replacement."""

    def __init__(self, data_file: str | Path) -> None:
        self.path = Path(data_file)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_unlocked([])
        self._read_unlocked()

    def list_notes(self) -> list[dict[str, str]]:
        with self._lock:
            return self._read_unlocked()

    def add_note(self, text: str) -> dict[str, str]:
        note = {
            "id": uuid.uuid4().hex,
            "text": text,
            "created_at": datetime.now(UTC).isoformat(),
        }
        with self._lock:
            notes = self._read_unlocked()
            notes.append(note)
            self._write_unlocked(notes)
        return note

    def is_ready(self) -> bool:
        """Check whether the data file and parent can support reads and atomic writes."""
        return (
            self.path.is_file()
            and os.access(self.path, os.R_OK)
            and os.access(self.path.parent, os.W_OK | os.X_OK)
        )

    def _read_unlocked(self) -> list[dict[str, str]]:
        try:
            with self.path.open(encoding="utf-8") as handle:
                data: Any = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StoreError("The notes data file could not be read") from exc
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise StoreError("The notes data file has an invalid format")
        return data

    def _write_unlocked(self, notes: list[dict[str, str]]) -> None:
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_name = handle.name
                json.dump(notes, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        except OSError as exc:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name)
                except OSError:
                    logging.warning(
                        "Could not remove temporary data file %s",
                        temporary_name,
                        exc_info=True,
                    )
            raise StoreError("The notes data file could not be written") from exc


class ServiceHTTPServer(ThreadingHTTPServer):
    """HTTP server carrying the store and application version for its handler."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        store: NotesStore,
        app_version: str,
    ) -> None:
        self.store = store
        self.app_version = app_version
        super().__init__(address, ServiceRequestHandler)


class ServiceRequestHandler(BaseHTTPRequestHandler):
    """JSON API with bounded request bodies and structured errors."""

    server_version = "OpsNotesAPI"
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlsplit(self.path).path
        if path == "/healthz":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/readyz":
            if self.server.store.is_ready():  # type: ignore[attr-defined]
                self._send_json(HTTPStatus.OK, {"status": "ready"})
            else:
                self._send_json(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"status": "not_ready", "reason": "storage_unavailable"},
                )
            return
        if path == "/":
            self._send_json(
                HTTPStatus.OK,
                {
                    "service": SERVICE_NAME,
                    "version": self.server.app_version,  # type: ignore[attr-defined]
                    "status": "ok",
                    "endpoints": ["/healthz", "/readyz", "/api/notes"],
                },
            )
            return
        if path == "/api/notes":
            try:
                self._send_json(
                    HTTPStatus.OK,
                    {"items": self.server.store.list_notes()},  # type: ignore[attr-defined]
                )
            except StoreError:
                logging.exception("Unable to read notes store")
                self._send_json(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "storage_unavailable"},
                )
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = urlsplit(self.path).path
        if path != "/api/notes":
            status = (
                HTTPStatus.NOT_FOUND
                if path not in {"/", "/healthz", "/readyz"}
                else HTTPStatus.METHOD_NOT_ALLOWED
            )
            error = "method_not_allowed" if status == HTTPStatus.METHOD_NOT_ALLOWED else "not_found"
            self._send_json(status, {"error": error})
            return

        content_type = (
            self.headers.get("Content-Type", "").split(";", maxsplit=1)[0].strip().lower()
        )
        if content_type != "application/json":
            self._send_json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "content_type_must_be_application_json"},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if content_length < 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if content_length > MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request_body_too_large"})
            return
        if content_length == 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "request_body_required"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "json_object_required"})
            return

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "text_required"})
            return
        text = text.strip()
        if len(text) > MAX_NOTE_LENGTH:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "text_too_long", "max_length": MAX_NOTE_LENGTH},
            )
            return

        try:
            note = self.server.store.add_note(text)  # type: ignore[attr-defined]
        except StoreError:
            logging.exception("Unable to write notes store")
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "storage_unavailable"})
            return
        self._send_json(HTTPStatus.CREATED, note)

    def do_PUT(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "GET, POST")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = json.dumps({"error": "method_not_allowed"}).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        logging.info(
            "http_access client=%s message=%s",
            self.client_address[0],
            format_string % args,
        )


def build_server(
    host: str,
    port: int,
    data_file: str | Path,
    version: str,
) -> ServiceHTTPServer:
    if not 0 <= port <= 65535:
        raise ValueError("PORT must be between 0 and 65535")
    store = NotesStore(data_file)
    return ServiceHTTPServer((host, port), store, version)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError as exc:
        raise SystemExit("PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise SystemExit("PORT must be between 1 and 65535")
    data_file = os.getenv("DATA_FILE", "/data/notes.json")
    version = os.getenv("APP_VERSION", "0.1.0-dev")
    try:
        server = build_server(host, port, data_file, version)
    except (OSError, ValueError, StoreError) as exc:
        raise SystemExit(f"Unable to start {SERVICE_NAME}: {exc}") from exc
    logging.info(
        "service_start service=%s host=%s port=%d version=%s",
        SERVICE_NAME,
        host,
        port,
        version,
    )
    try:
        with server:
            server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        logging.info("service_shutdown signal=keyboard_interrupt")


if __name__ == "__main__":
    main()
