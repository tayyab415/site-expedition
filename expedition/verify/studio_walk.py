"""Click the warehouse board in real time and x11grab the headed window.

This is not a screenshot slideshow. DISPLAY must point at a 1440x1000 Xvfb.

    DISPLAY=:97 PYTHONPATH=. python3 -m expedition.verify.studio_walk
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from expedition.verify.browser_smoke import (
    BrowserSmokeError,
    DevToolsConnection,
    _chromium_binary,
    _evaluate,
    _free_port,
    _wait_for_page,
    _wait_js,
)
from expedition.verify.feature_record import (
    Recorder,
    _mouse,
    _state,
    click,
    ensure_deck_open,
    ensure_rail_open,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "studio-walk"


def _close_overlays(cdp: DevToolsConnection) -> None:
    hidden = _evaluate(cdp, "Boolean(document.querySelector('#video-panel')?.hidden)")
    if hidden is False:
        try:
            click(cdp, "#close-video")
        except BrowserSmokeError:
            _evaluate(cdp, "document.querySelector('#video-panel').hidden = true")
        time.sleep(0.4)


def _select_card(cdp: DevToolsConnection, site_id: str) -> None:
    _close_overlays(cdp)
    try:
        _click_frac(cdp, f'.card[data-id="{site_id}"]', 0.5, 0.25)
    except BrowserSmokeError:
        pass
    time.sleep(0.5)
    if _evaluate(cdp, f"selectedId !== {site_id!r}"):
        _evaluate(cdp, f"selectSite({site_id!r}, {{fly: true, duration: 1.2}})")
        time.sleep(0.6)


def _hold(cdp: DevToolsConnection, recorder: Recorder, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        recorder.grab(cdp)
        time.sleep(0.45)


def _click_frac(cdp: DevToolsConnection, selector: str, fx: float, fy: float = 0.5) -> None:
    box = _evaluate(
        cdp,
        f"""(() => {{
          const el = document.querySelector({selector!r});
          if (!el) return null;
          el.scrollIntoView({{block: 'center', inline: 'nearest'}});
          const r = el.getBoundingClientRect();
          if (r.width < 2 || r.height < 2) return null;
          return {{x: r.x + r.width * {fx}, y: r.y + r.height * {fy}}};
        }})()""",
    )
    if not box:
        raise BrowserSmokeError(f"cannot click {selector}")
    _mouse(cdp, "mouseMoved", box["x"], box["y"])
    time.sleep(0.08)
    _mouse(cdp, "mousePressed", box["x"], box["y"])
    _mouse(cdp, "mouseReleased", box["x"], box["y"])
    time.sleep(0.3)


def _wait_packets(cdp: DevToolsConnection, recorder: Recorder, minimum: int = 4, timeout: float = 55) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    state: dict[str, Any] = {}
    while time.monotonic() < deadline:
        recorder.grab(cdp)
        state = _state(cdp)
        if state.get("packetCount", 0) >= minimum and not _evaluate(
            cdp, "Boolean(document.querySelector('#run-all')?.disabled)"
        ):
            return state
        time.sleep(0.45)
    return state


def _wait_mesh(cdp: DevToolsConnection, recorder: Recorder, timeout: float = 18) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    state: dict[str, Any] = {}
    while time.monotonic() < deadline:
        recorder.grab(cdp)
        state = _state(cdp)
        tiles = int(
            _evaluate(
                cdp,
                "Number((typeof tileset !== 'undefined' && tileset && tileset._statistics && tileset._statistics.numberOfTilesWithContentReady) || 0)",
            )
            or 0
        )
        mesh = bool(_evaluate(cdp, "Boolean(typeof meshContentReady !== 'undefined' && meshContentReady)"))
        if mesh and tiles >= 40:
            return state
        time.sleep(0.5)
    return state


class LoggedRecorder(Recorder):
    """Same x11grab path, but keep ffmpeg's stderr so a black clip is diagnosable."""

    def start(self, name: str) -> None:
        self.stop()
        self.current = name
        dest = self.clips / f"{name}.mp4"
        if dest.exists():
            dest.unlink()
        self.fallback_frames = []
        if not self.display:
            return
        log = self.output / "ffmpeg-x11grab.log"
        self.proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-f", "x11grab", "-video_size", "1440x1000",
                "-framerate", "12", "-i", self.display,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                "-crf", "23", "-movflags", "+faststart", str(dest),
            ],
            stdout=subprocess.DEVNULL,
            stderr=log.open("w"),
        )
        time.sleep(0.6)
        if self.proc.poll() is not None:
            self.proc = None


