# Iterations — pick a look, a backend, a harness

The product is one thing ([PRODUCT.md](PRODUCT.md)): a **property vetting agent**. Pin in, cross-examine the cited record against satellite witnesses, KEEP / KILL / ASK-A-HUMAN.

These folders are **different implementations** of that product. Same two pins:

| Pin | Verdict (after height gate) |
|---|---|
| San Leon, TX (`29.476, -94.967`) | **KILL** — TIME + HEIGHT |
| 3605 Winfield Cove, Austin | **KEEP** — inland, zone X, height fight gated off |

Shared evidence still lives in [`harness/`](harness/) (`vet.py --site san_leon|keep_control`). Iterations copy packets; they do not spend Mireye credits.

## How they differ

| Folder | Look | Backend | Harness / features | Run |
|---|---|---|---|---|
| [iteration-1](iteration-1/) | Print **memorandum** (cream, serif, stamp) | Static files, port **8021** | Thinnest: the letter *is* the app | `python3 serve.py` |
| [iteration-2](iteration-2/) | **Courtroom** split: record vs witnesses | Stdlib HTTP API, port **8022** | `/api/vet?site=` | `python3 serve.py` |
| [iteration-3](iteration-3/) | **Agent trace** (tool calls as the UI) | `harness.py` + `runner.py` + server **8023** | First-class tools: fetch → rewind → height → triage → judge → packet | `python3 runner.py --all && python3 serve.py` |
| [iteration-4](iteration-4/) | **Cinematic flip** — huge KILL/KEEP | Static, port **8024** | Feature bet: move the pin, the robot changes its mind | `python3 -m http.server 8024` |
| [iteration-5](iteration-5/) | **Analyst workbook** — why fights were staged | `intel/` triage + vintage + judge, port **8025** | Layer 2: HEIGHT gated; FEMA vintage vs 2001 breakpoint | `python3 intel/run.py && python3 intel/serve.py` |
| [iteration-6](iteration-6/) | **Email to the agent** | `compose.py` consequence lines, port **8026** | What the fight *does* to the deal (no fake $) | `python3 compose.py && python3 serve.py` |
| [iteration-7](iteration-7/) | **Photorealistic 3D eyes** (Cesium + Map Tiles) + EE overlays | Stdlib proxy + EE mapids, port **8027** | Google 3D is context; JRC / NAIP / FABDEM / embeddings are the witnesses | `.venv-ee/bin/python serve.py` |

Steal freely. A likely mix: **iteration-7 eyes** (3D + EE overlays) + **iteration-5 brain** + **iteration-3 trace** + **iteration-1 or 6** as the artifact a human forwards.

## What not to mix in

Map/globe as the product, diligence dump, buying assistant, live parcel lookups (300 credits), Aerial View of San Leon (none exists).
