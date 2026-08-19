"""Record the UChicago Aerial View 3D orbit on Earth, and Orbit without the cartoon tilt.

    DISPLAY=:98 PYTHONPATH=. python3 -m expedition.verify.earth_record --base-url http://127.0.0.1:8030
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from expedition.verify.browser_smoke import (
    DevToolsConnection,
    _chromium_binary,
    _evaluate,
    _free_port,
    _wait_for_page,
    _wait_js,
)
from expedition.verify.feature_record import Recorder, click, _check


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "earth"


def _scene(cdp: DevToolsConnection) -> dict[str, Any]:
    value = _evaluate(
        cdp,
        """(() => {
          const ground = document.querySelector('#earth-ground');
          const video = document.querySelector('#aerial-video');
          return {
            sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
            context: document.querySelector('#context-tag')?.textContent || '',
            streetHidden: Boolean(document.querySelector('#street-stage')?.hidden),
            earthHidden: Boolean(document.querySelector('#earth-stage')?.hidden),
            earthTiles: ground ? ground.querySelectorAll('img[data-loaded="true"]').length : 0,
            earthImgs: ground ? ground.querySelectorAll('img').length : 0,
            videoHidden: Boolean(document.querySelector('#video-panel')?.hidden),
            videoSrc: (video && video.currentSrc) ? (video.currentSrc.includes('googlevideo') || video.currentSrc.startsWith('http') ? 'http' : video.currentSrc) : '',
            videoTime: video ? Number(video.currentTime || 0) : 0,
            selectedId: typeof selectedId === 'undefined' ? null : selectedId,
            addressStatus: document.querySelector('#address-status')?.textContent || '',
            aerialStatus: document.querySelector('#aerial-status')?.textContent || '',
          };
        })()""",
    )
    return value if isinstance(value, dict) else {}


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    display = os.environ.get("DISPLAY")
    recorder = Recorder(output, display)
    checks: list[dict[str, Any]] = []
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    with tempfile.TemporaryDirectory(prefix="expedition-earth-") as profile:
        command = [
            chromium,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader",
            "--disable-background-networking",
            "--no-first-run",
            "--autoplay-policy=no-user-gesture-required",
            "--window-size=1440,1000",
            "--window-position=0,0",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            f"--app={args.base_url}/?variant=A",
        ]
        if not display:
            command.insert(1, "--headless=new")
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cdp = None
        try:
            page = _wait_for_page(port)
            cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
            for domain in ("Page.enable", "Runtime.enable", "Network.enable"):
                cdp.call(domain)
            cdp.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
            )
            _wait_js(cdp, "document.querySelectorAll('#tiles .tile').length === 5")
            click(cdp, '.tile[data-id="warehouse"]')
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            click(cdp, "#confirm")
            _wait_js(
                cdp,
                "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')",
            )
            _wait_js(cdp, "Boolean(typeof viewer !== 'undefined' && viewer)", timeout=30)
            time.sleep(1.2)
            _evaluate(cdp, "selectSite('san_marcos_tx', {fly:true})")
            time.sleep(0.8)

            recorder.start("earth-uchicago")
            _evaluate(cdp, "applyMode('earth')")
            deadline = time.monotonic() + 20
            state = {}
            while time.monotonic() < deadline:
                state = _scene(cdp)
                recorder.grab(cdp)
                if (
                    state.get("sceneMode") == "earth"
                    and not state.get("videoHidden")
                    and state.get("videoTime", 0) > 0.3
                ):
                    break
                time.sleep(0.4)
            time.sleep(3.0)
            recorder.grab(cdp, "earth-uchicago")
            _check(
                checks,
                "earth-uchicago",
                "Earth plays the UChicago Aerial View 3D orbit",
                state.get("sceneMode") == "earth"
                and not state.get("videoHidden")
                and "http" in (state.get("videoSrc") or ""),
                json.dumps(state),
            )
            _check(
                checks,
                "earth-uchicago",
                "Earth is Aerial View, not a tilted 2D map",
                state.get("earthHidden") is True
                and "aerial view" in (state.get("context") or "").lower(),
                state.get("context"),
            )
            recorder.stop()

            recorder.start("orbit-this-pin")
            _evaluate(cdp, "selectSite('san_marcos_tx', {fly:false}); applyMode('orbit')")
            deadline = time.monotonic() + 8
            orbit = {}
            while time.monotonic() < deadline:
                recorder.grab(cdp)
                orbit = _scene(cdp)
                if orbit.get("sceneMode") == "orbit" and orbit.get("earthHidden"):
                    break
                time.sleep(0.4)
            time.sleep(2.0)
            recorder.grab(cdp, "orbit-this-pin")
            _check(
                checks,
                "orbit-this-pin",
                "Orbit does not fall back to the cartoon Earth tilt",
                orbit.get("sceneMode") == "orbit" and orbit.get("earthHidden") is True,
                json.dumps(orbit),
            )
            recorder.stop()
        finally:
            recorder.stop()
            if cdp:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    report = {
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "output": str(output),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chromium", default=None)
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
