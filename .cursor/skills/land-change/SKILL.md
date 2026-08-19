---
name: land-change
description: Neighborhood built-cover change for one US pin — Dynamic World top-1 plus an NLCD check, INFORM only, never a score.
---

# Land Change

Use this when screening whether nearby built cover changed between an early and late window. This is an Expedition INFORM skill. It never vetoes, never gates, and never becomes a composite score.

## Rules

- Thresholded Dynamic World **top-1 labels** only. Mean class-probability scores are invalid.
- Attach an NLCD developed-fraction check when the replay carries one. Disagreement is a Verification Gap, not a chosen truth.
- Neighborhood buffer is context, not parcel condition, not a construction permit, and not listing/competition proof.
- Unknown stays Conditional. Do not invent a change type.
- Home may run this only when the Mission Plan explicitly includes it.

## How to run it

On a confirmed Site Expedition Mission Plan, include optional investigation `land_change` (Standard or Deep). Replay fixtures live under `expedition/data/fixtures/change/` and `expedition/data/fixtures/land_change/`.

For a natural-language question about the same pin, use `mireye_ask` with the coordinate or a full US address. Keep the citation. Do not treat Mireye land-cover class as a change interval.

## Relay

Always keep source (`GOOGLE/DYNAMICWORLD/V1`, NLCD when present), windows, buffer, `change_type`, and `agreement`. Say INFORM. Do not say the site is developing, listed, or permitted.
