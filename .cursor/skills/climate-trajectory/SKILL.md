---
name: climate-trajectory
description: Regional CMIP6 summer-heat range for one US pin — ensemble, not a parcel prediction.
---

# Climate Trajectory

Use this for a labeled regional climate scenario range at a Candidate Site. This is an Expedition INFORM MODEL skill.

## Rules

- GRIDMET historical June–August tmax plus NASA GDDP-CMIP6 members (ACCESS-CM2, MIROC6, NorESM2-LM, GFDL-ESM4) under SSP2-4.5 and SSP5-8.5.
- Report a **range**, not a single prediction. Nominal scale is ~25–28 km, not parcel.
- Not a cooling-load study, water-right forecast, or permit input.
- Unknown stays Conditional.

## How to run it

Include optional investigation `climate_trajectory` (Standard or Deep). Replay fixtures live under `expedition/data/fixtures/climate/`.

For a present-state heat fact, `mireye_ask` or fetch `days_above_32c_annual_count` is a different question. Do not merge it into this scenario range.

## Relay

Keep model list, SSP pair, historical baseline, future window, median delta, and min/max. Say regional, not a parcel prediction.
