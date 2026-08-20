"""Walk Stage A/B/C on the live board, record stills+clip, assess.

Cursor preview MCP is not hosted on this VM. This uses the same Chromium CDP
path as the other verify walks.

    PYTHONPATH=. python3 -m expedition.verify.locate_walk --base-url http://127.0.0.1:8041
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from expedition.verify.browser_smoke import (
    BrowserSmokeError,
    DevToolsConnection,
    _evaluate,
    _screenshot,
    _wait_js,
)
from expedition.verify.feature_record import Recorder, click, type_text
from expedition.verify.workflow_walk import kill_browser, launch_browser


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "var" / "flow-recordings" / "locate-walk"


def state(cdp: DevToolsConnection) -> dict[str, Any]:
    return _evaluate(
        cdp,
        """(() => {
          const chips = Array.from(document.querySelectorAll('#intent-chips .intent-chip')).map((el) => el.textContent);
          const locate = Array.from(document.querySelectorAll('#locate-cards .locate-card')).map((el) => ({
            region: el.dataset.region,
            rank: el.querySelector('.rank')?.textContent || '',
            title: el.querySelector('strong')?.textContent || '',
            vetoed: el.classList.contains('vetoed'),
          }));
          const cards = Array.from(document.querySelectorAll('#cards .card')).map((el) => ({
            id: el.dataset.id,
            name: el.querySelector('strong')?.textContent || '',
            origin: el.querySelector('.origin')?.textContent || '',
            label: el.querySelector('.label')?.textContent || '',
          }));
          return {
            mission,
            entryPath,
            boardBeat,
            confirm: document.querySelector('#confirm')?.textContent || '',
            confirmDisabled: Boolean(document.querySelector('#confirm')?.disabled),
            onboardHidden: Boolean(document.querySelector('#onboard')?.classList.contains('hidden')),
            locateHidden: Boolean(document.querySelector('#locate-panel')?.hidden),
            boardTitle: document.querySelector('#board-title')?.textContent || '',
            status: document.querySelector('#status')?.textContent || '',
            nextMove: document.querySelector('#next-move')?.textContent || '',
            runAll: document.querySelector('#run-all')?.textContent || '',
            planCard: document.querySelector('#plan-card')?.textContent || '',
            searchRegion: document.querySelector('#search-region')?.value || '',
            flood: Boolean(document.querySelector('#flood')?.checked),
            chips,
            locate,
            cards,
            regionAllowlist,
            topRegion: locatePacket && locatePacket.top_region_ids ? locatePacket.top_region_ids[0] : null,
            credits: locatePacket && locatePacket.credits ? locatePacket.credits.spent : null,
          };
        })()""",
    )


def assess(stage: str, got: dict[str, Any], checks: list[tuple[str, bool, str]]) -> list[str]:
    failed = []
    for name, ok, detail in checks:
        if not ok:
            failed.append(f"{stage}.{name}: {detail}")
    print(json.dumps({"stage": stage, "failed": failed, "state": got}, default=str)[:2000], flush=True)
    return failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8041")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output: Path = args.output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    rec = Recorder(output, display=None)
    failures: list[str] = []
    proc, cdp, profile = launch_browser(base_url=args.base_url, headless=True, display=None)
    try:
        cdp.call("Page.navigate", {"url": args.base_url})
        _wait_js(cdp, "location.pathname === '/' && document.readyState === 'complete'", timeout=30)
        _wait_js(cdp, "Boolean(document.querySelector('#intent-text'))", timeout=20)
        _wait_js(cdp, "document.querySelectorAll('#tiles .tile').length === 5", timeout=20)
        time.sleep(0.4)

        rec.start("stage-a-intent")
        rec.grab(cdp, "a0-onboard")
        type_text(
            cdp,
            "#intent-text",
            "I need a warehouse in Texas with rail and highway access, no flood",
        )
        rec.grab(cdp, "a1-typed")
        click(cdp, "#intent-go")
        _wait_js(
            cdp,
            "mission === 'warehouse' && document.querySelectorAll('#intent-chips .intent-chip').length >= 2 && !document.querySelector('#confirm').disabled",
            timeout=20,
        )
        rec.grab(cdp, "a2-chips")
        a = state(cdp)
        rec.stop()
        failures += assess("A", a, [
            ("mission", a["mission"] == "warehouse", f"mission={a['mission']}"),
            ("region", a["searchRegion"] == "texas_triangle", f"search={a['searchRegion']}"),
            ("allowlist", set(a.get("regionAllowlist") or []) == {"houston_metro", "austin_san_antonio", "dallas_fort_worth"}, f"allow={a.get('regionAllowlist')}"),
            ("flood", a["flood"] is True, f"flood={a['flood']}"),
            ("chips", any("rail" in (c or "").lower() for c in a["chips"]), f"chips={a['chips']}"),
            ("confirm", "geograph" in (a["confirm"] or "").lower(), f"confirm={a['confirm']}"),
        ])
        if failures:
            (output / "report.json").write_text(json.dumps({"failures": failures, "a": a}, indent=2))
            print("STAGE A FAILED", *failures, sep="\n")
            return 1

        rec.start("stage-b-locate")
        click(cdp, "#confirm")
        _wait_js(
            cdp,
            "boardBeat === 'locate' && document.querySelectorAll('#locate-cards .locate-card').length >= 1",
            timeout=30,
        )
        time.sleep(0.6)
        rec.grab(cdp, "b1-locate")
        b = state(cdp)
        rec.stop()
        survivors = [row for row in b["locate"] if not row["vetoed"]]
        failures += assess("B", b, [
            ("beat", b["boardBeat"] == "locate", f"beat={b['boardBeat']}"),
            ("panel", b["locateHidden"] is False, f"hidden={b['locateHidden']}"),
            ("top", b["topRegion"] == "dallas_fort_worth", f"top={b['topRegion']}"),
            ("three", len(survivors) == 3, f"survivors={survivors}"),
            ("houston", any(row["region"] == "houston_metro" for row in survivors), f"cards={survivors}"),
            ("credits", b["credits"] == 0, f"credits={b['credits']}"),
            ("rank1", any(row["region"] == "dallas_fort_worth" and "Rank 1" in row["rank"] for row in b["locate"]), f"locate={b['locate']}"),
            ("rank2", any(row["region"] == "houston_metro" and "Rank 2" in row["rank"] for row in b["locate"]), f"locate={b['locate']}"),
        ])
        if failures:
            (output / "report.json").write_text(json.dumps({"failures": failures, "a": a, "b": b}, indent=2))
            print("STAGE B FAILED", *failures, sep="\n")
            return 1

        rec.start("stage-c-scout")
        click(cdp, '#locate-cards .locate-card[data-region="dallas_fort_worth"]')
        if not _evaluate(cdp, "boardBeat === 'scout'"):
            _evaluate(
                cdp,
                "document.querySelector('#locate-cards .locate-card[data-region=\"dallas_fort_worth\"]')?.click()",
            )
        _wait_js(cdp, "boardBeat === 'scout'", timeout=20)
        _wait_js(
            cdp,
            "document.querySelectorAll('#cards .card').length >= 1 && (document.querySelectorAll('#cards .card[data-id^=\"osm_\"]').length >= 1 || /POTENTIAL map/.test(document.body.innerText))",
            timeout=20,
        )
        time.sleep(0.6)
        rec.grab(cdp, "c1-scout")
        c = state(cdp)
        rec.stop()
        names = " ".join(row["name"] for row in c["cards"])
        origins = [row["origin"] for row in c["cards"]]
        failures += assess("C", c, [
            ("beat", c["boardBeat"] == "scout", f"beat={c['boardBeat']}"),
            ("region", c["searchRegion"] == "dallas_fort_worth", f"search={c['searchRegion']}"),
            ("alliance", "alliance" in names.lower() or any(row["id"] == "alliance_tx" for row in c["cards"]), f"cards={c['cards']}"),
            ("osm", any("POTENTIAL" in (row["origin"] or "") or "map" in (row["origin"] or "").lower() for row in c["cards"]) or any(str(row["id"]).startswith("osm_") for row in c["cards"]), f"origins={origins} cards={c['cards']}"),
            ("screen_copy", "catalog" in (c["runAll"] or "").lower(), f"runAll={c['runAll']}"),
            ("discovered_copy", "map place" in (c["nextMove"] or "").lower() or "catalog" in (c["nextMove"] or "").lower(), f"next={c['nextMove']}"),
        ])
        (output / "report.json").write_text(
            json.dumps({"failures": failures, "a": a, "b": b, "c": c}, indent=2)
        )
        if failures:
            print("STAGE C FAILED", *failures, sep="\n")
            return 1
        print("LOCATE WALK OK", flush=True)
        return 0
    except BrowserSmokeError as exc:
        print("WALK ERROR", exc, file=sys.stderr)
        try:
            print("href", _evaluate(cdp, "location.href"), file=sys.stderr)
            print("title", _evaluate(cdp, "document.title"), file=sys.stderr)
            print("ready", _evaluate(cdp, "document.readyState"), file=sys.stderr)
            print("body", str(_evaluate(cdp, "document.body && document.body.innerText"))[:800], file=sys.stderr)
        except Exception as dump_exc:
            print("dump failed", dump_exc, file=sys.stderr)
        return 2
    finally:
        rec.stop()
        kill_browser(proc, cdp, profile)


if __name__ == "__main__":
    raise SystemExit(main())