def run(args: argparse.Namespace) -> dict[str, Any]:
    display = os.environ.get("DISPLAY")
    if not display:
        raise BrowserSmokeError("DISPLAY is required — start Xvfb and pass DISPLAY=:97")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    recorder = LoggedRecorder(output, display)
    notes: list[str] = []
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="expedition-studio-walk-") as profile:
        command = [
            chromium,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--no-first-run",
            "--disable-session-crashed-bubble",
            "--hide-crash-restore-bubble",
            "--window-size=1440,1000",
            "--window-position=0,0",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            f"--app={args.base_url}",
        ]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp: DevToolsConnection | None = None
        try:
            page = _wait_for_page(port)
            cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
            for domain in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
                cdp.call(domain)
            cdp.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
            )
            _wait_js(
                cdp,
                "document.readyState === 'complete' && document.querySelectorAll('#tiles .tile').length === 5",
            )
            time.sleep(0.8)

            recorder.start("warehouse-clickthrough")
            _hold(cdp, recorder, 4.0)
            recorder.grab(cdp, "01-onboard")

            click(cdp, '.tile[data-id="warehouse"]')
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            _hold(cdp, recorder, 5.0)
            recorder.grab(cdp, "02-warehouse-plan")

            click(cdp, "#confirm")
            _wait_js(
                cdp,
                "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')",
            )
            ensure_deck_open(cdp)
            ensure_rail_open(cdp)
            _close_overlays(cdp)
            _hold(cdp, recorder, 3.5)
            recorder.grab(cdp, "03-board-before-run")

            click(cdp, "#run-all")
            state = _wait_packets(cdp, recorder)
            _close_overlays(cdp)
            _hold(cdp, recorder, 4.0)
            recorder.grab(cdp, "04-after-run")
            notes.append("after_run:" + json.dumps(state, default=str)[:4000])

            _select_card(cdp, "san_leon")
            _wait_js(cdp, "selectedId === 'san_leon' && Boolean(packets.san_leon)", timeout=8)
            _hold(cdp, recorder, 2.5)
            past_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-past')?.disabled)"))
            deadline = time.monotonic() + 8
            while not past_ready and time.monotonic() < deadline:
                time.sleep(0.4)
                recorder.grab(cdp)
                past_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-past')?.disabled)"))
            if past_ready:
                click(cdp, "#mode-past")
                time.sleep(1.2)
                _hold(cdp, recorder, 4.0)
                try:
                    _click_frac(cdp, "#past-year", 0.2)
                    _hold(cdp, recorder, 2.2)
                    _click_frac(cdp, "#past-year", 0.78)
                    _hold(cdp, recorder, 2.5)
                except BrowserSmokeError:
                    _hold(cdp, recorder, 2.0)
            else:
                notes.append("past_button_disabled")
                _hold(cdp, recorder, 3.0)
            recorder.grab(cdp, "05-past")

            _select_card(cdp, "san_marcos_tx")
            _wait_js(cdp, "selectedId === 'san_marcos_tx'", timeout=8)
            _hold(cdp, recorder, 3.0)
            click(cdp, "#mode-today")
            _hold(cdp, recorder, 2.0)
            click(cdp, "#mode-earth")
            _hold(cdp, recorder, 4.0)
            mesh_ok = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-mesh')?.disabled)"))
            deadline = time.monotonic() + 10
            while not mesh_ok and time.monotonic() < deadline:
                time.sleep(0.4)
                recorder.grab(cdp)
                mesh_ok = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-mesh')?.disabled)"))
            if mesh_ok:
                click(cdp, "#mode-mesh")
            _wait_mesh(cdp, recorder)
            _hold(cdp, recorder, 6.0)
            recorder.grab(cdp, "06-today-3d")

            future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
            deadline = time.monotonic() + 8
            while not future_ready and time.monotonic() < deadline:
                time.sleep(0.4)
                recorder.grab(cdp)
                future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
            if future_ready:
                click(cdp, "#mode-future")
                time.sleep(1.5)
                _hold(cdp, recorder, 7.0)
            else:
                notes.append("future_button_disabled")
                _hold(cdp, recorder, 3.0)
            recorder.grab(cdp, "09-future-san-marcos")

            ensure_rail_open(cdp)
            try:
                click(cdp, "#show-interior")
                _hold(cdp, recorder, 6.0)
                click(cdp, "#concept-preset")
                _hold(cdp, recorder, 2.5)
                _evaluate(cdp, "document.querySelector('#concept-cad')?.scrollIntoView({block:'center'})")
                _hold(cdp, recorder, 2.0)
            except BrowserSmokeError as exc:
                notes.append(f"interior:{exc}")
                _hold(cdp, recorder, 3.0)
            recorder.grab(cdp, "11-future-interior")
            notes.append(
                "studio:"
                + json.dumps(
                    _evaluate(
                        cdp,
                        """(() => ({
                          selectedId: selectedId,
                          sceneMode: sceneMode,
                          interior: Boolean(document.querySelector('#show-interior')?.checked),
                          cadText: document.querySelector('#concept-cad')?.innerText || '',
                          preset: document.querySelector('#concept-preset')?.selectedOptions?.[0]?.textContent || '',
                          placement: document.querySelector('#placement-claim')?.textContent || '',
                          verdict: document.querySelector('#verdict')?.textContent || '',
                        }))()""",
                    ),
                    default=str,
                )
            )
            _hold(cdp, recorder, 3.0)
        finally:
            recorder.stop()
            if cdp:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    clip = output / "clips" / "warehouse-clickthrough.mp4"
    published = output / "warehouse-user-flow.mp4"
    if clip.is_file():
        shutil.copy2(clip, published)
    elapsed = round(time.time() - started, 3)
    report = {
        "ok": clip.is_file() and clip.stat().st_size > 50_000,
        "kind": "x11grab-clickthrough" if display else "missing-display",
        "elapsed_s": elapsed,
        "video": str(published),
        "clip": str(clip),
        "bytes": clip.stat().st_size if clip.is_file() else 0,
        "notes": notes,
    }
    (output / "clickthrough-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("ok", "elapsed_s", "video", "bytes")}))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chromium", default=None)
    args = parser.parse_args()
    try:
        run(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
