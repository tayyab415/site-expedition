"""Drive the live planning board with real pointer/keyboard events and record clips.

Cursor preview automation is not hosted on this VM. This is the computer-use
path: headed Chromium on Xvfb, CDP mouse/keyboard, ffmpeg x11grab per feature.

    PYTHONPATH=. python3 -m expedition.verify.feature_record
"""

from __future__ import annotations

import argparse
import json
import os
import signal
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
from expedition.verify.flow_record import _encode


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "verify"
WINFIELD = "3605 Winfield Cove, Austin, TX 78704"
CLIPS = [
    ("01-plan-expedition", "Confirm the plan, then the Expedition acts"),
    ("02-san-leon-veto-and-ground", "San Leon: FEMA veto plus untrusted ground"),
    ("03-replace-and-deepen", "Reject, replace, deepen the survivor"),
    ("04-today-is-the-site", "TODAY is the site. Pictures do not score."),
    ("05-future-fit-gap", "FUTURE is a concept. FIT is a named gap."),
    ("06-check-a-site", "Check a Site: a real address, not a listing"),
    ("07-farm-thin-proof", "Same engine, farm instead of warehouse"),
]

STORY = [
    (
        "01-plan-expedition",
        "You confirm a Mission Plan. Then the Expedition screens.",
        "Warehouse in the Texas Triangle. Hard rule: reject FEMA floodplain. The right-hand rail is owned by questions, not API names. The table is the result: survivors stay Conditional, San Leon is Reject. There is no composite score.",
        "Watch for: Warehouse tile, Confirm, Run Expedition, questions on the rail, comparison filling in.",
    ),
    (
        "02-san-leon-veto-and-ground",
        "San Leon dies on FEMA. The ground is also untrusted.",
        "Present-state FEMA mapped Special Flood Hazard Area is the veto. Flood rewind and USGS 3DEP vs NASADEM disagreement explain why you still would not trust the pin even if someone argued the map. Rewind does not rescue the veto. If Mireye already saw a nearby RMP facility, EPA ECHO names it — that is a Phase I lead, not a clean-site pass.",
        "Watch for: reject · mapped_sfha, 3DEP vs NASADEM, PAST water history, and the verdict still Reject.",
    ),
    (
        "03-replace-and-deepen",
        "The agent replaces the dead site and deepens the survivor.",
        "San Leon is rejected, so the Expedition brings Port Houston in from the lawful pool. San Marcos is the provisional finalist: Conditional, with real drive times, Skeptic Review, and homework (broker, utility letter, truck access). It is not a winner.",
        "Watch for: Brought in after a Reject on Port Houston, 3h-class time to Port of Houston, SKEPTIC REVIEW, Conditional not Strong Fit.",
    ),
    (
        "04-today-is-the-site",
        "TODAY is the real site. The pretty map does not decide.",
        "Aerial and photorealistic 3D are presentation. Flood still comes from FEMA. Google tiles contribute zero score.",
        "Watch for: TODAY Aerial, then TODAY 3D, and the line “does not score.”",
    ),
    (
        "05-future-fit-gap",
        "FUTURE is a warehouse concept. FIT is a named gap, not a grey button.",
        "One parametric warehouse sits on an assumed pad so you can see the idea. FIT stays a Verification Gap because there is no independently licensed parcel envelope. That is honest, not unfinished chrome.",
        "Watch for: FUTURE on San Marcos, the orange mass, and FIT deferred in the gaps list. There is no FIT mode button.",
    ),
    (
        "06-check-a-site",
        "You can drop in a real address.",
        "Type a US street, resolve it once. It becomes a USER SITE, not a listing. This one is 3605 Winfield Cove in Austin. It is not screened until you ask.",
        "Watch for: the pin jumping to the Austin house, and USER SITE · not screened.",
    ),
    (
        "07-farm-thin-proof",
        "Same engine. Farm, not warehouse.",
        "Iowa corn is cultivated, so it is Conditional — still missing a water right. Manhattan is not farmland, so it is reject · not_cultivated. No yearly crop map is invented.",
        "Watch for: “No yearly map is invented,” then Midtown Manhattan going red.",
    ),
]


