"""Planning board + probe harness. Keys stay on the server."""

from __future__ import annotations

import json
import os
import secrets
import socket
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
if str(PKG.parent) not in sys.path:
    sys.path.insert(0, str(PKG.parent))

from expedition.security import (  # noqa: E402
    BrowserSessionGate,
    InvalidRequestBody,
    OptionalBearerTokenGate,
    PerIpRateLimiter,
    RequestBodyTooLarge,
    SecurityHeadersMixin,
    client_ip,
    read_limited_body,
    request_origin_allowed,
    request_scheme,
)

PORT = 8030
GOOGLE_TILES = "https://tile.googleapis.com"
ENV_FILE = Path.home() / ".config" / "mireye-challenge-maps.env"
MISSION_SITES = json.loads((PKG / "data" / "mission_sites.json").read_text())
CANDIDATES = json.loads((PKG / "data" / "candidates.json").read_text())
_sat_session: dict | None = None
AUTH = BrowserSessionGate(OptionalBearerTokenGate.from_env())
API_LIMITER = PerIpRateLimiter(limit=180, window_seconds=60)
TILE_LIMITER = PerIpRateLimiter(limit=3000, window_seconds=60)
TRUST_PROXY = os.environ.get("EXPEDITION_TRUST_PROXY", "").strip().lower() in {
    "1", "true", "yes", "on"
}


