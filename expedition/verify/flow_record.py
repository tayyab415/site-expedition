"""Record the Warehouse planning-board user flow as stills + an MP4.

Uses the same Chromium/CDP computer-use path as browser_smoke.  Cursor's
preview MCP is not available on this VM, so this is the hosted recorder.

    PYTHONPATH=. python3 -m expedition.verify.flow_record
"""

from __future__ import annotations

import argparse
import json
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
    _screenshot,
    _wait_for_page,
    _wait_js,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings"


def _grab(cdp: DevToolsConnection, frames: list[Path], directory: Path, label: str | None = None) -> Path:
    path = directory / "frames" / f"{len(frames):05d}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    _screenshot(cdp, path)
    frames.append(path)
    if label:
        still = directory / "stills" / f"{label}.png"
        still.parent.mkdir(parents=True, exist_ok=True)
        still.write_bytes(path.read_bytes())
    return path


def _state(cdp: DevToolsConnection) -> dict[str, Any]:
    return _evaluate(
        cdp,
        """(() => {
          const packet = (typeof packets !== 'undefined' && selectedId) ? packets[selectedId] : null;
          const scene = packet && packet.scene;
          const app = document.querySelector('#app');
          const onboard = document.querySelector('#onboard');
          const claim = document.querySelector('#placement-claim');
          const cesium = document.querySelector('#cesium');
          const map = document.querySelector('#quick-map');
          return {
            mission: typeof mission === 'undefined' ? null : mission,
            selectedId: typeof selectedId === 'undefined' ? null : selectedId,
            sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
            onboardHidden: Boolean(onboard && onboard.classList.contains('hidden')),
            appHidden: Boolean(app && app.classList.contains('hidden')),
            confirmDisabled: Boolean(document.querySelector('#confirm')?.disabled),
            futureDisabled: Boolean(document.querySelector('#mode-future')?.disabled),
            padDisabled: Boolean(document.querySelector('#mode-pad')?.disabled),
            pastDisabled: Boolean(document.querySelector('#mode-past')?.disabled),
            context: document.querySelector('#context-tag')?.textContent || '',
            status: document.querySelector('#status')?.textContent || '',
            verdict: document.querySelector('#verdict')?.textContent || '',
            placement: claim?.textContent || '',
            placementClaim: claim?.dataset.claim || '',
            quickMapHidden: Boolean(map && map.classList.contains('hidden')),
            cesiumSize: cesium ? {w: cesium.clientWidth, h: cesium.clientHeight} : null,
            canvasCount: document.querySelectorAll('canvas').length,
            modelReady: Boolean(typeof conceptModel !== 'undefined' && conceptModel && conceptModel.ready),
            meshReady: Boolean(typeof meshContentReady !== 'undefined' && meshContentReady),
            tileContent: Number(tileset?._statistics?.numberOfTilesWithContentReady || 0),
            futureClaim: scene?.future?.claim || null,
            padClaim: scene?.assumed_pad?.claim || null,
            pastKind: scene?.past?.kind || null,
            packetCount: Object.keys(packets || {}).length,
          };
        })()""",
    )


