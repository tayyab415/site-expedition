# Iteration 5 — Intelligence Layer (Layer 2)

**Angle:** triage + vintage arithmetic + why HEIGHT is gated.

This iteration sits between the harness eyes (layer 1) and the verdict packet (layer 3). It makes verdicts *defensible*: the record decides which fights to stage, FEMA vintage is compared to the water breakpoint, and adjudication only counts triaged fights.

## Quick start

```bash
cd iteration-5

# 1. Run intel on bundled harness packets → out/*.json
python3 intel/run.py

# 2. Serve analyst workbook + API on port 8025
python3 intel/serve.py
```

Open **http://127.0.0.1:8025/** — switch between San Leon (KILL) and Winfield Cove (KEEP).

## Architecture

```
data/<site>/verdict.json + evidence.json   ← copied from harness/runs/
        │
        ▼
intel/triage.py    → which fights to stage (TIME / HEIGHT)
intel/vintage.py   → map_aged_out vs map_born_wrong
intel/judge.py     → apply fights only if triaged; 2+ KILL, 1 HUMAN, 0 KEEP
        │
        ▼
out/<site>.json    ← full intelligence packet
        │
        ▼
intel/serve.py     → GET /api/intel?site=… + static UI
```

## Fight triage (`intel/triage.py`)

| Fight | Staged when |
|---|---|
| **TIME** | Coastal (&lt; 5 km to shore) **or** zone AE/VE **or** poor drainage **or** water permanence &gt; 0 |
| **HEIGHT** | Elevation &lt; 10 m **or** zone in A / AE / VE / AO / AH |

Skipped fights get explicit reasons on screen, e.g.  
`HEIGHT skipped: inland, zone X, elev 206 m`

## Vintage arithmetic (`intel/vintage.py`)

Only when **zone is AE** and a **water breakpoint** exists.

FEMA `dataset_vintage` strings (e.g. `48167C_STUDY1`) rarely include an effective date. We proxy study year from the trailing token:

| Token | Proxy year |
|---|---|
| STUDY1 | 1995 |
| STUDY2 | 2005 |
| STUDY3 | 2015 |
| STUDY4 | 2020 |

**Rule:**

- **`map_aged_out`** — inferred study year **before** the breakpoint. The panel froze while the parcel was still dry; wetting since moved water history but the static map did not.
- **`map_born_wrong`** — inferred study year **on or after** the breakpoint. A restudy happened after wetting began, yet AE still conflicts with the satellite archive.

San Leon (`48167C_STUDY1`, breakpoint 2001) → **map_aged_out**.

## Adjudication (`intel/judge.py`)

Same witness thresholds as `harness/vet.py`, but fights run **only** if triage staged them:

- **TIME:** breakpoint exists, latest freq ≥ max(3× baseline, baseline + 0.05), observed ≥ 1.5× recorded permanence
- **HEIGHT:** |FABDEM − record| ≥ 1.0 m (and triage already passed the elevation/zone gate)

Verdict: **2+ fights → KILL · 1 → HUMAN · 0 → KEEP**

KEEP sites get a plain-language explanation listing why each fight was skipped or did not clear thresholds.

## Bundled sites

| Site slug | Expected | Demo feature |
|---|---|---|
| `san_leon` | KILL (TIME + HEIGHT) | Vintage callout — map_aged_out |
| `3605_winfield_cove_austin_tx` | KEEP | Full KEEP rationale — both fights gated off |

Data lives in `data/` (copied from `harness/runs/`). Re-copy after re-running the harness if witnesses change.

## API

```
GET /api/sites
GET /api/intel?site=san_leon
```

Response includes `triage`, `vintage`, `docket`, `ruling`, `record`, `witness_summary`, and inline `water_timeline_svg`.

## Constraints

- Python 3.10+ stdlib only — no npm, no live Mireye calls
- Verdicts are code, not model vibes (same principle as the harness)
