"""Dependency-free Chromium smoke test for the Site Expedition board.

The runner launches an isolated headless Chromium profile, drives the checked-in
UI through the Chrome DevTools Protocol, and records real PNG artifacts.  It
intentionally uses the browser UI rather than calling the Python engine directly.

Usage from the repository root while the app server is running::

    python3 -m expedition.verify.browser_smoke

The deployment token is read from ``expedition/var/access-token`` and is never
printed or written to the report.  Pass ``--base-url`` to exercise a protected
HTTPS tunnel instead of the loopback server.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import json
import os
import secrets
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_FILE = ROOT / "var" / "access-token"
DEFAULT_OUTPUT_DIR = ROOT / "var" / "browser-smoke"


class BrowserSmokeError(RuntimeError):
    """Raised when a browser assertion or CDP command fails."""


class DevToolsConnection:
    """Tiny synchronous WebSocket client sufficient for Chrome DevTools."""

    def __init__(self, websocket_url: str) -> None:
        parsed = urllib.parse.urlsplit(websocket_url)
        if parsed.scheme != "ws" or not parsed.hostname:
            raise BrowserSmokeError(f"unsupported DevTools URL: {websocket_url}")
        self.socket = socket.create_connection(
            (parsed.hostname, parsed.port or 80), timeout=15
        )
        self.socket.settimeout(30)
        self._next_id = 0
        self.events: list[dict[str, Any]] = []
        key = base64.b64encode(os.urandom(16)).decode()
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        request = (
            f"GET {target} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port or 80}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode()
        self.socket.sendall(request)
        response = self._receive_headers()
        if not response.startswith(b"HTTP/1.1 101"):
            raise BrowserSmokeError(
                "DevTools WebSocket upgrade failed: "
                + response.split(b"\r\n", 1)[0].decode(errors="replace")
            )
        expected = base64.b64encode(
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
            ).digest()
        ).decode()
        if f"sec-websocket-accept: {expected}".lower() not in response.decode().lower():
            raise BrowserSmokeError("DevTools WebSocket accept key did not match")

    def _receive_headers(self) -> bytes:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            block = self.socket.recv(4096)
            if not block:
                break
            data.extend(block)
            if len(data) > 64 * 1024:
                raise BrowserSmokeError("oversized WebSocket handshake")
        return bytes(data)

    @staticmethod
    def _masked_frame(payload: bytes, opcode: int = 1) -> bytes:
        mask = secrets.token_bytes(4)
        length = len(payload)
        if length < 126:
            prefix = struct.pack("!BB", 0x80 | opcode, 0x80 | length)
        elif length <= 0xFFFF:
            prefix = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, length)
        else:
            prefix = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, length)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return prefix + mask + masked

    def _read_exactly(self, size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            block = self.socket.recv(size - len(data))
            if not block:
                raise BrowserSmokeError("DevTools WebSocket closed unexpectedly")
            data.extend(block)
        return bytes(data)

    def _receive_frame(self) -> tuple[int, bytes]:
        first, second = self._read_exactly(2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exactly(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exactly(8))[0]
        mask = self._read_exactly(4) if masked else b""
        payload = self._read_exactly(length)
        if mask:
            payload = bytes(
                value ^ mask[index % 4] for index, value in enumerate(payload)
            )
        return opcode, payload

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._next_id += 1
        request_id = self._next_id
        payload = json.dumps(
            {"id": request_id, "method": method, "params": params or {}},
            separators=(",", ":"),
        ).encode()
        self.socket.sendall(self._masked_frame(payload))
        while True:
            opcode, raw = self._receive_frame()
            if opcode == 8:
                raise BrowserSmokeError("DevTools WebSocket closed")
            if opcode == 9:
                self.socket.sendall(self._masked_frame(raw, opcode=10))
                continue
            if opcode != 1:
                continue
            message = json.loads(raw)
            if message.get("id") != request_id:
                if "method" in message:
                    self.events.append(message)
                continue
            if "error" in message:
                raise BrowserSmokeError(
                    f"{method} failed: {message['error'].get('message', message['error'])}"
                )
            return message.get("result") or {}

    def close(self) -> None:
        try:
            self.socket.sendall(self._masked_frame(b"", opcode=8))
        except OSError:
            pass
        self.socket.close()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _chromium_binary(explicit: str | None) -> str:
    if explicit:
        return explicit
    for name in ("chromium-browser", "chromium", "google-chrome"):
        found = shutil.which(name)
        if found:
            return found
    raise BrowserSmokeError("Chromium was not found on PATH")


def _wait_for_page(port: int, timeout: float = 20) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/list", timeout=1
            ) as response:
                pages = json.loads(response.read())
            page = next((item for item in pages if item.get("type") == "page"), None)
            if page and page.get("webSocketDebuggerUrl"):
                return page
        except Exception as exc:  # Chromium is still starting.
            last_error = exc
        time.sleep(0.1)
    raise BrowserSmokeError(f"Chromium DevTools did not start: {last_error}")


def _evaluate(
    cdp: DevToolsConnection, expression: str, *, await_promise: bool = False
) -> Any:
    result = cdp.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
            "userGesture": True,
        },
    )
    if result.get("exceptionDetails"):
        detail = result["exceptionDetails"]
        raise BrowserSmokeError(
            detail.get("exception", {}).get("description")
            or detail.get("text")
            or "browser evaluation failed"
        )
    return (result.get("result") or {}).get("value")


def _wait_js(
    cdp: DevToolsConnection, expression: str, *, timeout: float = 20
) -> Any:
    deadline = time.monotonic() + timeout
    last_value: Any = None
    while time.monotonic() < deadline:
        try:
            last_value = _evaluate(cdp, expression)
            if last_value:
                return last_value
        except BrowserSmokeError as exc:
            if "Execution context was destroyed" not in str(exc):
                raise
        time.sleep(0.1)
    raise BrowserSmokeError(
        f"browser condition timed out after {timeout:.1f}s: {expression}; "
        f"last value={last_value!r}"
    )


def _screenshot(cdp: DevToolsConnection, path: Path) -> None:
    result = cdp.call(
        "Page.captureScreenshot",
        {"format": "png", "fromSurface": True, "captureBeyondViewport": False},
    )
    path.write_bytes(base64.b64decode(result["data"]))


def _paeth(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    distance_left = abs(estimate - left)
    distance_up = abs(estimate - up)
    distance_up_left = abs(estimate - up_left)
    if distance_left <= distance_up and distance_left <= distance_up_left:
        return left
    if distance_up <= distance_up_left:
        return up
    return up_left


def _decode_png(path: Path) -> tuple[int, int, int, bytes]:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise BrowserSmokeError(f"{path.name} is not a PNG")
    cursor = 8
    width = height = bit_depth = color_type = None
    idat = bytearray()
    while cursor + 8 <= len(raw):
        length = struct.unpack(">I", raw[cursor : cursor + 4])[0]
        chunk = raw[cursor + 4 : cursor + 8]
        data = raw[cursor + 8 : cursor + 8 + length]
        cursor += 12 + length
        if chunk == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", data[:10])
        elif chunk == b"IDAT":
            idat.extend(data)
        elif chunk == b"IEND":
            break
    if width is None or height is None:
        raise BrowserSmokeError(f"{path.name} is missing IHDR")
    if bit_depth != 8 or color_type not in {2, 6}:
        raise BrowserSmokeError(f"{path.name} uses unsupported PNG format {bit_depth}/{color_type}")
    channels = 3 if color_type == 2 else 4
    decompressed = zlib.decompress(bytes(idat))
    stride = width * channels
    rows: list[bytes] = []
    offset = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = decompressed[offset]
        scan = bytearray(decompressed[offset + 1 : offset + 1 + stride])
        offset += 1 + stride
        if filter_type == 1:
            for index, value in enumerate(scan):
                left = scan[index - channels] if index >= channels else 0
                scan[index] = (value + left) & 255
        elif filter_type == 2:
            for index, value in enumerate(scan):
                scan[index] = (value + previous[index]) & 255
        elif filter_type == 3:
            for index, value in enumerate(scan):
                left = scan[index - channels] if index >= channels else 0
                scan[index] = (value + ((left + previous[index]) // 2)) & 255
        elif filter_type == 4:
            for index, value in enumerate(scan):
                left = scan[index - channels] if index >= channels else 0
                up_left = previous[index - channels] if index >= channels else 0
                scan[index] = (value + _paeth(left, previous[index], up_left)) & 255
        elif filter_type != 0:
            raise BrowserSmokeError(f"{path.name} uses unsupported PNG filter {filter_type}")
        rows.append(bytes(scan))
        previous = scan
    return width, height, channels, b"".join(rows)


def _png_region_stats(
    path: Path,
    *,
    left: float = 0.22,
    top: float = 0.12,
    right: float = 0.78,
    bottom: float = 0.72,
    step: int = 4,
) -> dict[str, Any]:
    width, height, channels, pixels = _decode_png(path)
    x0, y0 = int(width * left), int(height * top)
    x1, y1 = max(x0 + 1, int(width * right)), max(y0 + 1, int(height * bottom))
    unique: set[tuple[int, int, int]] = set()
    count = 0
    sum_luma = 0.0
    sum_luma_sq = 0.0
    sum_blue = 0
    for y in range(y0, y1, step):
        row = y * width * channels
        for x in range(x0, x1, step):
            index = row + x * channels
            red, green, blue = pixels[index], pixels[index + 1], pixels[index + 2]
            unique.add((red // 16, green // 16, blue // 16))
            luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
            sum_luma += luma
            sum_luma_sq += luma * luma
            sum_blue += blue
            count += 1
    mean = sum_luma / count
    variance = max(0.0, sum_luma_sq / count - mean * mean)
    stdev = variance ** 0.5
    return {
        "unique_quantized": len(unique),
        "luma_mean": round(mean, 2),
        "luma_std": round(stdev, 2),
        "blue_mean": round(sum_blue / count, 2),
        "samples": count,
        "ok": len(unique) >= 12 and stdev >= 6,
    }


def _png_mean_abs_diff(
    first: Path,
    second: Path,
    *,
    left: float = 0.22,
    top: float = 0.12,
    right: float = 0.78,
    bottom: float = 0.72,
    step: int = 4,
) -> float:
    width, height, channels, pixels_a = _decode_png(first)
    width_b, height_b, channels_b, pixels_b = _decode_png(second)
    if (width, height, channels) != (width_b, height_b, channels_b):
        raise BrowserSmokeError("PNG dimensions do not match for visual diff")
    x0, y0 = int(width * left), int(height * top)
    x1, y1 = max(x0 + 1, int(width * right)), max(y0 + 1, int(height * bottom))
    total = 0
    count = 0
    for y in range(y0, y1, step):
        row = y * width * channels
        for x in range(x0, x1, step):
            index = row + x * channels
            total += abs(pixels_a[index] - pixels_b[index])
            total += abs(pixels_a[index + 1] - pixels_b[index + 1])
            total += abs(pixels_a[index + 2] - pixels_b[index + 2])
            count += 3
    return total / count


def _state(cdp: DevToolsConnection) -> dict[str, Any]:
    value = _evaluate(
        cdp,
        """(() => {
          const packet = (typeof packets !== 'undefined' && selectedId) ? packets[selectedId] : null;
          const scene = packet && packet.scene;
          const trace = window.__streamTrace || [];
          const packetIndex = trace.findIndex((row) => row.event === 'packet');
          return {
            mission: typeof mission === 'undefined' ? null : mission,
            selectedId: typeof selectedId === 'undefined' ? null : selectedId,
            sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
            planReady: typeof plan !== 'undefined' && Boolean(plan),
            cards: document.querySelectorAll('#cards .card').length,
            verdict: document.querySelector('#verdict')?.textContent || '',
            rail: document.querySelector('#rail')?.textContent || '',
            context: document.querySelector('#context-tag')?.textContent || '',
            status: document.querySelector('#status')?.textContent || '',
            scoreStates: Array.from(document.querySelectorAll('#scorecard .status-text')).map(el => el.textContent),
            floodMeter: Number(document.querySelector('.meter-row[data-id="flood"]')?.dataset.meter || 0),
            authVisible: !document.querySelector('#auth-gate')?.classList.contains('hidden'),
            consoleReady: document.readyState,
            loadedTiles: document.querySelectorAll('#quick-map img[data-loaded="true"]').length,
            pastAlpha: Number(document.querySelector('#past-overlay')?.dataset.alpha || 0),
            pastYear: Number(document.querySelector('#past-overlay')?.dataset.year || 0),
            padClaim: document.querySelector('#placement-claim')?.dataset.claim || '',
            padFit: document.querySelector('#placement-claim')?.dataset.fit || '',
            padOverlayClaim: document.querySelector('#pad-overlay')?.dataset.claim || '',
            futureBox: Boolean(document.querySelector('.future-box')),
            modelReady: Boolean(typeof conceptModel !== 'undefined' && conceptModel && conceptModel.ready),
            pastKind: scene?.past?.kind || null,
            pastScores: scene?.past?.scores,
            pastSeries: Array.isArray(scene?.past?.series) ? scene.past.series.length : 0,
            pastYearsObserved: scene?.past?.years_observed ?? null,
            futureClaim: scene?.future?.claim || null,
            streamPacketIndex: packetIndex,
            streamWorkstreamsBeforePacket: trace.slice(0, Math.max(packetIndex, 0)).filter((row) => row.event === 'workstream' && (row.status === 'running' || row.status === 'succeeded')).length,
          };
        })()""",
    )
    if not isinstance(value, dict):
        raise BrowserSmokeError("could not read browser state")
    return value


def _pick_and_run(cdp: DevToolsConnection, mission: str) -> dict[str, Any]:
    _evaluate(cdp, f"pickMission({json.dumps(mission)})")
    _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
    _evaluate(
        cdp,
        "(async () => { await confirmPlan(); await runExpedition(); return true; })()",
        await_promise=True,
    )
    return _state(cdp)


def _wait_for_scene(cdp: DevToolsConnection, *, future: bool = False) -> dict[str, Any]:
    target = "conceptModel?.readyPromise" if future else "tileset?.readyPromise"
    value = _evaluate(
        cdp,
        """(async () => {
          const readiness = %s;
          if (readiness) {
            await Promise.race([
              readiness,
              new Promise((_, reject) => setTimeout(() => reject(new Error('scene readiness timeout')), 15000)),
            ]);
          }
          if (!%s && config.has_google_tiles) {
            const deadline = Date.now() + 18000;
            while (Date.now() < deadline) {
              const ready = tileset?._statistics?.numberOfTilesWithContentReady || 0;
              if (ready >= 250) break;
              await new Promise(resolve => setTimeout(resolve, 250));
            }
            if ((tileset?._statistics?.numberOfTilesWithContentReady || 0) < 250) {
              throw new Error('photorealistic 3D content did not render');
            }
          }
          await new Promise(resolve => setTimeout(resolve, 800));
          return {
            tileContentReady: tileset?._statistics?.numberOfTilesWithContentReady || 0,
            modelReady: Boolean(conceptModel?.ready),
          };
        })()""" % (target, "true" if future else "false"),
        await_promise=True,
    )
    return value if isinstance(value, dict) else {}


def _browser_diagnostics(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for event in events:
        method = event.get("method")
        params = event.get("params") or {}
        if method == "Runtime.exceptionThrown":
            detail = params.get("exceptionDetails") or {}
            failures.append(
                {
                    "kind": "exception",
                    "text": detail.get("text"),
                    "description": (detail.get("exception") or {}).get("description"),
                }
            )
        elif method == "Log.entryAdded":
            entry = params.get("entry") or {}
            if entry.get("level") == "error":
                failures.append(
                    {"kind": "console", "source": entry.get("source"), "text": entry.get("text")}
                )
        elif method == "Network.loadingFailed" and not params.get("canceled"):
            failures.append(
                {
                    "kind": "network",
                    "error": params.get("errorText"),
                    "type": params.get("type"),
                }
            )
    # Headless SwiftShader and deliberate reload cancellation are platform noise,
    # not page failures.  Chromium emits those to stderr, which is not in this list.
    return failures


def run(args: argparse.Namespace) -> dict[str, Any]:
    token = args.token_file.read_text().strip() if args.token_file.exists() else ""
    if not token:
        token = "auth-disabled"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    started = time.time()
    report: dict[str, Any] = {
        "base_url": args.base_url,
        "started": started,
        "steps": [],
        "artifacts": [],
    }
    with tempfile.TemporaryDirectory(prefix="expedition-browser-") as profile:
        command = [
            chromium,
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--no-first-run",
            "--window-size=1440,1000",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            args.base_url,
        ]
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        cdp: DevToolsConnection | None = None
        try:
            page = _wait_for_page(port)
            cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
            for domain in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
                cdp.call(domain)
            cdp.call(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 1440,
                    "height": 1000,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
            )
            _wait_js(cdp, "document.readyState === 'complete'")
            auth_visible = _evaluate(
                cdp,
                "!document.querySelector('#auth-gate')?.classList.contains('hidden')",
            )
            auth_path = args.output_dir / "01-auth-gate.png"
            _screenshot(cdp, auth_path)
            report["artifacts"].append(str(auth_path))
            if auth_visible:
                auth_result = _evaluate(
                    cdp,
                    """(async () => {
                      const response = await fetch('/api/session', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token: %s}),
                      });
                      return {status: response.status};
                    })()""" % json.dumps(token),
                    await_promise=True,
                )
                if auth_result != {"status": 200}:
                    raise BrowserSmokeError(
                        f"browser session exchange failed: {auth_result!r}"
                    )
                cdp.call("Page.reload", {"ignoreCache": True})
                _wait_js(
                    cdp,
                    "document.readyState === 'complete' && document.querySelectorAll('#tiles .tile').length === 5 && document.querySelector('#auth-gate')?.classList.contains('hidden')",
                )
                report["steps"].append({"id": "auth_gate", "ok": True})
            else:
                _wait_js(cdp, "document.querySelectorAll('#tiles .tile').length === 5")
                report["steps"].append({"id": "auth_gate", "ok": True, "skipped": True})

            warehouse = _pick_and_run(cdp, "warehouse")
            _evaluate(cdp, "selectSite('san_leon', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'san_leon' && packets.san_leon && packets.san_leon.scene")
            _evaluate(cdp, "applyMode('past')")
            _wait_js(
                cdp,
                "sceneMode === 'past' && document.querySelector('#past-overlay') && document.querySelectorAll('#quick-map img[data-loaded=\"true\"]').length >= 4",
                timeout=25,
            )
            alpha_1985 = _evaluate(
                cdp,
                """(() => {
                  const slider = document.querySelector('#past-year');
                  slider.value = '1985';
                  slider.dispatchEvent(new Event('input', {bubbles: true}));
                  return Number(document.querySelector('#past-overlay').dataset.alpha);
                })()""",
            )
            past_1985_path = args.output_dir / "02a-past-1985.png"
            _screenshot(cdp, past_1985_path)
            report["artifacts"].append(str(past_1985_path))
            alpha_2001 = _evaluate(
                cdp,
                """(() => {
                  const slider = document.querySelector('#past-year');
                  slider.value = '2001';
                  slider.dispatchEvent(new Event('input', {bubbles: true}));
                  return Number(document.querySelector('#past-overlay').dataset.alpha);
                })()""",
            )
            past_2001_path = args.output_dir / "02b-past-2001.png"
            _screenshot(cdp, past_2001_path)
            report["artifacts"].append(str(past_2001_path))
            past_stats_1985 = _png_region_stats(past_1985_path)
            past_stats_2001 = _png_region_stats(past_2001_path)
            past_diff = _png_mean_abs_diff(past_1985_path, past_2001_path)
            warehouse_state = _state(cdp)
            stream_ok = (
                int(warehouse_state.get("streamPacketIndex") or -1) >= 2
                and int(warehouse_state.get("streamWorkstreamsBeforePacket") or 0) >= 1
            )
            past_ok = (
                warehouse_state.get("pastKind") == "flood_rewind"
                and warehouse_state.get("pastScores") is False
                and float(alpha_1985) < 0.05
                and float(alpha_2001) > float(alpha_1985) + 0.1
                and int(warehouse_state.get("loadedTiles") or 0) >= 4
                and past_stats_1985["ok"]
                and past_stats_2001["ok"]
                and past_diff >= 1.5
            )
            warehouse_ok = (
                warehouse["cards"] == 4
                and bool(warehouse["verdict"])
                and "running" not in warehouse["rail"].lower()
                and "environmental-record" in warehouse["rail"]
                and bool(warehouse["scoreStates"])
                and int(warehouse_state.get("floodMeter") or 0) == 100
                and stream_ok
                and past_ok
            )
            warehouse_path = args.output_dir / "02-warehouse.png"
            _screenshot(cdp, warehouse_path)
            report["artifacts"].append(str(warehouse_path))
            report["steps"].append(
                {
                    "id": "warehouse",
                    "ok": warehouse_ok,
                    "state": warehouse_state,
                    "past": {
                        "alpha_1985": alpha_1985,
                        "alpha_2001": alpha_2001,
                        "png_1985": past_stats_1985,
                        "png_2001": past_stats_2001,
                        "png_mad": round(past_diff, 3),
                    },
                }
            )

            _evaluate(cdp, "applyMode('mesh')")
            try:
                warehouse_scene = _wait_for_scene(cdp)
                mesh_ok = int(warehouse_scene.get("tileContentReady") or 0) >= 250 or not _evaluate(
                    cdp, "Boolean(config.has_google_tiles)"
                )
            except BrowserSmokeError as exc:
                warehouse_scene = {"error": str(exc)}
                mesh_ok = False
            mesh_path = args.output_dir / "02c-today-3d.png"
            _screenshot(cdp, mesh_path)
            report["artifacts"].append(str(mesh_path))
            report["steps"].append(
                {
                    "id": "warehouse_3d",
                    "ok": mesh_ok,
                    "scene": warehouse_scene,
                }
            )

            _evaluate(cdp, "applyMode('future')")
            _wait_js(
                cdp,
                "sceneMode === 'future' && document.querySelector('#placement-claim')?.dataset.claim === 'assumption'",
            )
            future_scene = _wait_for_scene(cdp, future=True)
            future = _state(cdp)
            future_path = args.output_dir / "03-future.png"
            _screenshot(cdp, future_path)
            report["artifacts"].append(str(future_path))
            future_png = _png_region_stats(future_path)
            future_ok = (
                future.get("sceneMode") == "future"
                and future.get("padClaim") == "assumption"
                and future.get("padFit") == "deferred"
                and future.get("futureClaim") == "visual_concept"
                and "future visual concept" in future["context"].lower()
                and bool(future_scene.get("modelReady"))
                and future_png["ok"]
            )
            report["steps"].append(
                {
                    "id": "future",
                    "ok": future_ok,
                    "state": future,
                    "scene": future_scene,
                    "png": future_png,
                }
            )

            _evaluate(cdp, "document.querySelector('#replan').click()")
            farm = _pick_and_run(cdp, "farm")
            _evaluate(cdp, "selectSite('iowa_corn', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'iowa_corn' && packets.iowa_corn && packets.iowa_corn.scene")
            _wait_js(
                cdp,
                "document.querySelectorAll('#quick-map img[data-loaded=\"true\"]').length >= 4",
                timeout=20,
            )
            farm = _state(cdp)
            farm_path = args.output_dir / "04-farm.png"
            _screenshot(cdp, farm_path)
            report["artifacts"].append(str(farm_path))
            report["steps"].append(
                {
                    "id": "farm",
                    "ok": farm["cards"] > 0
                    and "farm-history" in farm["rail"]
                    and "FUTURE" not in farm["context"]
                    and farm.get("pastKind") == "farm_history"
                    and farm.get("pastSeries") == 0
                    and farm.get("pastYearsObserved") == 9
                    and farm.get("pastScores") is False,
                    "state": farm,
                }
            )

            _evaluate(cdp, "document.querySelector('#replan').click()")
            data_center = _pick_and_run(cdp, "data_center")
            data_path = args.output_dir / "05-data-center.png"
            _screenshot(cdp, data_path)
            report["artifacts"].append(str(data_path))
            report["steps"].append(
                {
                    "id": "data_center",
                    "ok": data_center["cards"] == 2
                    and "observed-heat" in data_center["rail"]
                    and "FUTURE" not in data_center["context"],
                    "state": data_center,
                }
            )

            _evaluate(cdp, "document.querySelector('#replan').click()")
            _evaluate(cdp, "pickMission('custom')")
            _wait_js(cdp, "Boolean(document.querySelector('#manifest-id option:nth-child(2)'))")
            _evaluate(
                cdp,
                """(() => {
                  const select = document.querySelector('#manifest-id');
                  select.value = select.options[1].value;
                  select.dispatchEvent(new Event('change', {bubbles: true}));
                  return select.value;
                })()""",
            )
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            _evaluate(
                cdp,
                "(async () => { await confirmPlan(); await runExpedition(); return true; })()",
                await_promise=True,
            )
            custom = _state(cdp)
            custom_path = args.output_dir / "06-custom.png"
            _screenshot(cdp, custom_path)
            report["artifacts"].append(str(custom_path))
            report["steps"].append(
                {"id": "custom", "ok": custom["cards"] == 4, "state": custom}
            )

            _evaluate(cdp, "document.querySelector('#replan').click()")
            _evaluate(cdp, "pickMission('warehouse')")
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            _evaluate(cdp, "(async () => { await confirmPlan(); return true; })()", await_promise=True)
            _evaluate(
                cdp,
                """(() => {
                  document.querySelector('#pin-lat').value = '40.12345';
                  document.querySelector('#pin-lng').value = '-100.54321';
                  addUserSite();
                  return selectedId;
                })()""",
            )
            negative_event_start = len(cdp.events)
            _evaluate(cdp, "(async () => { await runOne(selectedId); return true; })()", await_promise=True)
            replay_miss = _state(cdp)
            miss_path = args.output_dir / "07-replay-miss.png"
            _screenshot(cdp, miss_path)
            report["artifacts"].append(str(miss_path))
            report["steps"].append(
                {
                    "id": "replay_miss",
                    "ok": "failed" in replay_miss["rail"].lower()
                    and "running" not in replay_miss["rail"].lower(),
                    "state": replay_miss,
                }
            )

            positive_diagnostics = _browser_diagnostics(cdp.events[:negative_event_start])
            negative_diagnostics = _browser_diagnostics(cdp.events[negative_event_start:])
            expected_negative = [
                item
                for item in negative_diagnostics
                if "status of 409" in str(item.get("text") or "")
                or "replay_cache_miss" in str(item.get("text") or "")
            ]
            report["expected_negative_diagnostics"] = expected_negative
            report["diagnostics"] = positive_diagnostics + [
                item for item in negative_diagnostics if item not in expected_negative
            ]
        finally:
            if cdp is not None:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    report["finished"] = time.time()
    report["elapsed_s"] = round(report["finished"] - started, 3)
    report["passed"] = sum(1 for step in report["steps"] if step.get("ok"))
    report["failed"] = sum(1 for step in report["steps"] if not step.get("ok"))
    report["ok"] = report["failed"] == 0 and not report.get("diagnostics")
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--base-url", default="http://127.0.0.1:8030")
    result.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    result.add_argument("--chromium", default=None)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        report = run(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    public = {
        "ok": report["ok"],
        "passed": report["passed"],
        "failed": report["failed"],
        "elapsed_s": report["elapsed_s"],
        "diagnostics": report.get("diagnostics", []),
        "artifacts": report["artifacts"],
    }
    print(json.dumps(public, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
