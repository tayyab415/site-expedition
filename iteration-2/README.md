# Iteration 2 — Courtroom Exhibit

A **property vetting agent** interface: split courtroom layout where the cited Mireye record cross-examines independent Earth Engine witnesses, then stamps **KILL** or **KEEP**.

## Look

Dark ink courtroom with a three-panel split:

| Panel | Content |
|---|---|
| **Left — Exhibit A: The Record** | Mireye cited facts table (elevation, FEMA zone, wetland, water %, coast distance, soil drainage) with federal sources and vintages |
| **Right — Exhibit B: The Witnesses** | JRC water timeline SVG + height model bars (Record vs FABDEM vs NASADEM) + fight cards |
| **Bottom — Verdict dock** | Rotated stamp: **KILL** (red) or **KEEP** (green). KILL shows the tagline: *"You're buying 2021 dirt at a 1995 feeling"* |

Pin switcher in the header toggles between the two demo sites.

## Backend

Small Python HTTP server (`serve.py`, stdlib only — no FastAPI):

| Endpoint | Returns |
|---|---|
| `GET /` | Courtroom UI (`static/index.html`) |
| `GET /api/sites` | List of available pins (`san_leon`, `keep_control`) |
| `GET /api/vet?site=san_leon\|keep_control` | Full vet packet: `verdict.json` + `evidence.json` + letter markdown + timeline URL |
| `GET /api/timeline?site=…` | `water_timeline.svg` for the selected site |
| `GET /static/*` | CSS and JS assets |

Port **8022**.

## Harness

No live Mireye calls. The API loads pre-built JSON packets from `data/` on disk:

```
data/
  san_leon/          ← KILL (2 fights) — Galveston Bay shore
    verdict.json
    evidence.json
    water_timeline.svg
    kill_letter.md
  keep_control/      ← KEEP (0 fights) — 3605 Winfield Cove, Austin TX
    verdict.json
    evidence.json
    water_timeline.svg
    advisory.md
```

Source: `harness/runs/san_leon/` and `harness/runs/3605_winfield_cove_austin_tx/`.

## Features

- **Pin flip demo:** Switch `san_leon` → **KILL** with 2 fights (TIME + HEIGHT); switch `keep_control` → **KEEP** with 0 fights. Same agent, different pin — proof it's adjudication, not mood.
- **Real numbers** from harness JSON — no placeholder data.
- **Cited record table** with source links and vintages.
- **Witness panels:** 37-year water timeline (red bars = post-breakpoint) + elevation model comparison bars.
- **Fight cards** surface record-vs-witness contradictions with full number payloads.
- **Verdict stamp** with fight count and coordinates.

## How to run

```bash
cd iteration-2
python3 serve.py
```

Open [http://127.0.0.1:8022](http://127.0.0.1:8022).

Toggle pins in the header to see KILL ↔ KEEP flip.

## Files

```
iteration-2/
├── serve.py              # HTTP API + static file server
├── README.md
├── data/
│   ├── san_leon/         # KILL packet
│   └── keep_control/     # KEEP packet
└── static/
    ├── index.html        # Courtroom layout
    ├── styles.css        # Dark ink / gold / stamp styling
    └── app.js            # Pin switcher + API client + renderers
```
