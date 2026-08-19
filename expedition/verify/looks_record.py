"""Record the five planning-board looks with real pointer events.

    DISPLAY=:98 PYTHONPATH=. python3 -m expedition.verify.looks_record --base-url http://127.0.0.1:8030
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
from expedition.verify.feature_record import Recorder, click, _esc, _check


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "looks"
LOOKS = [
    ("A", "HUD overlay", "Full-bleed city, glass corners, lot chips along the bottom."),
    ("B", "Layer rack", "A map-mode column on the left. Flood/power/roads as layers, inspector on the right."),
    ("C", "Ops table", "Fat bottom console and demand meters, Cities: Skylines style."),
    ("D", "Cinema", "Street or orbit is the movie. Cards are a filmstrip. Side panels gone."),
    ("E", "Street inspector", "Street View is the city. Photorealistic 3D is a picture-in-picture."),
]


def _write_gallery(output: Path, checks: list[dict[str, Any]]) -> None:
    stamp = str(int(time.time()))
    cards = []
    for look_id, name, body in LOOKS:
        clip = f"look-{look_id.lower()}"
        cards.append(
            f"""
    <p class="step">Look {look_id}</p>
    <h2>{_esc(name)}</h2>
    <p>{_esc(body)}</p>
    <p><a href="/?variant={look_id}">Open this look on the live board →</a></p>
    <video controls playsinline preload="metadata" poster="/looks/stills/{clip}.png" src="/looks/clips/{clip}.mp4?v={stamp}"></video>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Site Expedition — five looks</title>
  <link rel="stylesheet" href="/fonts.css">
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; font: 18px/1.5 Clash, system-ui, sans-serif; background: #0c0d0e; color: #ece8e0; }}
    main {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 96px; }}
    h1 {{ font-weight: 700; font-size: 32px; margin: 0 0 8px; }}
    h2 {{ font-weight: 700; font-size: 22px; margin: 40px 0 8px; }}
    p, li {{ color: #c9c3b8; }}
    a {{ color: #ece8e0; }}
    .lede {{ font-size: 20px; max-width: 42rem; }}
    video {{ display: block; width: 100%; background: #111; border: 1px solid rgba(236,232,224,.14); margin: 12px 0 8px; }}
    .step {{ margin: 0 0 8px; letter-spacing: .08em; text-transform: uppercase; font: 12px Clash, system-ui, sans-serif; color: #9a948a; }}
  </style>
</head>
<body>
  <main>
    <p><a href="/?variant=A">Open the live board →</a></p>
    <h1>Five planning-board looks</h1>
    <p class="lede">Same Expedition. Five layouts. TODAY starts at Street View when Google has a panorama at the pin, otherwise street-height photorealistic 3D. The old top-down map is a fallback tool labeled Map. Pick a look. Arrow keys cycle them on the board.</p>
    {''.join(cards)}
    <p>Pictures do not score. FIT is still a named gap. San Leon still dies on FEMA.</p>
  </main>
</body>
</html>
"""
    (ROOT / "ui" / "looks.html").write_text(html)
    (output / "index.html").write_text(html)


def _scene(cdp: DevToolsConnection) -> dict[str, Any]:
    value = _evaluate(
        cdp,
        """(() => ({
          look: document.body.dataset.look || '',
          sceneMode: typeof sceneMode === 'undefined' ? null : sceneMode,
          streetHidden: Boolean(document.querySelector('#street-stage')?.hidden),
          streetSrc: document.querySelector('#street-image')?.getAttribute('src') || '',
          context: document.querySelector('#context-tag')?.textContent || '',
          appHidden: document.querySelector('#app')?.classList.contains('hidden'),
          selectedId: typeof selectedId === 'undefined' ? null : selectedId,
        }))()""",
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
    with tempfile.TemporaryDirectory(prefix="expedition-looks-") as profile:
        command = [
            chromium,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-unsafe-swiftshader",
            "--disable-background-networking",
            "--no-first-run",
            f"--window-size=1440,1000",
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
            _wait_js(cdp, "document.querySelector('#app') && !document.querySelector('#app').classList.contains('hidden')")
            time.sleep(2.5)
            click(cdp, '.card[data-id="san_marcos_tx"]')
            time.sleep(2.0)

            for look_id, name, _body in LOOKS:
                clip = f"look-{look_id.lower()}"
                recorder.start(clip)
                _evaluate(cdp, f"applyLook({look_id!r})")
                time.sleep(0.6)
                click(cdp, "#mode-street")
                time.sleep(2.4)
                recorder.grab(cdp, clip)
                state = _scene(cdp)
                _check(
                    checks,
                    clip,
                    f"{look_id} is street-first, not a top-down map",
                    state.get("sceneMode") in {"street", "orbit", "mesh"}
                    or (not state.get("streetHidden") and "/sv?" in (state.get("streetSrc") or "")),
                    json.dumps(state),
                )
                _check(checks, clip, f"{look_id} look applied", state.get("look") == look_id, state.get("look"))
                time.sleep(3.2)
                recorder.grab(cdp)
                time.sleep(2.4)
                recorder.grab(cdp)
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
    print(json.dumps({"ok": report["ok"], "failed": [c for c in report["checks"] if not c["ok"]]}, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
