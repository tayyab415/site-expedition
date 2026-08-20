"""Before/after stills and a headed click-through for the Place → Scout → Screen → Sketch board.

Before stills are copied from the Keep/Pass session (this tree, earlier today).
After stills and the video are the current working tree.

    PYTHONPATH=. python3 -m expedition.verify.workflow_walk
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
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
from expedition.verify.feature_record import (
    Recorder,
    _mouse,
    click,
    ensure_deck_open,
    ensure_rail_open,
)
from expedition.verify.flow_record import _encode


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SWIPE = ROOT / "var" / "flow-recordings" / "swipe-session"
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "workflow-session"
NOTES: list[dict[str, Any]] = []

BEFORE_COPIES = (
    ("stills/after-01-onboard.png", "stills/before-01-onboard.png"),
    ("stills/after-02-plan.png", "stills/before-02-plan.png"),
    ("stills/after-03-board.png", "stills/before-03-board.png"),
    ("stills/after-05-pass.png", "stills/before-04-pass.png"),
    ("stills/after-09-run-pass.png", "stills/before-05-after-run.png"),
    ("stills/after-10-san-leon-reject.png", "stills/before-06-san-leon.png"),
    ("crops/after-03-board.png", "crops/before-03-board.png"),
    ("crops/after-05-pass.png", "crops/before-04-pass.png"),
    ("crops/after-09-run-pass.png", "crops/before-05-after-run.png"),
    ("crops/after-10-san-leon-reject.png", "crops/before-06-san-leon.png"),
)


def log(step: str, **extra: Any) -> None:
    row = {"step": step, **extra}
    NOTES.append(row)
    print("·", step, json.dumps(extra, default=str)[:240], flush=True)


def copy_before(output: Path) -> None:
    for rel_src, rel_dst in BEFORE_COPIES:
        src = SWIPE / rel_src
        dest = output / rel_dst
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not src.is_file():
            log("before-missing", src=str(src))
            continue
        shutil.copy2(src, dest)
        log("before-copy", dest=rel_dst, bytes=dest.stat().st_size)


def workflow_state(cdp: DevToolsConnection) -> dict[str, Any]:
    return _evaluate(
        cdp,
        """(() => {
          const cards = [...document.querySelectorAll('#cards .card')];
          const beats = [...document.querySelectorAll('#beat-strip .beat')].map((el) => ({
            beat: el.dataset.beat,
            on: el.classList.contains('on'),
            done: el.classList.contains('done'),
            text: el.textContent.trim(),
          }));
          const place = [...document.querySelectorAll('.place-beats li')].map((el) => ({
            on: el.classList.contains('on'),
            text: el.textContent.trim(),
          }));
          return {
            title: document.title,
            onboardTitle: document.querySelector('#onboard-title')?.textContent || '',
            onboardKicker: document.querySelector('#onboard-kicker')?.textContent || '',
            onboardLede: document.querySelector('#onboard-lede')?.textContent || '',
            confirm: document.querySelector('#confirm')?.textContent?.trim() || '',
            confirmDisabled: Boolean(document.querySelector('#confirm')?.disabled),
            entryFind: document.querySelector('#entry-find')?.classList.contains('on'),
            entryCheck: document.querySelector('#entry-check')?.classList.contains('on'),
            checkHidden: Boolean(document.querySelector('#check-entry')?.hidden),
            planCard: (document.querySelector('#plan-card')?.innerText || '').replace(/\\s+/g, ' ').trim(),
            placeBeats: place,
            boardTitle: document.querySelector('#board-title')?.textContent || '',
            nextMove: document.querySelector('#next-move')?.textContent || '',
            runAll: document.querySelector('#run-all')?.textContent?.trim() || '',
            runDisabled: Boolean(document.querySelector('#run-all')?.disabled),
            compareWait: document.querySelector('#compare-wait')?.textContent || '',
            compareWaitHidden: Boolean(document.querySelector('#compare-wait')?.hidden),
            story: document.querySelector('#story')?.textContent || '',
            status: document.querySelector('#status')?.textContent || '',
            credits: document.querySelector('#credits')?.textContent || '',
            verdict: document.querySelector('#verdict')?.textContent || '',
            face: (document.querySelector('#swipe-face')?.innerText || '').replace(/\\s+/g, ' ').trim(),
            beats,
            dataBeat: document.querySelector('#app')?.dataset.beat || '',
            cards: cards.length,
            ids: cards.map((c) => c.dataset.id),
            passed: cards.filter((c) => c.classList.contains('passed')).map((c) => c.dataset.id),
            reject: cards.filter((c) => c.classList.contains('reject')).map((c) => c.dataset.id),
            selectedId: typeof selectedId === 'undefined' ? null : selectedId,
            mission: typeof mission === 'undefined' ? null : mission,
            boardBeat: typeof boardBeat === 'undefined' ? null : boardBeat,
            entryPath: typeof entryPath === 'undefined' ? null : entryPath,
            screened: typeof packets === 'undefined' ? [] : Object.keys(packets),
            sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
            appHidden: Boolean(document.querySelector('#app')?.classList.contains('hidden')),
            onboardHidden: Boolean(document.querySelector('#onboard')?.classList.contains('hidden')),
          };
        })()""",
    )


def snap(cdp: DevToolsConnection, output: Path, name: str, *, dock: int | None = None, top: int | None = None) -> Path:
    stills = output / "stills"
    stills.mkdir(parents=True, exist_ok=True)
    path = stills / f"{name}.png"
    _screenshot(cdp, path)
    extra: dict[str, Any] = {"bytes": path.stat().st_size}
    try:
        from PIL import Image

        im = Image.open(path)
        extra["size"] = list(im.size)
        if dock:
            crops = output / "crops"
            crops.mkdir(parents=True, exist_ok=True)
            w, h = im.size
            im.crop((0, max(0, h - dock), w, h)).save(crops / f"{name}.png")
        if top:
            crops = output / "crops"
            crops.mkdir(parents=True, exist_ok=True)
            w, _h = im.size
            im.crop((0, 0, w, top)).save(crops / f"{name}-top.png")
    except Exception as exc:
        extra["crop_error"] = str(exc)
    log("snap", name=name, **extra)
    return path


def launch_browser(*, base_url: str, headless: bool, display: str | None) -> tuple[subprocess.Popen, DevToolsConnection, str]:
    port = _free_port()
    profile = tempfile.mkdtemp(prefix="workflow-walk-")
    env = os.environ.copy()
    if display:
        env["DISPLAY"] = display
    cmd = [
        _chromium_binary(None),
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
    ]
    if headless:
        cmd.insert(1, "--headless=new")
        cmd.append(base_url)
    else:
        cmd.insert(1, "--kiosk")
        cmd.insert(2, "--test-type")
        cmd.insert(3, "--disable-infobars")
        cmd.append(f"--app={base_url}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    page = _wait_for_page(port, timeout=40)
    cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
    for domain in ("Page.enable", "Runtime.enable"):
        cdp.call(domain)
    if headless:
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
        )
    return proc, cdp, profile


def kill_browser(proc: subprocess.Popen, cdp: DevToolsConnection | None, profile: str) -> None:
    if cdp:
        try:
            cdp.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    shutil.rmtree(profile, ignore_errors=True)


def wait_onboard(cdp: DevToolsConnection) -> None:
    _wait_js(cdp, "document.readyState === 'complete' && document.querySelectorAll('#tiles .tile').length === 5")
    _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
    time.sleep(0.4)


def confirm_warehouse(cdp: DevToolsConnection) -> None:
    click(cdp, '.tile[data-id="warehouse"]')
    _wait_js(cdp, "Boolean(plan) && mission === 'warehouse' && !document.querySelector('#confirm').disabled")
    time.sleep(0.25)
    click(cdp, "#confirm")
    _wait_js(
        cdp,
        "!document.querySelector('#app').classList.contains('hidden') && document.querySelectorAll('#cards .card').length >= 2",
    )
    try:
        _wait_js(
            cdp,
            "Boolean(document.querySelector('#swipe-photo img')?.naturalWidth) || !document.querySelector('#swipe-face')",
            timeout=8,
        )
    except BrowserSmokeError:
        pass
    ensure_deck_open(cdp)
    ensure_rail_open(cdp)
    time.sleep(0.5)


def start_local_server() -> tuple[subprocess.Popen, str]:
    port = _free_port()
    log_path = DEFAULT_OUTPUT / "local-server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["EXPEDITION_DISABLE_AUTH"] = "1"
    env["EXPEDITION_BIND_HOST"] = "127.0.0.1"
    env["PYTHONPATH"] = str(REPO)
    env.pop("EXPEDITION_TRUST_PROXY", None)
    script = (
        "import os\n"
        "from expedition.ui import serve\n"
        f"serve.PORT = {port}\n"
        "serve.main()\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=str(REPO),
        env=env,
        stdout=log_path.open("w"),
        stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}"
    last = ""
    for _ in range(80):
        if proc.poll() is not None:
            raise RuntimeError(f"local serve exited: {log_path.read_text()[-800:]}")
        try:
            with urllib.request.urlopen(url + "/api/session", timeout=1) as resp:
                if resp.status == 200:
                    log("local-server", url=url)
                    return proc, url
        except Exception as exc:
            last = str(exc)
        time.sleep(0.15)
    raise RuntimeError(f"local serve did not answer: {last}")


class GrabRecorder(Recorder):
    def start(self, name: str) -> None:
        self.stop()
        self.current = name
        dest = self.clips / f"{name}.mp4"
        if dest.exists():
            dest.unlink()
        self.fallback_frames = []
        if not self.display:
            return
        log_path = self.output / "ffmpeg-x11grab.log"
        self.proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-f", "x11grab", "-draw_mouse", "1", "-video_size", "1440x1000",
                "-framerate", "12", "-i", self.display,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                "-crf", "20", "-movflags", "+faststart", str(dest),
            ],
            stdout=subprocess.DEVNULL,
            stderr=log_path.open("w"),
        )
        time.sleep(0.7)
        if self.proc.poll() is not None:
            self.proc = None


def hold(cdp: DevToolsConnection, rec: GrabRecorder, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        rec.grab(cdp)
        time.sleep(0.4)


def mark(clock0: float, name: str, **extra: Any) -> None:
    log("chapter", t=round(time.monotonic() - clock0, 1), name=name, **extra)


def capture_after_stills(base_url: str, output: Path) -> dict[str, Any]:
    proc, cdp, profile = launch_browser(base_url=base_url, headless=True, display=None)
    shots: dict[str, Any] = {}
    try:
        wait_onboard(cdp)
        shots["onboard"] = workflow_state(cdp)
        snap(cdp, output, "after-01-onboard", top=520)
        click(cdp, '.tile[data-id="farm"]')
        _wait_js(cdp, "mission === 'farm'")
        time.sleep(0.3)
        shots["farm"] = workflow_state(cdp)
        snap(cdp, output, "after-02-farm", top=520)
        click(cdp, '.tile[data-id="warehouse"]')
        _wait_js(cdp, "mission === 'warehouse'")
        click(cdp, "#entry-check")
        _wait_js(cdp, "entryPath === 'check' && !document.querySelector('#check-entry')?.hidden")
        time.sleep(0.25)
        shots["check"] = workflow_state(cdp)
        snap(cdp, output, "after-03-check", top=720)
        click(cdp, "#entry-find")
        _wait_js(cdp, "entryPath === 'find'")
        confirm_warehouse(cdp)
        shots["scout"] = workflow_state(cdp)
        snap(cdp, output, "after-04-scout", dock=360)
        click(cdp, '#cards .card[data-id="alliance_tx"]')
        time.sleep(0.4)
        click(cdp, "#pass-site")
        time.sleep(0.4)
        shots["pass"] = workflow_state(cdp)
        snap(cdp, output, "after-05-pass", dock=360)
        click(cdp, "#run-all")
        time.sleep(0.25)
        shots["screening"] = workflow_state(cdp)
        snap(cdp, output, "after-06-screening", dock=360)
        _wait_js(
            cdp,
            "Boolean(packets && packets.san_leon) && !document.querySelector('#run-all').disabled",
            timeout=180,
        )
        time.sleep(0.8)
        shots["compare"] = workflow_state(cdp)
        snap(cdp, output, "after-07-compare", dock=360)
        click(cdp, '#cards .card[data-id="san_leon"]')
        time.sleep(0.6)
        shots["san_leon"] = workflow_state(cdp)
        snap(cdp, output, "after-08-san-leon", dock=360)
        click(cdp, '#cards .card[data-id="san_marcos_tx"]')
        _wait_js(cdp, "selectedId === 'san_marcos_tx'", timeout=8)
        time.sleep(0.5)
        future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
        deadline = time.monotonic() + 10
        while not future_ready and time.monotonic() < deadline:
            time.sleep(0.3)
            future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
        if future_ready:
            click(cdp, "#mode-future")
            time.sleep(1.4)
        shots["sketch"] = workflow_state(cdp)
        snap(cdp, output, "after-09-sketch", dock=360)
        try:
            click(cdp, "#show-interior")
            time.sleep(1.2)
        except BrowserSmokeError as exc:
            log("interior-miss", error=str(exc))
        shots["interior"] = workflow_state(cdp)
        snap(cdp, output, "after-10-interior")
    finally:
        kill_browser(proc, cdp, profile)
    return shots


def record_video(base_url: str, output: Path, display: str) -> dict[str, Any]:
    rec = GrabRecorder(output, display)
    proc, cdp, profile = launch_browser(base_url=base_url, headless=False, display=display)
    clock0 = time.monotonic()
    try:
        wait_onboard(cdp)
        rec.start("warehouse-clickthrough")
        hold(cdp, rec, 2.4)
        rec.grab(cdp, "video-01-onboard")
        mark(clock0, "onboard", **workflow_state(cdp))

        click(cdp, '.tile[data-id="farm"]')
        _wait_js(cdp, "mission === 'farm'")
        hold(cdp, rec, 2.4)
        rec.grab(cdp, "video-02-farm")
        mark(clock0, "farm")

        click(cdp, '.tile[data-id="home"]')
        _wait_js(cdp, "mission === 'home'")
        hold(cdp, rec, 1.8)
        click(cdp, '.tile[data-id="data_center"]')
        _wait_js(cdp, "mission === 'data_center'")
        hold(cdp, rec, 1.8)
        rec.grab(cdp, "video-03-data-hall")
        mark(clock0, "other-missions")

        click(cdp, '.tile[data-id="warehouse"]')
        _wait_js(cdp, "mission === 'warehouse'")
        hold(cdp, rec, 1.2)
        click(cdp, "#entry-check")
        _wait_js(cdp, "entryPath === 'check'")
        hold(cdp, rec, 2.6)
        rec.grab(cdp, "video-04-check")
        mark(clock0, "check")

        click(cdp, "#entry-find")
        _wait_js(cdp, "entryPath === 'find'")
        hold(cdp, rec, 1.0)
        click(cdp, "#confirm")
        _wait_js(
            cdp,
            "!document.querySelector('#app').classList.contains('hidden') && document.querySelectorAll('#cards .card').length >= 2",
        )
        try:
            _wait_js(cdp, "Boolean(document.querySelector('#swipe-photo img')?.naturalWidth)", timeout=8)
        except BrowserSmokeError:
            pass
        ensure_deck_open(cdp)
        ensure_rail_open(cdp)
        hold(cdp, rec, 3.6)
        rec.grab(cdp, "video-05-scout")
        mark(clock0, "scout", **{k: workflow_state(cdp)[k] for k in ("boardTitle", "runAll", "nextMove", "dataBeat")})

        click(cdp, '#cards .card[data-id="alliance_tx"]')
        hold(cdp, rec, 2.0)
        rec.grab(cdp, "video-06-alliance")
        click(cdp, "#pass-site")
        hold(cdp, rec, 2.2)
        rec.grab(cdp, "video-07-pass")
        mark(clock0, "pass", passed=workflow_state(cdp).get("passed"))

        click(cdp, "#run-all")
        mark(clock0, "screen-start")
        deadline = time.monotonic() + 180
        ready = False
        while time.monotonic() < deadline:
            rec.grab(cdp)
            ready = bool(
                _evaluate(
                    cdp,
                    "Boolean(packets && packets.san_leon) && !document.querySelector('#run-all').disabled",
                )
            )
            if ready:
                break
            time.sleep(0.45)
        hold(cdp, rec, 3.2)
        rec.grab(cdp, "video-08-compare")
        mark(clock0, "compare", **workflow_state(cdp))

        try:
            click(cdp, '#cards .card[data-id="san_leon"]')
            hold(cdp, rec, 2.8)
            rec.grab(cdp, "video-09-san-leon")
            mark(clock0, "san-leon")
        except BrowserSmokeError:
            hold(cdp, rec, 1.0)

        try:
            click(cdp, '#cards .card[data-id="san_marcos_tx"]')
            _wait_js(cdp, "selectedId === 'san_marcos_tx'", timeout=8)
            hold(cdp, rec, 2.0)
            click(cdp, "#mode-today")
            hold(cdp, rec, 1.6)
            rec.grab(cdp, "video-10-today")
            future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
            wait_until = time.monotonic() + 10
            while not future_ready and time.monotonic() < wait_until:
                rec.grab(cdp)
                time.sleep(0.4)
                future_ready = bool(_evaluate(cdp, "!Boolean(document.querySelector('#mode-future')?.disabled)"))
            if future_ready:
                click(cdp, "#mode-future")
                hold(cdp, rec, 5.0)
            rec.grab(cdp, "video-11-sketch")
            mark(clock0, "sketch", **workflow_state(cdp))
            try:
                click(cdp, "#show-interior")
                hold(cdp, rec, 4.5)
                rec.grab(cdp, "video-12-interior")
                mark(clock0, "interior")
            except BrowserSmokeError as exc:
                log("video-interior-miss", error=str(exc))
        except BrowserSmokeError as exc:
            log("video-san-marcos-miss", error=str(exc))
            hold(cdp, rec, 2.0)

        try:
            click(cdp, "#beat-strip .beat[data-beat='scout']")
            hold(cdp, rec, 2.0)
            rec.grab(cdp, "video-13-back-scout")
            mark(clock0, "back-scout")
        except BrowserSmokeError:
            hold(cdp, rec, 1.0)
        hold(cdp, rec, 1.6)
        rec.stop()
    except Exception:
        rec.stop()
        raise
    finally:
        kill_browser(proc, cdp, profile)

    clip = output / "clips" / "warehouse-clickthrough.mp4"
    final = output / "warehouse-clickthrough.mp4"
    if clip.is_file() and clip.stat().st_size > 2000:
        shutil.copy2(clip, final)
    elif rec.fallback_frames:
        _encode(rec.fallback_frames, final)
        log("video-fallback-frames", count=len(rec.fallback_frames))
    log("video", path=str(final), bytes=final.stat().st_size if final.is_file() else 0)
    return {"video": str(final), "bytes": final.stat().st_size if final.is_file() else 0}


def start_xvfb(display: str) -> subprocess.Popen | None:
    n = display.lstrip(":")
    lock = Path(f"/tmp/.X{n}-lock")
    if lock.exists():
        log("xvfb-reuse", display=display)
        return None
    proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", "1440x1000x24", "-ac", "+extension", "RANDR", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        if proc.poll() is not None:
            raise RuntimeError("Xvfb exited")
        if lock.exists():
            time.sleep(0.25)
            return proc
        time.sleep(0.1)
    return proc


def sample_video(path: Path, dest_dir: Path) -> list[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        duration = float((probe.stdout or "0").strip() or 0)
    except ValueError:
        duration = 0.0
    stamps = [1, 8, 16, 28, 40, 55]
    if duration > 70:
        stamps.extend([int(duration * 0.55), int(duration * 0.72), int(duration * 0.88), max(1, int(duration) - 3)])
    names = []
    for t in stamps:
        if duration and t >= duration:
            continue
        out = dest_dir / f"t{t:03d}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-q:v", "3", str(out)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if out.is_file() and out.stat().st_size > 2000:
            names.append(out.name)
            log("video-frame", t=t, bytes=out.stat().st_size)
    log("video-duration", seconds=round(duration, 1), frames=names)
    return names


def mean_luma(path: Path) -> float:
    from PIL import Image

    im = Image.open(path).convert("L").resize((160, 100))
    pixels = list(im.getdata())
    return round(sum(pixels) / max(1, len(pixels)), 1)


def verify_artifacts(output: Path, shots: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(ok: bool, name: str, detail: Any) -> None:
        checks.append({"ok": ok, "name": name, "detail": detail})

    onboard = shots.get("onboard") or {}
    add("Find warehouse places" in (onboard.get("onboardTitle") or ""), "onboard-title", onboard.get("onboardTitle"))
    add((onboard.get("confirm") or "") == "Show matching places", "confirm-label", onboard.get("confirm"))
    add(bool(onboard.get("entryFind")), "find-default", onboard.get("entryFind"))
    farm = shots.get("farm") or {}
    add("Find farm places" in (farm.get("onboardTitle") or ""), "farm-title", farm.get("onboardTitle"))
    check = shots.get("check") or {}
    add(check.get("entryCheck") is True and check.get("checkHidden") is False, "check-panel", check.get("checkHidden"))
    scout = shots.get("scout") or {}
    add((scout.get("boardTitle") or "") == "Scout", "scout-title", scout.get("boardTitle"))
    add("Screen" in (scout.get("runAll") or "") and "Expedition" not in (scout.get("runAll") or ""), "run-label", scout.get("runAll"))
    add((scout.get("dataBeat") or "") == "scout", "data-beat", scout.get("dataBeat"))
    passed = (shots.get("pass") or {}).get("passed") or []
    add("alliance_tx" in passed, "pass-alliance", passed)
    compare = shots.get("compare") or {}
    add("san_leon" in (compare.get("screened") or []), "screened-san-leon", compare.get("screened"))
    add("alliance_tx" not in (compare.get("screened") or []), "alliance-not-screened", compare.get("screened"))
    add("alliance_tx" in (compare.get("passed") or []), "alliance-stayed-passed", compare.get("passed"))
    san = shots.get("san_leon") or {}
    add("san_leon" in (san.get("reject") or []), "san-leon-reject", san.get("reject"))
    add("alliance_tx" not in (san.get("reject") or []), "pass-is-not-reject", {"passed": san.get("passed"), "reject": san.get("reject")})
    credits = (compare.get("credits") or scout.get("credits") or "")
    add("245" in credits and "20000" in credits, "credits-replay", credits)
    sketch = shots.get("sketch") or {}
    add((sketch.get("dataBeat") or sketch.get("boardBeat") or "") in {"sketch", "compare"}, "sketch-beat", sketch.get("dataBeat"))

    stills = list((output / "stills").glob("after-*.png"))
    add(len(stills) >= 8, "after-still-count", len(stills))
    dark = []
    for path in stills:
        try:
            luma = mean_luma(path)
            if luma < 8:
                dark.append({"name": path.name, "luma": luma})
        except Exception as exc:
            dark.append({"name": path.name, "error": str(exc)})
    add(not dark, "stills-not-black", dark)

    video = output / "warehouse-clickthrough.mp4"
    add(video.is_file() and video.stat().st_size > 50_000, "video-bytes", video.stat().st_size if video.is_file() else 0)
    frames = sample_video(video, output / "video-frames") if video.is_file() else []
    frame_dark = []
    for name in frames:
        path = output / "video-frames" / name
        try:
            luma = mean_luma(path)
            if luma < 8:
                frame_dark.append({"name": name, "luma": luma})
        except Exception as exc:
            frame_dark.append({"name": name, "error": str(exc)})
    add(bool(frames) and not frame_dark, "video-not-black", {"frames": frames, "dark": frame_dark})

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
    parser.add_argument("--display", default=":95")
    parser.add_argument("--skip-video", action="store_true")
    parser.add_argument("--skip-stills", action="store_true")
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "stills").mkdir(exist_ok=True)
    (output / "crops").mkdir(exist_ok=True)
    (output / "clips").mkdir(exist_ok=True)

    copy_before(output)
    server = None
    xvfb = None
    base_url = args.base_url
    shots: dict[str, Any] = {}
    report: dict[str, Any] = {"ok": False, "failed": ["did-not-run"]}
    try:
        if not base_url:
            server, base_url = start_local_server()
        if not args.skip_stills:
            shots = capture_after_stills(base_url, output)
            (output / "after-state.json").write_text(json.dumps(shots, indent=2, default=str) + "\n")
        else:
            state_path = output / "after-state.json"
            if state_path.is_file():
                shots = json.loads(state_path.read_text())
        if not args.skip_video:
            xvfb = start_xvfb(args.display)
            os.environ["DISPLAY"] = args.display
            record_video(base_url, output, args.display)
        report = verify_artifacts(output, shots)
    finally:
        (output / "notes.json").write_text(json.dumps(NOTES, indent=2, default=str) + "\n")
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