def maps_key() -> str:
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        return os.environ["GOOGLE_MAPS_API_KEY"].strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("GOOGLE_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


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
    req = urllib.request.Request(url, headers={"User-Agent": "mireye-expedition-board"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
            ctype = resp.headers.get("Content-Type") or "application/octet-stream"
            return 200, payload, ctype
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type") or "application/json"


class Handler(SecurityHeadersMixin, BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        if "/v1/3dtiles/" in self.path or "/g2d/" in self.path or self.path.startswith("/sv"):
            return
        sys.stderr.write("ui: " + (fmt % args) + "\n")

    def _send(self, code: int, body: bytes, ctype: str, headers: dict[str, str] | None = None) -> None:
        self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def parse_request(self) -> bool:
        ok = super().parse_request()
        if ok:
            self.close_connection = True
            path = self.path or ""
            # Keep a finite timeout. Clearing it lets Cesium tile keep-alives
            # hold every worker slot until the board stops answering.
            timeout = 20.0 if ("/v1/3dtiles/" in path or "/g2d/" in path or path.startswith("/sv")) else 90.0
            try:
                self.connection.settimeout(timeout)
            except OSError:
                pass
        return ok

    def _json(
        self,
        code: int,
        payload: object,
        headers: dict[str, str] | None = None,
    ) -> None:
        try:
            body = json.dumps(payload, default=str, allow_nan=False).encode()
        except (TypeError, ValueError):
            code = 500
            body = b'{"error":"invalid_response","message":"response contained a non-finite or unsupported value"}'
        self._send(code, body, "application/json", headers)

    def _begin_ndjson(self) -> None:
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _ndjson(self, payload: object) -> None:
        line = json.dumps(payload, default=str, allow_nan=False).encode() + b"\n"
        self.wfile.write(line)
        self.wfile.flush()

    def _api_error(self, code: int, error: str, message: str) -> None:
        self._json(code, {"error": error, "message": message})

    def _guard(self, path: str, *, require_auth: bool = True) -> bool:
        protected = (
            path.startswith("/api/")
            or path.startswith("/v1/3dtiles")
            or path.startswith("/g2d/")
            or path.startswith("/sv")
        )
        if not protected:
            return True
        if not request_origin_allowed(
            self.headers,
            request_scheme=request_scheme(self.headers, trust_proxy=TRUST_PROXY),
        ):
            self._json(403, {"error": "cross-origin request rejected"})
            return False
        if require_auth and not AUTH.allows(self.headers):
            self._send(401, b'{"error":"authentication required"}', "application/json", AUTH.challenge_headers())
            return False
        limiter = TILE_LIMITER if path.startswith(("/v1/3dtiles", "/g2d/", "/sv")) else API_LIMITER
        decision = limiter.check(client_ip(self))
        if not decision.allowed:
            self._send(429, b'{"error":"rate limit exceeded"}', "application/json", {"Retry-After": str(decision.retry_after)})
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        session_status = path == "/api/session"
        if not self._guard(path, require_auth=not session_status):
            return
        files = {
            "/": (ROOT / "index.html", "text/html; charset=utf-8"),
            "/index.html": (ROOT / "index.html", "text/html; charset=utf-8"),
            "/app.js": (ROOT / "app.js", "text/javascript"),
            "/styles.css": (ROOT / "styles.css", "text/css"),
            "/variants.css": (ROOT / "variants.css", "text/css"),
            "/fonts.css": (ROOT / "fonts.css", "text/css"),
            "/looks": (ROOT / "looks.html", "text/html; charset=utf-8"),
            "/looks.html": (ROOT / "looks.html", "text/html; charset=utf-8"),
            "/probe": (ROOT / "probe.html", "text/html; charset=utf-8"),
            "/probe.html": (ROOT / "probe.html", "text/html; charset=utf-8"),
            "/probe.js": (ROOT / "probe.js", "text/javascript"),
            "/probe.css": (ROOT / "probe.css", "text/css"),
            "/recordings": (ROOT / "recordings.html", "text/html; charset=utf-8"),
            "/recordings.html": (ROOT / "recordings.html", "text/html; charset=utf-8"),
            "/verify": (ROOT / "verify.html", "text/html; charset=utf-8"),
            "/verify.html": (ROOT / "verify.html", "text/html; charset=utf-8"),
        }
        if path in files:
            file, ctype = files[path]
            self._send(200, file.read_bytes(), ctype)
            return
        if path.startswith("/fonts/"):
            name = path.rsplit("/", 1)[-1]
            fonts = {
                "Clash_Regular.ttf": "font/ttf",
                "Clash_Bold.ttf": "font/ttf",
            }
            target = ROOT / "fonts" / name
            if name != target.name or name not in fonts or not target.is_file():
                self._json(404, {"error": "not found"})
                return
            self._send(200, target.read_bytes(), fonts[name])
            return
        recordings = PKG / "var" / "flow-recordings"
        recording_files = {
            "/recordings/after.mp4": (recordings / "after" / "warehouse-user-flow.mp4", "video/mp4"),
            "/recordings/before.mp4": (recordings / "warehouse-user-flow.mp4", "video/mp4"),
        }
        if path in recording_files:
            file, ctype = recording_files[path]
            if not file.is_file():
                self._json(404, {"error": "recording missing"})
                return
            self._send(200, file.read_bytes(), ctype)
            return
        if path.startswith("/recordings/stills/"):
            name = path.rsplit("/", 1)[-1]
            still = recordings / "after" / "stills" / name
            if name != still.name or ".." in name or not still.is_file() or still.suffix != ".png":
                self._json(404, {"error": "not found"})
                return
            self._send(200, still.read_bytes(), "image/png")
            return
        if path.startswith("/verify/clips/") or path.startswith("/verify/stills/"):
            name = path.rsplit("/", 1)[-1]
            folder = recordings / "verify" / ("clips" if "/clips/" in path else "stills")
            allowed = {".mp4": "video/mp4", ".png": "image/png"}
            target = folder / name
            if name != target.name or ".." in name or target.suffix not in allowed or not target.is_file():
                self._json(404, {"error": "not found"})
                return
            self._send(200, target.read_bytes(), allowed[target.suffix])
            return
        if path.startswith("/looks/clips/") or path.startswith("/looks/stills/"):
            name = path.rsplit("/", 1)[-1]
            folder = recordings / "looks" / ("clips" if "/clips/" in path else "stills")
            allowed = {".mp4": "video/mp4", ".png": "image/png"}
            target = folder / name
            if name != target.name or ".." in name or target.suffix not in allowed or not target.is_file():
                self._json(404, {"error": "not found"})
                return
            self._send(200, target.read_bytes(), allowed[target.suffix])
            return
        if path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        if path == "/api/session":
            self._json(200, {"authenticated": AUTH.allows(self.headers)})
            return
        if path == "/api/candidates":
            self._json(200, CANDIDATES)
            return
        if path == "/api/mission-sites":
            self._json(200, MISSION_SITES)
            return
        if path == "/api/custom-manifests":
            from expedition.manifests import list_reviewed_manifests

            self._json(200, {"manifests": list_reviewed_manifests()})
            return
        if path == "/api/credits":
            from expedition.credits import snapshot

            self._json(200, snapshot())
            return
        if path == "/api/aerial-play":
            from expedition.adapters.aerial import lookup_playback, playback_uri

            video_id = (parse_qs(urlparse(self.path).query).get("video_id") or [""])[0]
            if not video_id or len(video_id) > 256 or not all(
                c.isalnum() or c in "-_" for c in video_id
            ):
                self._json(400, {"error": "invalid video id"})
                return
            try:
                playback = lookup_playback(video_id, maps_key())
                uri = playback_uri(playback)
                if not uri:
                    self._json(502, {"error": "Aerial playback URI unavailable"})
                    return
                # Signed playback is returned ephemerally and never written to disk.
                self._json(200, {"video_id": video_id, "uri": uri})
            except urllib.error.HTTPError as exc:
                self._json(exc.code, {"error": "Aerial playback unavailable"})
            except Exception:
                self._json(502, {"error": "Aerial playback unavailable"})
            return
        if path == "/api/aerial-meta":
            from expedition.adapters.aerial import lookup_metadata

            query = (parse_qs(urlparse(self.path).query).get("query") or [""])[0].strip()
            if not query or len(query) > 200:
                self._json(400, {"error": "address query required"})
                return
            key = maps_key()
            if not key:
                self._json(503, {"error": "aerial lookup unavailable"})
                return
            try:
                raw = lookup_metadata(query, key)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    self._json(200, {"state": "NOT_FOUND", "video_id": None, "query": query})
                    return
                self._json(exc.code, {"error": "aerial lookup unavailable"})
                return
            except Exception:
                self._json(502, {"error": "aerial lookup unavailable"})
                return
            state = str(raw.get("state") or "").upper()
            self._json(
                200,
                {
                    "state": state,
                    "video_id": raw.get("videoId") if state == "ACTIVE" else None,
                    "duration": raw.get("duration"),
                    "capture_date": raw.get("captureDate"),
                    "query": query,
                },
            )
            return
        if path == "/api/street-meta":
            from expedition.adapters.streetview import street_meta

            query = parse_qs(urlparse(self.path).query)
            try:
                lat = float((query.get("lat") or [""])[0])
                lng = float((query.get("lng") or [""])[0])
            except (TypeError, ValueError):
                self._json(400, {"error": "lat and lng required"})
                return
            if not (18 <= lat <= 72 and -180 <= lng <= -65):
                self._json(400, {"error": "point is outside the US envelope"})
                return
            self._json(200, street_meta(lat, lng))
            return
        if path == "/sv":
            from expedition.adapters.streetview import lookup_image

            query = parse_qs(urlparse(self.path).query)
            try:
                lat = float((query.get("lat") or [""])[0])
                lng = float((query.get("lng") or [""])[0])
                heading = float((query.get("heading") or ["70"])[0])
            except (TypeError, ValueError):
                self._json(400, {"error": "lat, lng, heading required"})
                return
            if not (18 <= lat <= 72 and -180 <= lng <= -65):
                self._json(400, {"error": "point is outside the US envelope"})
                return
            key = maps_key()
            if not key:
                self._json(503, {"error": "street view unavailable"})
                return
            try:
                body = lookup_image(lat, lng, heading, key)
            except urllib.error.HTTPError as exc:
                self._json(exc.code, {"error": "street view unavailable"})
                return
            except Exception:
                self._json(502, {"error": "street view unavailable"})
                return
            self._send(200, body, "image/jpeg")
            return
        if path == "/api/config":
            from expedition.concept import run_concept_test

            concept = run_concept_test()
            self._json(
                200,
                {
                    "has_google_tiles": bool(maps_key()),
                    "tileset": "/v1/3dtiles/root.json",
                    "satellite": "/g2d/{z}/{x}/{y}",
                    "warehouse_gltf": "/assets/warehouse.gltf",
                    "concept": concept,
                    "note": "Google tiles are presentation only. They do not score.",
                },
            )
            return
        if path == "/api/concept-test":
            from expedition.concept import run_concept_test

            self._json(200, run_concept_test())
            return
        if path == "/assets/warehouse.gltf":
            self._send(200, (PKG / "assets" / "warehouse.gltf").read_bytes(), "model/gltf+json")
            return
        if path.startswith("/v1/3dtiles"):
            status, body, ctype = proxy_google(path, urlparse(self.path).query)
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
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        session_exchange = path == "/api/session"
        if not self._guard(path, require_auth=not session_exchange):
            return
        try:
            raw = read_limited_body(self) or b"{}"
        except RequestBodyTooLarge as exc:
            self._json(413, {"error": str(exc)})
            return
        except InvalidRequestBody as exc:
            self._json(400, {"error": str(exc)})
            return
        try:
            payload = json.loads(
                raw.decode() or "{}",
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-finite JSON number {value}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._api_error(400, "invalid_request", "request body must be finite JSON")
            return
        if not isinstance(payload, dict):
            self._api_error(400, "invalid_request", "request body must be a JSON object")
            return
        if path == "/api/session":
            token = payload.get("token")
            issue = getattr(AUTH, "issue", None)
            session_id = issue(token) if callable(issue) and isinstance(token, str) else None
            if not session_id:
                self._send(
                    401,
                    b'{"error":"authentication_failed","message":"invalid access token"}',
                    "application/json",
                    AUTH.challenge_headers(),
                )
                return
            scheme = request_scheme(self.headers, trust_proxy=TRUST_PROXY)
            self._json(
                200,
                {"status": "authenticated"},
                {"Set-Cookie": AUTH.cookie_header(session_id, secure=scheme == "https")},
            )
            return
        if path == "/api/plan":
            from expedition.plan import compile_plan

            try:
                plan = compile_plan(
                    payload.get("mission") or "warehouse",
                    scan_budget=payload.get("scan_budget") or "standard",
                    site_form=payload.get("site_form") or "either",
                    flood_intolerant=payload.get("flood_intolerant"),
                    require_cultivated=payload.get("require_cultivated"),
                    route_anchors=payload.get("route_anchors"),
                    manifest_id=payload.get("manifest_id"),
                    search_region=payload.get("search_region") or "texas_triangle",
                    geography_band=payload.get("geography_band") or "selected_region",
                    size_band=payload.get("size_band") or "flexible",
                    budget_band=payload.get("budget_band") or "flexible",
                    preferences=payload.get("preferences") or [],
                    optional_investigations=payload.get("optional_investigations") or [],
                    require_water_service=bool(payload.get("require_water_service")),
                    require_sewer_service=bool(payload.get("require_sewer_service")),
                    require_fiber_service=bool(payload.get("require_fiber_service")),
                )
            except ValueError as exc:
                self._api_error(400, "invalid_request", str(exc))
                return
            self._json(200, plan.to_dict())
            return
        if path == "/api/resolve-address":
            from expedition.adapters.mireye import resolve_address
            from expedition.credits import CreditCeiling, snapshot

            try:
                resolved, spent = resolve_address(
                    payload.get("address") or "",
                    live=bool(payload.get("live")),
                )
                if resolved.get("disposition") == "resolved":
                    match = next(
                        (
                            candidate
                            for candidate in CANDIDATES["candidates"]
                            if abs(candidate["lat"] - resolved["lat"]) <= 0.0002
                            and abs(candidate["lng"] - resolved["lng"]) <= 0.0002
                        ),
                        None,
                    )
                    if match:
                        resolved["geocode_lat"] = resolved["lat"]
                        resolved["geocode_lng"] = resolved["lng"]
                        resolved["lat"] = match["lat"]
                        resolved["lng"] = match["lng"]
                        resolved["candidate_id"] = match["id"]
                        resolved["pin_lock"] = "curated_locked_pin"
                    resolved["credits"] = {"spent": spent, "ledger": snapshot()}
                self._json(200, resolved)
            except FileNotFoundError as exc:
                self._json(409, {"error": "replay_cache_miss", "message": str(exc)})
            except CreditCeiling as exc:
                self._json(402, {"error": str(exc)})
            except Exception as exc:
                self._json(502, {"error": f"address resolve failed: {type(exc).__name__}"})
            return
        if path in {"/api/run", "/api/expedition", "/api/run-stream", "/api/expedition-stream"}:
            from expedition.candidates import CandidateError
            from expedition.credits import CreditCeiling
            from expedition.engine import run_mission, run_site
            from expedition.plan import MISSIONS

            streaming = path.endswith("-stream")
            single = path in {"/api/run", "/api/run-stream"}
            try:
                missing = [
                    field
                    for field in (("mission", "candidate_id") if single else ("mission",))
                    if not isinstance(payload.get(field), str)
                    or not str(payload.get(field)).strip()
                ]
                if missing:
                    raise ValueError(f"missing required field(s): {', '.join(missing)}")
                mission = str(payload["mission"]).replace(" ", "_").lower()
                if mission not in MISSIONS:
                    raise ValueError(f"unknown mission {mission}")
                controls = dict(payload.get("controls") or {})
                if payload.get("manifest_id") and not controls.get("manifest_id"):
                    controls["manifest_id"] = payload["manifest_id"]
                live = bool(payload.get("live"))
                review = bool(payload.get("review"))
                if streaming:
                    self._begin_ndjson()
                    try:
                        def on_progress(event):
                            self._ndjson(event)

                        if single:
                            packet = run_site(
                                mission,
                                payload["candidate_id"],
                                live=live,
                                review=review,
                                controls=controls,
                                candidate=payload.get("candidate"),
                                on_progress=on_progress,
                            )
                        else:
                            ids = MISSION_SITES.get(mission) or (
                                MISSION_SITES.get("warehouse", []) if mission == "custom" else []
                            )
                            packet = run_mission(
                                mission,
                                ids,
                                live=live,
                                review=review,
                                controls=controls,
                                on_progress=on_progress,
                            )
                        self._ndjson({"event": "packet", "packet": packet})
                    except CreditCeiling as exc:
                        self._ndjson({"event": "error", "error": "credit_ceiling", "message": str(exc)})
                    except FileNotFoundError as exc:
                        self._ndjson({"event": "error", "error": "replay_cache_miss", "message": str(exc)})
                    except CandidateError as exc:
                        self._ndjson({"event": "error", "error": "invalid_candidate", "message": str(exc)})
                    except Exception as exc:
                        self._ndjson({"event": "error", "error": "expedition_failed", "message": type(exc).__name__})
                    return
                if single:
                    packet = run_site(
                        mission,
                        payload["candidate_id"],
                        live=live,
                        review=review,
                        controls=controls,
                        candidate=payload.get("candidate"),
                    )
                    self._json(200, packet)
                    return
                ids = MISSION_SITES.get(mission) or (
                    MISSION_SITES.get("warehouse", []) if mission == "custom" else []
                )
                packet = run_mission(
                    mission,
                    ids,
                    live=live,
                    review=review,
                    controls=controls,
                )
                self._json(200, packet)
            except CreditCeiling as exc:
                self._api_error(402, "credit_ceiling", str(exc))
            except FileNotFoundError as exc:
                self._api_error(409, "replay_cache_miss", str(exc))
            except CandidateError as exc:
                self._api_error(400, "invalid_candidate", str(exc))
            except (KeyError, TypeError, ValueError) as exc:
                self._api_error(400, "invalid_request", str(exc))
            except Exception as exc:
                self._api_error(502, "expedition_failed", type(exc).__name__)
            return
        self._json(404, {"error": "not found"})


BUSY_JSON = b'{"error":"server_busy","message":"the board is busy; retry in a moment"}'


class BoundedThreadingHTTPServer(ThreadingHTTPServer):
    """Threaded prototype server with pre-header timeouts and hard bounds."""

    daemon_threads = True
    block_on_close = False
    request_queue_size = 128

    def __init__(
        self,
        server_address,
        handler_class,
        *,
        max_connections: int = 16,
        socket_timeout: float = 5.0,
        slot_wait_timeout: float | None = None,
    ) -> None:
        if max_connections <= 0:
            raise ValueError("max_connections must be positive")
        if socket_timeout <= 0:
            raise ValueError("socket_timeout must be positive")
        wait = socket_timeout if slot_wait_timeout is None else float(slot_wait_timeout)
        if wait <= 0:
            raise ValueError("slot_wait_timeout must be positive")
        self.max_connections = max_connections
        self.socket_timeout = float(socket_timeout)
        self.slot_wait_timeout = wait
        self._connection_slots = threading.BoundedSemaphore(max_connections)
        super().__init__(server_address, handler_class)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(self.socket_timeout)
        return request, address

    def process_request(self, request, client_address) -> None:
        # Apply bounded backpressure in the accept loop instead of dropping a
        # burst as soon as all worker slots are occupied.  The kernel listen
        # queue remains bounded, and the timeout prevents the accept loop from
        # waiting forever behind long-running clients.
        if not self._connection_slots.acquire(timeout=self.slot_wait_timeout):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Content-Length: " + str(len(BUSY_JSON)).encode() + b"\r\n"
                    b"Connection: close\r\n"
                    b"Cache-Control: no-store\r\n"
                    b"\r\n" + BUSY_JSON
                )
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._connection_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._connection_slots.release()


ACCESS_TOKEN_FILE = PKG / "var" / "access-token"
DISABLE_AUTH_ENV = "EXPEDITION_DISABLE_AUTH"


def configure_auth(token: str) -> None:
    global AUTH
    AUTH = BrowserSessionGate(OptionalBearerTokenGate(token))


def ensure_server_auth() -> bool:
    """Load or create a private deployment token; return whether it was created."""

    if os.environ.get(DISABLE_AUTH_ENV, "").strip().lower() in {
        "1", "true", "yes", "on"
    }:
        configure_auth("")
        return False
    if AUTH.enabled:
        return False
    token = os.environ.get("EXPEDITION_BEARER_TOKEN", "").strip()
    if token:
        configure_auth(token)
        return False
    created = False
    if ACCESS_TOKEN_FILE.exists():
        token = ACCESS_TOKEN_FILE.read_text().strip()
    else:
        ACCESS_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        token = secrets.token_urlsafe(32)
        try:
            descriptor = os.open(
                ACCESS_TOKEN_FILE,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w") as stream:
                stream.write(token + "\n")
            created = True
        except FileExistsError:
            token = ACCESS_TOKEN_FILE.read_text().strip()
    if not token:
        raise RuntimeError("Expedition access token is empty")
    configure_auth(token)
    return created


def main() -> None:
    created = ensure_server_auth()
    host = os.environ.get("EXPEDITION_BIND_HOST", "127.0.0.1").strip() or "127.0.0.1"
    max_connections = int(os.environ.get("EXPEDITION_MAX_CONNECTIONS", "128"))
    socket_timeout = float(os.environ.get("EXPEDITION_SOCKET_TIMEOUT", "5"))
    slot_wait_timeout = float(os.environ.get("EXPEDITION_SLOT_WAIT", "15"))
    httpd = BoundedThreadingHTTPServer(
        (host, PORT),
        Handler,
        max_connections=max_connections,
        socket_timeout=socket_timeout,
        slot_wait_timeout=slot_wait_timeout,
    )
    print(f"Site Expedition  http://{host}:{PORT}  probe /probe", flush=True)
    if not AUTH.enabled:
        print("WARNING: authentication disabled for testing", flush=True)
    if created:
        print(f"Access token created at {ACCESS_TOKEN_FILE}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
