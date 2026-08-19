#!/usr/bin/env python3
"""Property vetting agent — courtroom exhibit server (iteration 2)."""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"
PORT = 8022

SITES = {
    "san_leon": {
        "id": "san_leon",
        "name": "San Leon, TX (Galveston Bay shore)",
        "label": "San Leon — coastal pin",
        "lat": 29.475732,
        "lng": -94.966533,
        "letter_file": "kill_letter.md",
    },
    "keep_control": {
        "id": "keep_control",
        "name": "3605 Winfield Cove, Austin TX",
        "label": "Winfield Cove — inland control",
        "lat": 30.2363775,
        "lng": -97.7807633,
        "letter_file": "advisory.md",
    },
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_text(path: Path) -> str:
    with path.open(encoding="utf-8") as fh:
        return fh.read()


def build_vet_packet(site_id: str) -> dict:
    meta = SITES[site_id]
    site_dir = DATA / site_id
    verdict = load_json(site_dir / "verdict.json")
    evidence = load_json(site_dir / "evidence.json")
    letter_path = site_dir / meta["letter_file"]
    letter = load_text(letter_path) if letter_path.exists() else ""

    return {
        "site_id": site_id,
        "site": meta,
        "verdict": verdict,
        "evidence": evidence,
        "letter": letter,
        "timeline_url": f"/api/timeline?site={site_id}",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _file(self, path: Path) -> None:
        if not path.is_file():
            self._json(404, {"error": "not found"})
            return
        mime, _ = mimetypes.guess_type(str(path))
        body = path.read_bytes()
        self._send(200, body, mime or "application/octet-stream")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/sites":
            sites = [
                {
                    "id": meta["id"],
                    "name": meta["name"],
                    "label": meta["label"],
                    "lat": meta["lat"],
                    "lng": meta["lng"],
                }
                for meta in SITES.values()
            ]
            self._json(200, {"sites": sites})
            return

        if path == "/api/vet":
            site_id = (query.get("site") or [""])[0]
            if site_id not in SITES:
                self._json(400, {"error": "site must be san_leon or keep_control"})
                return
            self._json(200, build_vet_packet(site_id))
            return

        if path == "/api/timeline":
            site_id = (query.get("site") or [""])[0]
            if site_id not in SITES:
                self._json(400, {"error": "site must be san_leon or keep_control"})
                return
            svg_path = DATA / site_id / "water_timeline.svg"
            self._file(svg_path)
            return

        if path in ("/", "/index.html"):
            self._file(STATIC / "index.html")
            return

        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            self._file(STATIC / rel)
            return

        self._json(404, {"error": "not found"})


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Courtroom exhibit running at http://127.0.0.1:{PORT}")
    print("  GET /api/sites")
    print("  GET /api/vet?site=san_leon|keep_control")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
