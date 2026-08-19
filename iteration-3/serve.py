#!/usr/bin/env python3
"""Serve the harness trace UI and GET /api/trace?site=..."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent
UI = ROOT / "ui"
TRACE = ROOT / "trace"
SITES = ("san_leon", "keep_control")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj):
        self._send(code, json.dumps(obj, indent=2).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/trace":
            qs = parse_qs(parsed.query)
            site = (qs.get("site") or [""])[0]
            if site not in SITES:
                self._json(400, {"error": "site required", "choices": list(SITES)})
                return
            trace_file = TRACE / f"{site}.json"
            if not trace_file.exists():
                self._json(404, {"error": f"no trace for {site}", "hint": "run: python3 runner.py --all"})
                return
            self._json(200, json.loads(trace_file.read_text()))
            return

        if path == "/api/sites":
            self._json(200, {"sites": list(SITES)})
            return

        if path in ("/", "/index.html"):
            return self._file(UI / "index.html")

        rel = path.lstrip("/")
        candidate = UI / rel
        if candidate.is_file():
            return self._file(candidate)

        self._json(404, {"error": "not found", "path": path})

    def _file(self, path: Path):
        if not path.is_file():
            self._json(404, {"error": "missing", "path": str(path)})
            return
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), ctype)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port", nargs="?", type=int, default=8023)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()

    if not (TRACE / "san_leon.json").exists():
        print("trace/ missing — run: python3 runner.py --all")
        import subprocess
        subprocess.run(["python3", str(ROOT / "runner.py"), "--all"], check=True)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"harness trace UI  http://{args.host}:{args.port}/")
    print("API  GET /api/trace?site=san_leon|keep_control")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
