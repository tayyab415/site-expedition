"""UI walk for Find places (OSM map search) and I have a place.

    PYTHONPATH=. python3 -m expedition.verify.discover_walk
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import time
from pathlib import Path
from typing import Any

from expedition.verify.browser_smoke import BrowserSmokeError, _evaluate, _wait_js
from expedition.verify.feature_record import click, type_text
from expedition.verify.workflow_walk import (
    GrabRecorder,
    hold,
    kill_browser,
    launch_browser,
    log,
    sample_video,
    snap,
    start_local_server,
    start_xvfb,
    wait_onboard,
    workflow_state,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "discover-session"


def capture_stills(base_url: str, output: Path) -> dict[str, Any]:
    proc, cdp, profile = launch_browser(base_url=base_url, headless=True, display=None)
    shots: dict[str, Any] = {}
    try:
        wait_onboard(cdp)
        shots["onboard"] = workflow_state(cdp)
        snap(cdp, output, "01-find-onboard", top=560)

        click(cdp, "#entry-check")
        _wait_js(cdp, "entryPath === 'check' && !document.querySelector('#check-entry')?.hidden")
        time.sleep(0.3)
        shots["check"] = workflow_state(cdp)
        snap(cdp, output, "02-have-a-place", top=720)

        click(cdp, "#entry-find")
        _wait_js(cdp, "entryPath === 'find'")
        type_text(cdp, "#look-query", "Chicago, IL")
        time.sleep(0.4)
        shots["chicago_typed"] = workflow_state(cdp)
        snap(cdp, output, "03-chicago-typed", top=560)

        click(cdp, "#confirm")
        _wait_js(cdp, "!document.querySelector('#app').classList.contains('hidden')", timeout=20)
        try:
            _wait_js(
                cdp,
                "extras.some((row) => row && row.source === 'openstreetmap') || document.querySelectorAll('#cards .card[data-id^=\"osm_\"]').length >= 3",
                timeout=28,
            )
        except BrowserSmokeError:
            log("osm-miss", state=workflow_state(cdp))
        time.sleep(1.2)
        shots["chicago_board"] = workflow_state(cdp)
        shots["chicago_board"]["osmIds"] = _evaluate(
            cdp,
            "extras.filter((row) => row && row.source === 'openstreetmap').map((row) => row.id)",
        )
        snap(cdp, output, "04-chicago-board", dock=360)
    finally:
        kill_browser(proc, cdp, profile)
    return shots


def record_video(base_url: str, output: Path, display: str) -> None:
    rec = GrabRecorder(output, display)
    proc, cdp, profile = launch_browser(base_url=base_url, headless=False, display=display)
    try:
        wait_onboard(cdp)
        rec.start("chicago-find")
        hold(cdp, rec, 2.0)
        rec.grab(cdp, "video-01-find")

        click(cdp, "#entry-check")
        _wait_js(cdp, "entryPath === 'check'")
        hold(cdp, rec, 2.2)
        rec.grab(cdp, "video-02-check")

        click(cdp, "#entry-find")
        _wait_js(cdp, "entryPath === 'find'")
        type_text(cdp, "#look-query", "Chicago, IL")
        hold(cdp, rec, 2.0)
        rec.grab(cdp, "video-03-typed")

        click(cdp, "#confirm")
        _wait_js(cdp, "!document.querySelector('#app').classList.contains('hidden')", timeout=20)
        hold(cdp, rec, 2.0)
        try:
            _wait_js(
                cdp,
                "extras.some((row) => row && row.source === 'openstreetmap')",
                timeout=28,
            )
        except BrowserSmokeError:
            pass
        hold(cdp, rec, 4.0)
        rec.grab(cdp, "video-04-board")
        rec.stop()
    except Exception:
        rec.stop()
        raise
    finally:
        kill_browser(proc, cdp, profile)

    clip = output / "clips" / "chicago-find.mp4"
    dest = output / "chicago-find.mp4"
    if clip.is_file() and clip.stat().st_size > 2000:
        shutil.copy2(clip, dest)
    log("video", path=str(dest), bytes=dest.stat().st_size if dest.is_file() else 0)


def verify(output: Path, shots: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(ok: bool, name: str, detail: Any) -> None:
        checks.append({"ok": bool(ok), "name": name, "detail": detail})

    onboard = shots.get("onboard") or {}
    add("Find warehouse places" in (onboard.get("onboardTitle") or ""), "find-title", onboard.get("onboardTitle"))
    add(bool(onboard.get("entryFind")), "find-default", onboard.get("entryFind"))
    add((onboard.get("confirm") or "") == "Show matching places", "confirm-find", onboard.get("confirm"))

    check = shots.get("check") or {}
    add(check.get("entryCheck") is True and check.get("checkHidden") is False, "check-panel", check.get("checkHidden"))
    add("Check this warehouse" in (check.get("onboardTitle") or ""), "check-title", check.get("onboardTitle"))

    board = shots.get("chicago_board") or {}
    ids = board.get("ids") or []
    osm = [item for item in (board.get("osmIds") or ids) if str(item).startswith("osm_")]
    add(len(osm) >= 3, "chicago-osm-cards", {"osm": len(osm), "ids": ids[:16], "cards": board.get("cards"), "status": board.get("status")})
    add("san_leon" not in ids and "alliance_tx" not in ids, "texas-pins-out", ids)
    add(board.get("onboardHidden") is True and board.get("appHidden") is False, "board-open", board.get("boardTitle"))

    video = output / "chicago-find.mp4"
    stills = list((output / "stills").glob("*.png"))
    add(len(stills) >= 4, "still-count", len(stills))
    add(video.is_file() and video.stat().st_size > 40_000, "video-bytes", video.stat().st_size if video.is_file() else 0)
    if video.is_file():
        sample_video(video, output / "video-frames")

    report = {
        "ok": all(row["ok"] for row in checks),
        "checks": checks,
        "failed": [row["name"] for row in checks if not row["ok"]],
    }
    (output / "verify.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    log("verify", ok=report["ok"], failed=report["failed"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--display", default=":96")
    parser.add_argument("--skip-video", action="store_true")
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "stills").mkdir(exist_ok=True)

    server = None
    xvfb = None
    base_url = args.base_url
    shots: dict[str, Any] = {}
    report: dict[str, Any] = {"ok": False, "failed": ["did-not-run"]}
    try:
        if not base_url:
            server, base_url = start_local_server()
        shots = capture_stills(base_url, output)
        (output / "after-state.json").write_text(json.dumps(shots, indent=2, default=str) + "\n")
        if not args.skip_video:
            xvfb = start_xvfb(args.display)
            os.environ["DISPLAY"] = args.display
            record_video(base_url, output, args.display)
        report = verify(output, shots)
    finally:
        if xvfb:
            xvfb.send_signal(signal.SIGTERM)
            try:
                xvfb.wait(timeout=4)
            except Exception:
                xvfb.kill()
        if server:
            server.send_signal(signal.SIGTERM)
            try:
                server.wait(timeout=6)
            except Exception:
                server.kill()
    print(json.dumps({"ok": report.get("ok"), "failed": report.get("failed"), "output": str(output)}))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
