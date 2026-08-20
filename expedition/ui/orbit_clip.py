"""Local orbit clips rendered from Google photorealistic tiles.

Google's Aerial View render queue can take hours for a first-time address.
This renders a comparable orbit clip on this machine in about a minute by
stepping a headless Chromium around the pin on /orbit-stage.html and encoding
the frames with ffmpeg. Clips are cached on disk forever. Presentation only;
nothing here enters scoring.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIP_DIR = ROOT / "var" / "cache" / "orbit"
FRAMES = 120
FPS = 12
WIDTH, HEIGHT = 1024, 576

_LOCK = threading.Lock()
_STATE: dict[str, str] = {}
_RENDER_SLOT = threading.Semaphore(1)  # swiftshader is CPU-heavy; one render at a time


def _display() -> str | None:
    """An X display to render on. Headless swiftshader draws the mesh black,
    so headed Chromium on Xvfb is required for textured tiles."""
    if os.environ.get("DISPLAY"):
        return os.environ["DISPLAY"]
    x11 = Path("/tmp/.X11-unix")
    if x11.is_dir():
        for sock in sorted(x11.iterdir()):
            if sock.name.startswith("X") and sock.name[1:].isdigit():
                return f":{sock.name[1:]}"
    return None


def clip_file(lat: float, lng: float) -> Path:
    key = f"{lat:.5f}_{lng:.5f}".replace("-", "m").replace(".", "p")
    return CLIP_DIR / f"orbit_{key}.mp4"


def ensure_clip(lat: float, lng: float, base_url: str) -> dict:
    path = clip_file(lat, lng)
    if path.is_file():
        return {"state": "READY", "url": f"/orbit-clips/{path.name}"}
    with _LOCK:
        state = _STATE.get(path.name)
        if state == "RENDERING":
            return {"state": "RENDERING", "url": None}
        if state == "FAILED":
            # Sticky per server run so pollers stop; a restart retries.
            return {"state": "FAILED", "url": None}
        _STATE[path.name] = "RENDERING"
    threading.Thread(
        target=_render, args=(lat, lng, base_url, path), daemon=True
    ).start()
    return {"state": "RENDERING", "url": None}


def _render(lat: float, lng: float, base_url: str, path: Path) -> None:
    with _RENDER_SLOT:
        try:
            _record(lat, lng, base_url, path)
            with _LOCK:
                _STATE[path.name] = "READY"
        except Exception:
            with _LOCK:
                _STATE[path.name] = "FAILED"


def _settle(cdp, timeout: float) -> None:
    from expedition.verify.browser_smoke import _evaluate

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _evaluate(cdp, "tilesSettled()") is True:
            return
        time.sleep(0.1)


def _record(lat: float, lng: float, base_url: str, path: Path) -> None:
    from expedition.verify.browser_smoke import (
        DevToolsConnection,
        _chromium_binary,
        _evaluate,
        _free_port,
        _screenshot,
        _wait_for_page,
        _wait_js,
    )

    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    chromium = _chromium_binary(None)
    with tempfile.TemporaryDirectory(prefix="orbit-clip-") as scratch:
        profile = Path(scratch) / "profile"
        frame_dir = Path(scratch) / "frames"
        frame_dir.mkdir(parents=True)
        command = [
            chromium,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader",
            "--disable-background-networking",
            "--no-first-run",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            f"--app={base_url}/orbit-stage.html?lat={lat:.7f}&lng={lng:.7f}",
        ]
        env = dict(os.environ)
        display = _display()
        if display:
            env["DISPLAY"] = display
        else:
            command.insert(1, "--headless=new")
        process = subprocess.Popen(
            command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        cdp = None
        try:
            page = _wait_for_page(port)
            cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
            for domain in ("Page.enable", "Runtime.enable"):
                cdp.call(domain)
            cdp.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": WIDTH, "height": HEIGHT, "deviceScaleFactor": 1, "mobile": False},
            )
            _wait_js(cdp, "window.__ready === true || window.__failed === true", timeout=60)
            if _evaluate(cdp, "window.__failed") is True:
                raise RuntimeError("orbit stage failed to boot")
            _settle(cdp, 60.0)
            # Warm sweep so the tile cache holds the whole ring before capture.
            for frame in range(0, FRAMES, 6):
                _evaluate(cdp, f"stepOrbit({frame}, {FRAMES})")
                _settle(cdp, 8.0)
            frames: list[Path] = []
            for frame in range(FRAMES):
                _evaluate(cdp, f"stepOrbit({frame}, {FRAMES})")
                _settle(cdp, 4.0)
                frame_path = frame_dir / f"{frame:05d}.png"
                _screenshot(cdp, frame_path)
                frames.append(frame_path)
            _encode(frame_dir, path)
        finally:
            if cdp:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def _encode(frame_dir: Path, dest: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found on PATH")
    partial = dest.with_name(dest.name + ".partial.mp4")
    subprocess.run(
        [
            ffmpeg, "-y", "-framerate", str(FPS), "-i", str(frame_dir / "%05d.png"),
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "23",
            "-movflags", "+faststart", str(partial),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    partial.replace(dest)
