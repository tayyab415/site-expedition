#!/usr/bin/env python3
"""Iteration 7 — photorealistic 3D eyes + Earth Engine witnesses.

Google Map Tiles are proxied so the API key never sits in the HTML.
EE overlays are signed mapids (public catalog). Packets are on disk.
"""
from __future__ import annotations

import json
import mimetypes
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EXHIBITS = ROOT / "exhibits"
PORT = 8027
EE_PROJECT = "gen-lang-client-0261050164"
GOOGLE_TILES = "https://tile.googleapis.com"
ENV_FILE = Path.home() / ".config" / "mireye-challenge-maps.env"

SITES = {
    "san_leon": {
        "id": "san_leon",
        "name": "San Leon, TX (Galveston Bay shore)",
        "label": "San Leon — bay shore",
        "lat": 29.475732,
        "lng": -94.966533,
        "verdict": "KILL",
        "one_liner": "You're buying 2021 dirt at a 1995 feeling.",
        "letter_file": "kill_letter.md",
        "camera": {"heading": 78, "pitch": -28, "range": 560, "height": 12},
    },
    "keep_control": {
        "id": "keep_control",
        "name": "3605 Winfield Cove, Austin TX",
        "label": "Winfield Cove — inland",
        "lat": 30.2363775,
        "lng": -97.7807633,
        "verdict": "KEEP",
        "one_liner": "No material contradiction.",
        "letter_file": "advisory.md",
        "camera": {"heading": 205, "pitch": -32, "range": 280, "height": 18},
    },
}

_ee_lock = threading.Lock()
_ee_layers: dict | None = None
_ee_error: str | None = None
_sat_session: dict | None = None


def maps_key() -> str:
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        return os.environ["GOOGLE_MAPS_API_KEY"].strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def exhibit_manifest() -> dict:
    path = EXHIBITS / "manifest.json"
    if path.exists():
        return load_json(path)
    return {"sites": {}}


def build_vet(site_id: str) -> dict:
    meta = SITES[site_id]
    site_dir = DATA / site_id
    return {
        "site": meta,
        "verdict": load_json(site_dir / "verdict.json"),
        "evidence": load_json(site_dir / "evidence.json"),
        "letter": (site_dir / meta["letter_file"]).read_text(encoding="utf-8"),
        "timeline_url": f"/data/{site_id}/water_timeline.svg",
        "exhibits": exhibit_manifest().get("sites", {}).get(site_id, {}),
    }


def _map_url(image, vis: dict) -> str:
    mid = image.visualize(**vis).getMapId()
    return mid["tile_fetcher"].url_format


def compute_ee_layers() -> dict:
    import ee

    ee.Initialize(project=EE_PROJECT)
    # Both demo pins sit in this window (Austin + Galveston Bay).
    frame = ee.Geometry.Rectangle([-98.4, 28.7, -94.3, 30.8])
    occ = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0).clip(frame)
    naip = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterBounds(frame)
        .filterDate("2021-01-01", "2023-01-01")
        .select(["R", "G", "B"])
        .mosaic()
        .clip(frame)
    )
    fab = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().clip(frame)
    col = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterBounds(frame)
    a = col.filterDate("2017-01-01", "2018-01-01").mosaic()
    b = col.filterDate("2024-01-01", "2025-01-01").mosaic()
    change = ee.Image(1).subtract(a.multiply(b).reduce(ee.Reducer.sum())).rename("change").clip(frame)

    return {
        "water": {
            "url": _map_url(occ, {"min": 0, "max": 60, "palette": ["000000", "1b4f72", "5dade2", "f4d03f", "e74c3c"]}),
            "credit": "JRC Global Surface Water occurrence · Earth Engine",
            "note": "How often this pixel was water, 1984–2021. The TIME witness.",
        },
        "naip": {
            "url": _map_url(naip, {"min": 0, "max": 255}),
            "credit": "USDA NAIP 2021–22 · Earth Engine",
            "note": "Public 1 m aerial. Texas vintage ends 2022 — print the date.",
        },
        "height": {
            "url": _map_url(
                fab,
                {
                    "min": 0,
                    "max": 10,
                    "palette": ["08306b", "2171b5", "6baed6", "ffffcc", "fd8d3c", "b10026"],
                },
            ),
            "credit": "FABDEM bare-earth · Earth Engine",
            "note": "0–10 m stretch. Marsh sits in the blue. Austin (205 m) saturates — high ground.",
        },
        "change": {
            "url": _map_url(change, {"min": 0, "max": 0.25, "palette": ["00000000", "2ecc71", "f4d03f", "e74c3c"]}),
            "credit": "Google Satellite Embedding V1 2017→2024 · Earth Engine",
            "note": "1 − cosine of 64-d annual fingerprints. Hot = the land itself changed.",
        },
    }