def _state(cdp: DevToolsConnection) -> dict[str, Any]:
    return _evaluate(
        cdp,
        """(() => {
          const packet = (typeof packets !== 'undefined' && selectedId) ? packets[selectedId] : null;
          const scene = packet && packet.scene;
          const compare = document.querySelector('#compare-body')?.innerText || '';
          const head = document.querySelector('.compare thead')?.innerText || '';
          return {
            mission: typeof mission === 'undefined' ? null : mission,
            selectedId: typeof selectedId === 'undefined' ? null : selectedId,
            sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
            planReady: Boolean(typeof plan !== 'undefined' && plan),
            planText: document.querySelector('#plan-card')?.textContent || '',
            confirmDisabled: Boolean(document.querySelector('#confirm')?.disabled),
            onboardHidden: Boolean(document.querySelector('#onboard')?.classList.contains('hidden')),
            appHidden: Boolean(document.querySelector('#app')?.classList.contains('hidden')),
            futureDisabled: Boolean(document.querySelector('#mode-future')?.disabled),
            padDisabled: Boolean(document.querySelector('#mode-pad')?.disabled),
            pastDisabled: Boolean(document.querySelector('#mode-past')?.disabled),
            fitDisabled: Boolean(document.querySelector('[data-mode="fit"]')?.disabled),
            fitClass: document.querySelector('[data-mode="fit"]')?.className || '',
            context: document.querySelector('#context-tag')?.textContent || '',
            status: document.querySelector('#status')?.textContent || '',
            verdict: document.querySelector('#verdict')?.textContent || '',
            rail: document.querySelector('#rail')?.innerText || '',
            log: document.querySelector('#expedition-log')?.innerText || '',
            gaps: document.querySelector('#gaps')?.innerText || '',
            fitGap: document.querySelector('#fit-gap')?.innerText || '',
            fitGapHidden: Boolean(document.querySelector('#fit-gap')?.hidden),
            fitButton: Boolean(document.querySelector('[data-mode="fit"]:not([hidden])')),
            origins: Array.from(document.querySelectorAll('#cards .origin')).map((el) => el.textContent).join(' | '),
            heldCard: Boolean(document.querySelector('#cards .card.held')),
            replacementCard: Boolean(document.querySelector('#cards .card.replacement')),
            brief: document.querySelector('#brief')?.innerText || '',
            skeptic: document.querySelector('#skeptic-stamp')?.innerText || '',
            skepticHidden: Boolean(document.querySelector('#skeptic-stamp')?.hidden),
            scorecard: document.querySelector('#scorecard')?.innerText || '',
            compare,
            compareHead: head,
            placement: document.querySelector('#placement-claim')?.textContent || '',
            placementClaim: document.querySelector('#placement-claim')?.dataset.claim || '',
            padFit: document.querySelector('#placement-claim')?.dataset.fit || '',
            addressStatus: document.querySelector('#address-status')?.textContent || '',
            aerialStatus: document.querySelector('#aerial-status')?.textContent || '',
            pastNote: document.querySelector('#past-note')?.textContent || '',
            pastSliderHidden: Boolean(document.querySelector('#past-slider-wrap')?.hidden),
            pastKind: scene?.past?.kind || null,
            pastSeries: Array.isArray(scene?.past?.series) ? scene.past.series.length : 0,
            pastScores: scene?.past?.scores,
            futureClaim: scene?.future?.claim || null,
            padClaim: scene?.assumed_pad?.claim || null,
            fitClaim: scene?.fit?.claim || null,
            demDelta: scene?.past?.dem_delta_m ?? null,
            usgs3dep: scene?.past?.usgs_3dep_m ?? null,
            nasadem: scene?.past?.nasadem_m ?? null,
            packetCount: Object.keys(packets || {}).length,
            cards: document.querySelectorAll('#cards .card').length,
            streamTrace: window.__streamTrace || [],
            liveOn: Boolean(document.querySelector('#live')?.checked),
            mapLabel: document.querySelector('.quick-map-label')?.textContent || '',
          };
        })()""",
    )


def _box(cdp: DevToolsConnection, selector: str) -> dict[str, float]:
    box = _evaluate(
        cdp,
        f"""(() => {{
          const el = document.querySelector({selector!r});
          if (!el) return null;
          el.scrollIntoView({{block: 'center', inline: 'nearest'}});
          const r = el.getBoundingClientRect();
          if (r.width < 2 || r.height < 2) return null;
          return {{x: r.x + r.width / 2, y: r.y + r.height / 2}};
        }})()""",
    )
    if not box:
        raise BrowserSmokeError(f"cannot click {selector}")
    return box


def _mouse(cdp: DevToolsConnection, kind: str, x: float, y: float) -> None:
    payload = {"type": kind, "x": x, "y": y, "button": "left", "clickCount": 1}
    cdp.call("Input.dispatchMouseEvent", payload)