def _encode(frames: list[Path], dest: Path) -> None:
    if not frames:
        raise BrowserSmokeError("no frames to encode")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise BrowserSmokeError("ffmpeg was not found on PATH")
    list_file = dest.with_suffix(".txt")
    lines = []
    for frame in frames:
        lines.append(f"file '{frame.resolve()}'\n")
        lines.append("duration 0.35\n")
    lines.append(f"file '{frames[-1].resolve()}'\n")
    list_file.write_text("".join(lines))
    subprocess.run(
        [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-vsync", "vfr", "-pix_fmt", "yuv420p", "-c:v", "libx264",
            "-crf", "23", "-movflags", "+faststart", str(dest),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    notes: list[str] = []
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="expedition-flow-") as profile:
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
            _wait_js(cdp, "document.readyState === 'complete' && document.querySelectorAll('#tiles .tile').length === 5")
            _grab(cdp, frames, args.output_dir, "01-onboard")

            _evaluate(cdp, "pickMission('warehouse')")
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            _grab(cdp, frames, args.output_dir, "02-warehouse-plan")

            _evaluate(cdp, "(async () => { await confirmPlan(); return true; })()", await_promise=True)
            _wait_js(cdp, "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')")
            time.sleep(0.8)
            _grab(cdp, frames, args.output_dir, "03-board-before-run")
            notes.append("after_confirm:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "document.querySelector('#run-all').click()")
            deadline = time.monotonic() + 50
            while time.monotonic() < deadline:
                _grab(cdp, frames, args.output_dir)
                state = _state(cdp)
                if state.get("packetCount", 0) >= 4 and not _evaluate(cdp, "Boolean(document.querySelector('#run-all')?.disabled)"):
                    break
                time.sleep(0.45)
            time.sleep(1.4)
            _grab(cdp, frames, args.output_dir, "04-after-run")
            notes.append("after_run:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "selectSite('san_leon', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'san_leon' && Boolean(packets.san_leon)")
            _evaluate(cdp, "applyMode('past')")
            time.sleep(1.4)
            _grab(cdp, frames, args.output_dir, "05-past")
            notes.append("05-past:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "selectSite('san_marcos_tx', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'san_marcos_tx'")
            _evaluate(cdp, "applyMode('mesh')")
            time.sleep(8.0)
            _grab(cdp, frames, args.output_dir, "06-today-3d")
            notes.append("06-today-3d:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "applyMode('pad')")
            time.sleep(1.8)
            _grab(cdp, frames, args.output_dir, "07-pad")
            notes.append("07-pad:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "selectSite('san_leon', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'san_leon'")
            _evaluate(cdp, "applyMode('future')")
            time.sleep(2.4)
            _grab(cdp, frames, args.output_dir, "08-future-san-leon")
            notes.append("08-future:" + json.dumps(_state(cdp), default=str))

            _evaluate(cdp, "selectSite('san_marcos_tx', {fly: true, duration: 0})")
            _wait_js(cdp, "selectedId === 'san_marcos_tx'")
            _evaluate(cdp, "applyMode('future')")
            time.sleep(2.4)
            _grab(cdp, frames, args.output_dir, "09-future-san-marcos")
            notes.append("san_marcos_future:" + json.dumps(_state(cdp), default=str))

            _evaluate(
                cdp,
                """(() => {
                  const box = document.querySelector('#show-interior');
                  if (box) {
                    box.checked = true;
                    box.dispatchEvent(new Event('change', {bubbles: true}));
                  }
                  return {
                    interior: Boolean(box && box.checked),
                    cadHidden: Boolean(document.querySelector('#concept-cad')?.hidden),
                    cadText: document.querySelector('#concept-cad')?.innerText || '',
                    preset: document.querySelector('#concept-preset')?.selectedOptions?.[0]?.textContent || '',
                    rail: document.querySelector('#rail')?.innerText || '',
                    gaps: document.querySelector('#gaps')?.innerText || '',
                    scout: document.querySelector('#scout-followups')?.innerText || '',
                  };
                })()""",
            )
            time.sleep(2.6)
            _grab(cdp, frames, args.output_dir, "11-future-interior")
            notes.append("san_marcos_interior:" + json.dumps(_state(cdp), default=str))
            notes.append(
                "san_marcos_studio:"
                + json.dumps(
                    _evaluate(
                        cdp,
                        """(() => ({
                          interior: Boolean(document.querySelector('#show-interior')?.checked),
                          cadHidden: Boolean(document.querySelector('#concept-cad')?.hidden),
                          cadText: document.querySelector('#concept-cad')?.innerText || '',
                          preset: document.querySelector('#concept-preset')?.value || '',
                          presetLabel: document.querySelector('#concept-preset')?.selectedOptions?.[0]?.textContent || '',
                          note: document.querySelector('#concept-note')?.textContent || '',
                          rail: document.querySelector('#rail')?.innerText || '',
                          scout: document.querySelector('#scout-followups')?.innerText || '',
                          scorecard: document.querySelector('#scorecard')?.innerText || '',
                        }))()""",
                    ),
                    default=str,
                )
            )

            _evaluate(cdp, "applyMode('pad')")
            time.sleep(1.6)
            _grab(cdp, frames, args.output_dir, "10-pad-san-marcos")
        finally:
            if cdp:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    video = args.output_dir / "warehouse-user-flow.mp4"
    _encode(frames, video)
    report = {
        "ok": True,
        "elapsed_s": round(time.time() - started, 3),
        "frame_count": len(frames),
        "video": str(video),
        "stills": sorted(str(path) for path in (args.output_dir / "stills").glob("*.png")),
        "notes": notes,
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"ok": True, "video": str(video), "frames": len(frames), "stills": len(report["stills"])}))
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
