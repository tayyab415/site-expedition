"""Fast browser gate for the first useful map after plan confirmation.

This is intentionally narrower than ``browser_smoke``.  It verifies that the
board does not expose a blank-prone photorealistic 3D canvas while Google tile
content is still starting.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

from expedition.verify.browser_smoke import (
    DEFAULT_TOKEN_FILE,
    BrowserSmokeError,
    DevToolsConnection,
    _browser_diagnostics,
    _chromium_binary,
    _evaluate,
    _free_port,
    _screenshot,
    _wait_for_page,
    _wait_js,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "scene-startup"


def run(args: argparse.Namespace) -> dict:
    token = args.token_file.read_text().strip()
    if not token:
        raise BrowserSmokeError("deployment access token is empty")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    chromium = _chromium_binary(args.chromium)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="expedition-startup-") as profile:
        process = subprocess.Popen(
            [
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
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cdp = None
        try:
            page = _wait_for_page(port)
            cdp = DevToolsConnection(page["webSocketDebuggerUrl"])
            for domain in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
                cdp.call(domain)
            cdp.call("Page.navigate", {"url": args.base_url})
            _wait_js(cdp, "document.readyState === 'complete'")
            _wait_js(cdp, "location.protocol === 'http:' || location.protocol === 'https:'")
            _wait_js(
                cdp,
                "!document.querySelector('#auth-gate')?.classList.contains('hidden')",
            )
            auth = _evaluate(
                cdp,
                """(async () => {
                  const response = await fetch('/api/session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: %s}),
                  });
                  return response.status;
                })()""" % json.dumps(token),
                await_promise=True,
            )
            if auth != 200:
                raise BrowserSmokeError(f"session exchange failed with HTTP {auth}")
            cdp.call("Page.reload", {"ignoreCache": True})
            _wait_js(
                cdp,
                "document.readyState === 'complete' && document.querySelectorAll('#tiles .tile').length === 5 && document.querySelector('#auth-gate')?.classList.contains('hidden')",
            )
            _evaluate(cdp, "pickMission('warehouse')")
            _wait_js(cdp, "Boolean(plan) && !document.querySelector('#confirm').disabled")
            confirmed = time.perf_counter()
            _evaluate(
                cdp,
                "(async () => { await confirmPlan(); return true; })()",
                await_promise=True,
            )
            if args.force_mode:
                _evaluate(cdp, f"applyMode({json.dumps(args.force_mode)})")
            _wait_js(cdp, "!document.querySelector('#app')?.classList.contains('hidden')")
            imagery_expression = "document.querySelectorAll('#quick-map.ready img[data-loaded=true]').length"
            try:
                _wait_js(cdp, imagery_expression, timeout=args.budget_seconds)
            except BrowserSmokeError:
                pass
            state = _evaluate(
                cdp,
                """(() => ({
                  sceneMode,
                  globeVisible: Boolean(viewer?.scene?.globe?.show),
                  imageryLayers: viewer?.imageryLayers?.length || 0,
                  surfaceTiles: viewer?.scene?.globe?._surface?._tilesToRender?.length || 0,
                  imageryProviderReady: Boolean(viewer?.imageryLayers?.get(0)?.imageryProvider?.ready),
                  imageryLayerShow: Boolean(viewer?.imageryLayers?.get(0)?.show),
                  cameraHeight: viewer?.camera?.positionCartographic?.height || null,
                  surfaceTileImageryCounts: (viewer?.scene?.globe?._surface?._tilesToRender || [])
                    .map(tile => tile.data?.imagery?.length || 0),
                  surfaceTileImageryStates: (viewer?.scene?.globe?._surface?._tilesToRender || [])
                    .flatMap(tile => (tile.data?.imagery || []).map(item => ({
                      loading: item.loadingImagery?.imagery?.state ?? null,
                      ready: item.readyImagery?.imagery?.state ?? null,
                    }))),
                  imageryTextures: (viewer?.scene?.globe?._surface?._tilesToRender || [])
                    .reduce((count, tile) => count + (tile.data?.imagery || [])
                      .filter(item => Boolean(item.readyImagery?.imagery?.texture)).length, 0),
                  quickMapVisible: !document.querySelector('#quick-map')?.classList.contains('hidden'),
                  quickMapTilesLoaded: document.querySelectorAll('#quick-map.ready img[data-loaded=true]').length,
                  tileContentReady: tileset?._statistics?.numberOfTilesWithContentReady || 0,
                  context: document.querySelector('#context-tag')?.textContent || '',
                  status: document.querySelector('#status')?.textContent || '',
                }))()""",
            )
            state["after_confirm_ms"] = round(
                (time.perf_counter() - confirmed) * 1000,
                1,
            )
            state["nonblank_first_mode"] = (
                (
                    (
                        state["sceneMode"] in {"aerial", "osm"}
                        and state["quickMapVisible"]
                        and state["quickMapTilesLoaded"] > 0
                    )
                    or (
                        state["sceneMode"] == "mesh"
                        and (
                            (state["quickMapVisible"] and state["quickMapTilesLoaded"] > 0)
                            or int(state.get("tileContentReady") or 0) > 0
                        )
                    )
                )
                and state["after_confirm_ms"] <= args.budget_seconds * 1000
            )
            screenshot = args.output_dir / "startup.png"
            _screenshot(cdp, screenshot)
            diagnostics = _browser_diagnostics(cdp.events)
            network = []
            for event in cdp.events:
                if event.get("method") != "Network.responseReceived":
                    continue
                response = (event.get("params") or {}).get("response") or {}
                url = str(response.get("url") or "")
                if "/g2d/" in url or "/v1/3dtiles" in url:
                    network.append({"url": url.split("?", 1)[0], "status": response.get("status")})
            report = {
                "ok": state["nonblank_first_mode"] and not diagnostics,
                "elapsed_s": round(time.perf_counter() - started, 3),
                "state": state,
                "diagnostics": diagnostics,
                "network": network,
                "screenshot": str(screenshot),
            }
            (args.output_dir / "report.json").write_text(
                json.dumps(report, indent=2, allow_nan=False) + "\n"
            )
            return report
        finally:
            if cdp is not None:
                cdp.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8030")
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chromium")
    parser.add_argument("--budget-seconds", type=float, default=4.0)
    parser.add_argument("--force-mode", choices=("aerial", "osm"))
    return parser.parse_args()


def main() -> None:
    report = run(parse_args())
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