def get_ee_layers() -> tuple[dict | None, str | None]:
    global _ee_layers, _ee_error
    with _ee_lock:
        if _ee_layers is not None or _ee_error is not None:
            return _ee_layers, _ee_error
        try:
            print("computing EE overlay mapids…", flush=True)
            _ee_layers = compute_ee_layers()
            print("EE overlays ready", flush=True)
        except Exception as exc:  # noqa: BLE001
            _ee_error = str(exc)
            print("EE overlays failed:", exc, flush=True)
        return _ee_layers, _ee_error


def satellite_session() -> str | None:
    global _sat_session
    key = maps_key()
    if not key:
        return None
    if _sat_session and _sat_session.get("session"):
        return _sat_session["session"]
    body = json.dumps({"mapType": "satellite", "language": "en-US", "region": "US"}).encode()
    req = urllib.request.Request(
        f"{GOOGLE_TILES}/v1/createSession?key={urllib.parse.quote(key)}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        _sat_session = json.loads(resp.read())
    return _sat_session.get("session")


def proxy_google(path: str, query: str) -> tuple[int, bytes, str]:
    key = maps_key()
    if not key:
        return 503, b'{"error":"GOOGLE_MAPS_API_KEY missing"}', "application/json"
    params = parse_qs(query, keep_blank_values=True)
    params.pop("key", None)
    flat = {k: v[-1] for k, v in params.items()}
    flat["key"] = key
    url = f"{GOOGLE_TILES}{path}?{urllib.parse.urlencode(flat)}"
    req = urllib.request.Request(url, headers={"User-Agent": "mireye-challenge-iter7"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
            ctype = resp.headers.get("Content-Type") or "application/octet-stream"
            return 200, payload, ctype
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type") or "application/json"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        if "/v1/3dtiles/" in self.path or "/g2d/" in self.path:
            return
        print(f"[{self.log_date_time_string()}] {fmt % args}", flush=True)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: object) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

    def _file(self, path: Path) -> None:
        if not path.is_file():
            self._json(404, {"error": "not found", "path": str(path.name)})
            return
        mime, _ = mimetypes.guess_type(str(path))
        self._send(200, path.read_bytes(), mime or "application/octet-stream")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query

        if path.startswith("/v1/3dtiles"):
            status, body, ctype = proxy_google(path, query)
            self._send(status, body, ctype)
            return

        if path.startswith("/g2d/"):
            parts = path.strip("/").split("/")
            if len(parts) != 4:
                self._json(400, {"error": "expected /g2d/z/x/y"})
                return
            _, z, x, y = parts
            session = satellite_session()
            if not session:
                self._json(503, {"error": "no satellite session"})
                return
            status, body, ctype = proxy_google(
                f"/v1/2dtiles/{z}/{x}/{y}",
                urllib.parse.urlencode({"session": session}),
            )
            self._send(status, body, ctype)
            return

        if path == "/api/config":
            layers, err = get_ee_layers()
            self._json(
                200,
                {
                    "has_google_tiles": bool(maps_key()),
                    "tileset": "/v1/3dtiles/root.json",
                    "satellite": "/g2d/{z}/{x}/{y}",
                    "sites": SITES,
                    "ee_layers": layers,
                    "ee_error": err,
                    "aerial_view": {
                        "san_leon": None,
                        "keep_control": None,
                        "note": "Aerial View 404 at both pins (no pre-rendered orbit). Photorealistic 3D tiles are the Google eye. Downtown Austin (500 W 2nd) has an ACTIVE 40s orbit — not this house.",
                    },
                },
            )
            return

        if path == "/api/sites":
            self._json(200, {"sites": list(SITES.values())})
            return

        if path == "/api/vet":
            site_id = (parse_qs(query).get("site") or [""])[0]
            if site_id not in SITES:
                self._json(400, {"error": "site must be san_leon or keep_control"})
                return
            self._json(200, build_vet(site_id))
            return

        if path in ("/", "/index.html"):
            self._file(ROOT / "index.html")
            return

        rel = path.lstrip("/")
        candidate = (ROOT / rel).resolve()
        if str(candidate).startswith(str(ROOT.resolve())) and candidate.is_file():
            self._file(candidate)
            return

        self._json(404, {"error": "not found"})


def main() -> None:
    if not maps_key():
        print("WARN: no GOOGLE_MAPS_API_KEY — 3D tiles will 503", flush=True)
    threading.Thread(target=get_ee_layers, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"iteration-7 eyes  http://0.0.0.0:{PORT}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
