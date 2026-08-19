# Iteration 4 — The flip IS the product

Editorial verdict surface: two pins, one decision. Move from San Leon (Galveston Bay shore) to inland Austin and watch **KILL** become **KEEP**.

## Run

```bash
cd iteration-4
python3 -m http.server 8024
```

Open [http://localhost:8024](http://localhost:8024).

## What you get

- **Pin rail** — click left (San Leon) or right (Austin). Keyboard: focus the rail, use ← →.
- **Single focus** — one property card morphs; huge verdict word flips with cinematic color.
- **Side by side** — both cards visible: red water-timeline bars vs flat gray, KILL vs KEEP.
- **Caption** — *Move the pin. The robot changes its mind.*
- **One-liners** — KILL: *You're buying 2021 dirt at a 1995 feeling.* · KEEP: *No material contradiction.*

## Data

Copied from harness runs (read-only):

| Folder | Source |
|--------|--------|
| `data/san_leon/` | `harness/runs/san_leon/` |
| `data/keep_control/` | `harness/runs/3605_winfield_cove_austin_tx/` |

Each contains `verdict.json`, `evidence.json`, and `water_timeline.svg`.

## Stack

Static HTML + CSS + vanilla JS. No npm, no maps. `python3 -m http.server` only (fetch requires a local origin).