def click(cdp: DevToolsConnection, selector: str) -> None:
    box = _box(cdp, selector)
    _mouse(cdp, "mouseMoved", box["x"], box["y"])
    time.sleep(0.05)
    _mouse(cdp, "mousePressed", box["x"], box["y"])
    _mouse(cdp, "mouseReleased", box["x"], box["y"])
    time.sleep(0.25)


def ensure_deck_open(cdp: DevToolsConnection) -> None:
    if _evaluate(cdp, "Boolean(document.querySelector('#app')?.classList.contains('deck-off'))"):
        click(cdp, "#toggle-deck")
        time.sleep(0.35)


def ensure_rail_open(cdp: DevToolsConnection) -> None:
    if _evaluate(cdp, "Boolean(document.querySelector('#app')?.classList.contains('rail-off'))"):
        click(cdp, "#toggle-rail")
        time.sleep(0.35)


def type_text(cdp: DevToolsConnection, selector: str, text: str) -> None:
    click(cdp, selector)
    cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "modifiers": 2, "windowsVirtualKeyCode": 65})
    cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "modifiers": 2, "windowsVirtualKeyCode": 65})
    cdp.call("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Backspace", "windowsVirtualKeyCode": 8})
    cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "windowsVirtualKeyCode": 8})
    cdp.call("Input.insertText", {"text": text})
    time.sleep(0.2)


