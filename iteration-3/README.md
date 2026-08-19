# Iteration 3 — The harness IS the product

**Angle:** an explicit tool-loop the user watches, not a hidden CLI script.

Most vetting demos hide the robot: run a script, open a PDF. This iteration inverts that — the **trace UI is the product surface**. You see `mireye.fetch → ee.water_rewind → ee.height_check → intel.triage → judge.verdict → act.write_packet` as a vertical timeline, each row expanding to JSON in/out. The moat is that tools are first-class citizens.

## vs hidden CLI (`harness/vet.py`)

| Hidden CLI | This iteration |
|---|---|
| `[1/4] Mireye record...` printed to stdout | `mireye.fetch` row with full cached payload |
| EE runs silently for minutes | `ee.water_rewind` / `ee.height_check` show witness JSON + simulated timing |
| Judge logic buried in Python | `judge.verdict` step exposes fights + ruling |
| Packet files appear on disk | `act.write_packet` is the last tool call; verdict stamp follows |
| No replay | Play trace for **san_leon** (KILL) vs **keep_control** (KEEP) |

Same deterministic rules. Same cached data. Different surface — the agent trace an IDE would show.

## Run

```bash
cd iteration-3

# Generate trace.json from cached packets (no live APIs)
python3 runner.py --all

# Serve UI + API
python3 serve.py 8023
```

Open **http://127.0.0.1:8023/**

- Switch **san_leon** → play → **KILL** (TIME + HEIGHT fights, aggravators)
- Switch **keep_control** (3605 Winfield Cove, Austin) → play → **KEEP**

API: `GET /api/trace?site=san_leon|keep_control`

## Architecture

```
harness.py   tools as dicts: name, input_schema, run(ctx)
runner.py    fixed plan (no LLM) → trace/<site>.json
serve.py     stdlib http.server — UI + /api/trace
ui/          dark monospace trace replay
data/        cached runs + mireye/earth payloads
```

### Tool loop (fixed plan)

1. **mireye.fetch** — cited record from `data/<site>/cache/mireye/`
2. **ee.water_rewind** — JRC monthly history from `cache/earth/`
3. **ee.height_check** — FABDEM vs NASADEM vs record elevation
4. **intel.triage** — record picks the docket (coastal → time + height witnesses)
5. **judge.verdict** — deterministic KEEP / KILL / HUMAN
6. **act.write_packet** — writes verdict.json, evidence, SVG, letter

Timings in the trace are **simulated** (420 ms fetch, 2.8 s water rewind, etc.). Payloads are **real cached packets** from the parent harness runs.

## Data

Copied from `harness/runs/` and `harness/cache/`:

- `data/san_leon/` — Galveston Bay shore pin → **KILL**
- `data/keep_control/` — 3605 Winfield Cove, Austin → **KEEP** (control)

## Constraints

- No npm, no bundler — static HTML/CSS/JS
- No live Mireye or Earth Engine calls
- Verdicts are code, not model vibes (same rules as `harness/vet.py`)
