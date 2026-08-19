#!/usr/bin/env python3
"""Serve analyst workbook UI + /api/intel on port 8025 (stdlib only)."""

from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "ui"
OUT = ROOT / "out"
DATA = ROOT / "data"
PORT = 8025


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_intel(self, slug: str) -> dict | None:
        path = OUT / f"{slug}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"

        if route == "/api/sites":
            sites = []
            for slug in sorted(p.stem for p in OUT.glob("*.json")):
                intel = self._read_intel(slug)
                if intel:
                    sites.append({
                        "slug": slug,
                        "name": intel["site"]["name"],
                        "verdict": intel["ruling"]["verdict"],
                    })
            self._send_json({"sites": sites})
            return

        if route == "/api/intel":
            qs = parse_qs(parsed.query)
            slug = (qs.get("site") or [""])[0]
            if not slug:
                self._send_json({"error": "missing ?site="}, status=400)
                return
            intel = self._read_intel(slug)
            if intel is None:
                self._send_json({"error": f"unknown site: {slug}"}, status=404)
                return
            timeline_path = DATA / slug / "water_timeline.svg"
            if timeline_path.exists():
                intel = dict(intel)
                intel["water_timeline_svg"] = timeline_path.read_text()
            self._send_json(intel)
            return

        if route == "/":
            route = "/index.html"

        file_path = (UI / route.lstrip("/")).resolve()
        if not str(file_path).startswith(str(UI.resolve())):
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self._send_bytes(file_path.read_bytes(), content_type)


def main() -> None:
    if not OUT.exists() or not any(OUT.glob("*.json")):
        print("No intel output found — run: python intel/run.py", file=sys.stderr)
        sys.exit(1)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Layer 2 workbook: http://0.0.0.0:{PORT}/")
    print(f"API: http://0.0.0.0:{PORT}/api/intel?site=san_leon")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