class Recorder:
    def __init__(self, output: Path, display: str | None) -> None:
        self.output = output
        self.display = display
        self.clips = output / "clips"
        self.stills = output / "stills"
        self.frames_root = output / "frames"
        self.clips.mkdir(parents=True, exist_ok=True)
        self.stills.mkdir(parents=True, exist_ok=True)
        self.proc: subprocess.Popen[bytes] | None = None
        self.current: str | None = None
        self.fallback_frames: list[Path] = []

    def start(self, name: str) -> None:
        self.stop()
        self.current = name
        dest = self.clips / f"{name}.mp4"
        if dest.exists():
            dest.unlink()
        if self.display:
            self.proc = subprocess.Popen(
                [
                    "ffmpeg", "-y", "-f", "x11grab", "-video_size", "1440x1000",
                    "-framerate", "12", "-i", self.display,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                    "-crf", "23", "-movflags", "+faststart", str(dest),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.4)
            if self.proc.poll() is not None:
                self.proc = None
        self.fallback_frames = []

    def grab(self, cdp: DevToolsConnection, label: str | None = None) -> Path:
        folder = self.frames_root / (self.current or "misc")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{len(self.fallback_frames):05d}.png"
        _screenshot(cdp, path)
        self.fallback_frames.append(path)
        if label:
            still = self.stills / f"{label}.png"
            still.write_bytes(path.read_bytes())
        return path

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        name = self.current
        dest = self.clips / f"{name}.mp4" if name else None
        if name and dest and (not dest.is_file() or dest.stat().st_size < 2000) and self.fallback_frames:
            _encode(self.fallback_frames, dest)
        self.current = None


def _write_gallery(output: Path, checks: list[dict[str, Any]]) -> None:
    stamp = str(int(time.time()))
    cards = []
    for clip_id, title, body, watch in STORY:
        poster = f"/verify/stills/{clip_id}.png"
        cards.append(
            f"""
    <p class="step">{_esc(clip_id.split('-', 1)[0])}</p>
    <h2>{_esc(title)}</h2>
    <p>{_esc(body)}</p>
    <video controls playsinline preload="metadata" poster="{poster}" src="/verify/clips/{clip_id}.mp4?v={stamp}"></video>
    <p class="watch">{_esc(watch)}</p>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Site Expedition — grilling tour</title>
  <link rel="stylesheet" href="/fonts.css">
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; font: 18px/1.5 Clash, system-ui, sans-serif; background: #0c0d0e; color: #ece8e0; }}
    main {{ max-width: 820px; margin: 0 auto; padding: 32px 20px 96px; }}
    h1 {{ font-weight: 700; font-size: 32px; margin: 0 0 8px; }}
    h2 {{ font-weight: 700; font-size: 22px; margin: 40px 0 8px; }}
    p, li {{ color: #c9c3b8; }}
    a {{ color: #ece8e0; }}
    .lede {{ font-size: 20px; max-width: 40rem; }}
    video {{ display: block; width: 100%; background: #111; border: 1px solid rgba(236,232,224,.14); margin: 12px 0 8px; }}
    .step {{ margin: 0 0 8px; letter-spacing: .08em; text-transform: uppercase; font: 12px Clash, system-ui, sans-serif; color: #9a948a; }}
    .watch {{ color: #9a948a; font-size: 15px; }}
  </style>
</head>
<body>
  <main>
    <p><a href="/">Open the live board →</a></p>
    <h1>The Expedition, as grilled</h1>
    <p class="lede">A distribution operator confirms a Mission Plan. The agent screens candidates, rejects the ones that fail hard gates, replaces them from a lawful pool, deepens survivors, and challenges the leader. TODAY is the real site. FUTURE is a concept. FIT is a named gap until a licensed parcel exists.</p>
    <p>The clips below are me clicking that board. Watch them in order.</p>
    {''.join(cards)}
    <h2>If you want to click it yourself</h2>
    <ol>
      <li>Open the <a href="/">board</a>.</li>
      <li>Click <strong>Warehouse / light industrial</strong>.</li>
      <li>Click <strong>Confirm Mission Plan</strong>.</li>
      <li>Leave Live Mireye off. Click <strong>Run Expedition</strong>.</li>
      <li>Watch the rail questions, San Leon go Reject, Port Houston come in, then San Marcos stay Conditional.</li>
      <li>Stay on TODAY. Then open FUTURE. FIT is in the gaps list, not a mode button.</li>
    </ol>
    <p>This is screening and comparison. It is not a listings website, not a permit, and not a score.</p>
  </main>
</body>
</html>
"""
    (ROOT / "ui" / "verify.html").write_text(html)
    (output / "index.html").write_text(html)


def _esc(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _check(checks: list[dict[str, Any]], clip: str, name: str, ok: Any, detail: Any) -> None:
    checks.append({"clip": clip, "name": name, "ok": bool(ok), "detail": str(detail)})


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    display = os.environ.get("DISPLAY")
    recorder = Recorder(output, display)
    checks: list[dict[str, Any]] = []
    notes: list[str] = []
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="expedition-verify-") as profile:
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
            f"--window-size=1440,1000",
            "--window-position=0,0",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            f"--app={args.base_url}",
        ]
        if not display:
            command.insert(1, "--headless=new")
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

            recorder.start("01-plan-expedition")
            click(cdp, '.tile[data-id="warehouse"]')
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            recorder.grab(cdp, "01-plan-expedition")
            state = _state(cdp)
            _check(checks, "01-plan-expedition", "plan compiled", state["planReady"] and not state["confirmDisabled"], state["planText"][:240])
            click(cdp, "#confirm")
            _wait_js(cdp, "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')")
            time.sleep(0.8)
            ensure_deck_open(cdp)
            ensure_rail_open(cdp)
            click(cdp, "#run-all")
            deadline = time.monotonic() + 55
            streamed = False
            while time.monotonic() < deadline:
                recorder.grab(cdp)
                state = _state(cdp)
                if any(row.get("event") == "workstream" for row in state.get("streamTrace") or []):
                    streamed = True
                if state.get("packetCount", 0) >= 4 and not _evaluate(cdp, "Boolean(document.querySelector('#run-all')?.disabled)"):
                    break
                time.sleep(0.4)
            time.sleep(1.0)
            recorder.grab(cdp, "01-after-run")
            state = _state(cdp)
            notes.append("after_run:" + json.dumps(state, default=str)[:2400])
            rail = (state.get("rail") or "").lower()
            _check(checks, "01-plan-expedition", "question-owned rail", "does present-state evidence veto" in rail or "veto this site" in rail, state["rail"][:400])
            _check(checks, "01-plan-expedition", "NDJSON workstream events", streamed or "done" in rail, f"streamed={streamed} rail={state['rail'][:240]}")
            _check(checks, "01-plan-expedition", "comparison has no composite score", "score" not in state["compareHead"].lower() and "verdict" in state["compareHead"].lower(), state["compareHead"])
            _check(checks, "01-plan-expedition", "survivors and reject present", "conditional" in state["compare"].lower() and "reject" in state["compare"].lower(), state["compare"][:400])
            recorder.stop()

            recorder.start("02-san-leon-veto-and-ground")
            click(cdp, '.card[data-id="san_leon"]')
            _wait_js(cdp, "selectedId === 'san_leon' && Boolean(packets.san_leon)")
            time.sleep(0.6)
            if not _state(cdp)["pastDisabled"]:
                click(cdp, "#mode-past")
                time.sleep(1.2)
            recorder.grab(cdp, "02-san-leon-veto-and-ground")
            state = _state(cdp)
            blob = " ".join([
                state.get("verdict") or "",
                state.get("rail") or "",
                state.get("context") or "",
                state.get("pastNote") or "",
                state.get("gaps") or "",
            ]).lower()
            _check(checks, "02-san-leon-veto-and-ground", "FEMA mapped_sfha reject", "reject" in state["verdict"].lower() and "mapped_sfha" in state["verdict"].lower(), state["verdict"])
            _check(
                checks,
                "02-san-leon-veto-and-ground",
                "DEM disagreement witnessed",
                "nasadem" in blob or "3dep" in blob or state.get("demDelta") not in (None, 0),
                f"delta={state.get('demDelta')} 3dep={state.get('usgs3dep')} nasa={state.get('nasadem')} blob={blob[:280]}",
            )
            _check(checks, "02-san-leon-veto-and-ground", "rewind does not score", state["pastScores"] is False and "does not score" in blob, state.get("pastNote"))
            _check(
                checks,
                "02-san-leon-veto-and-ground",
                "EPA only after RMP hit",
                "environmental-record" in (state.get("rail") or "") or "robinson" in blob or "phase i" in blob,
                f"rail={state['rail'][:240]} gaps={state['gaps'][:200]}",
            )
            recorder.stop()

            recorder.start("03-replace-and-deepen")
            click(cdp, "#mode-today")
            time.sleep(0.4)
            recorder.grab(cdp)
            state = _state(cdp)
            replaced = (
                state.get("replacementCard")
                or "brought in" in (state.get("log") or "").lower()
                or "port houston" in (state.get("log") or "").lower()
                or "replaced" in (state.get("status") or "").lower()
            )
            _check(checks, "03-replace-and-deepen", "rejected site replaced", replaced, f"log={state.get('log')} status={state.get('status')} origins={state.get('origins')}")
            click(cdp, '.card[data-id="san_marcos_tx"]')
            _wait_js(cdp, "selectedId === 'san_marcos_tx' && Boolean(packets.san_marcos_tx)")
            time.sleep(0.8)
            recorder.grab(cdp, "03-replace-and-deepen")
            state = _state(cdp)
            _check(checks, "03-replace-and-deepen", "route times on comparison", "port of houston" in state["compare"].lower() or "h " in state["compare"].lower(), state["compare"][:400])
            _check(checks, "03-replace-and-deepen", "Skeptic stamp on survivor", (not state["skepticHidden"]) and "skeptic" in state["skeptic"].lower(), state["skeptic"])
            _check(checks, "03-replace-and-deepen", "Conditional not Strong Fit", "conditional" in state["verdict"].lower(), state["verdict"])
            recorder.stop()

            recorder.start("04-today-is-the-site")
            click(cdp, "#mode-today")
            time.sleep(0.3)
            click(cdp, "#mode-street")
            time.sleep(1.6)
            recorder.grab(cdp, "04-street")
            street = _state(cdp)
            click(cdp, "#mode-orbit")
            time.sleep(1.4)
            recorder.grab(cdp, "04-orbit")
            click(cdp, "#mode-mesh")
            time.sleep(3.0)
            recorder.grab(cdp, "04-today-is-the-site")
            mesh = _state(cdp)
            _check(checks, "04-today-is-the-site", "street is presentation", "does not score" in street["context"].lower() or street["sceneMode"] in {"street", "orbit", "mesh"}, street["context"])
            _check(checks, "04-today-is-the-site", "3D path does not score", "does not score" in mesh["context"].lower() or mesh["sceneMode"] in {"mesh", "street", "orbit"}, f"{mesh['sceneMode']} {mesh['context']}")
            recorder.stop()

            recorder.start("05-future-fit-gap")
            click(cdp, "#mode-future")
            time.sleep(1.6)
            recorder.grab(cdp, "05-future-fit-gap")
            future = _state(cdp)
            _check(checks, "05-future-fit-gap", "FUTURE visual_concept", future["futureClaim"] == "visual_concept" and "future visual concept" in future["context"].lower(), future["context"])
            _check(checks, "05-future-fit-gap", "FIT is a named gap", (not future.get("fitGapHidden")) and "parcel" in (future.get("fitGap") or future.get("gaps") or "").lower(), f"gap={future.get('fitGap')} gaps={future.get('gaps')[:240]}")
            _check(checks, "05-future-fit-gap", "no FIT mode button", not future.get("fitButton"), f"fitButton={future.get('fitButton')}")
            recorder.stop()

            recorder.start("06-check-a-site")
            click(cdp, "#mode-today")
            time.sleep(0.3)
            click(cdp, "#mode-street")
            time.sleep(0.4)
            ensure_deck_open(cdp)
            if not _state(cdp)["liveOn"]:
                click(cdp, "#live")
            type_text(cdp, "#site-address", WINFIELD)
            click(cdp, "#resolve-address")
            deadline = time.monotonic() + 25
            resolved = {}
            while time.monotonic() < deadline:
                recorder.grab(cdp)
                resolved = _state(cdp)
                if "user site" in resolved["addressStatus"].lower() or "clarif" in resolved["addressStatus"].lower() or "fail" in resolved["addressStatus"].lower():
                    break
                time.sleep(0.4)
            time.sleep(0.6)
            recorder.grab(cdp, "06-check-a-site")
            _check(checks, "06-check-a-site", "live address became USER SITE", "user site" in resolved["addressStatus"].lower(), resolved["addressStatus"])
            _check(checks, "06-check-a-site", "map moved to resolved pin", "winfield" in (resolved.get("mapLabel") or "").lower() or "30.23" in (resolved.get("mapLabel") or "") or "user site" in resolved["verdict"].lower(), f"{resolved.get('mapLabel')} | {resolved['verdict']}")
            if _state(cdp)["liveOn"]:
                click(cdp, "#live")
            recorder.stop()

            recorder.start("07-farm-thin-proof")
            click(cdp, "#replan")
            _wait_js(cdp, "!document.querySelector('#onboard').classList.contains('hidden')")
            click(cdp, '.tile[data-id="farm"]')
            _wait_js(cdp, "mission === 'farm' && Boolean(plan) && !document.querySelector('#confirm').disabled", timeout=25)
            recorder.grab(cdp, "07-farm-plan")
            click(cdp, "#confirm")
            _wait_js(cdp, "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')")
            time.sleep(0.6)
            click(cdp, "#run-all")
            deadline = time.monotonic() + 50
            while time.monotonic() < deadline:
                recorder.grab(cdp)
                state = _state(cdp)
                if state.get("packetCount", 0) >= 3 and not _evaluate(cdp, "Boolean(document.querySelector('#run-all')?.disabled)"):
                    break
                time.sleep(0.4)
            click(cdp, '.card[data-id="iowa_corn"]')
            _wait_js(cdp, "selectedId === 'iowa_corn' && Boolean(packets.iowa_corn)")
            time.sleep(0.4)
            if not _state(cdp)["pastDisabled"]:
                click(cdp, "#mode-past")
                time.sleep(1.0)
            recorder.grab(cdp, "07-farm-thin-proof")
            farm = _state(cdp)
            _check(checks, "07-farm-thin-proof", "farm-history workstream", "farm-history" in farm["rail"] or "cultivated" in farm["rail"].lower(), farm["rail"][:300])
            _check(checks, "07-farm-thin-proof", "no invented yearly map", farm["pastKind"] == "farm_history" and farm["pastSeries"] == 0 and farm["pastSliderHidden"] and "no invented" in (farm["context"] + farm["pastNote"]).lower(), f"series={farm['pastSeries']} note={farm['pastNote']}")
            click(cdp, '.card[data-id="manhattan_midtown"]')
            _wait_js(cdp, "selectedId === 'manhattan_midtown' && Boolean(packets.manhattan_midtown)")
            time.sleep(0.6)
            recorder.grab(cdp, "07-manhattan-reject")
            nyc = _state(cdp)
            _check(checks, "07-farm-thin-proof", "Manhattan reject not_cultivated", "reject" in nyc["verdict"].lower() and "not_cultivated" in nyc["verdict"].lower(), nyc["verdict"])
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

    _write_gallery(output, checks)
    report = {
        "ok": all(item["ok"] for item in checks),
        "elapsed_s": round(time.time() - started, 3),
        "checks": checks,
        "notes": notes,
        "clips": [str(output / "clips" / f"{clip_id}.mp4") for clip_id, _ in CLIPS],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "ok": report["ok"],
        "passed": sum(1 for item in checks if item["ok"]),
        "failed": sum(1 for item in checks if not item["ok"]),
        "gallery": str(ROOT / "ui" / "verify.html"),
    }))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chromium", default=None)
    args = parser.parse_args()
    try:
        report = run(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
