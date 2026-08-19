---
name: labor-access
description: County labor-shed context for warehouse or data-center sites — never a hiring claim, never used for Home.
---

# Labor Access

Use this for county employment / commute context around a warehouse or data-center pin. This is an Expedition INFORM skill.

## Rules

- **Never Home.** Housing ranking must not include demographic or labor facts.
- **Never claim workers are available.** `workers_available` is always null. ACS labor force and LODES flows are not a hiring forecast.
- Declared logistics destinations are not a labor shed.
- Unknown stays Conditional.

## How to run it

Include optional investigation `labor_access` on Warehouse or Data Center (Standard or Deep). Replay fixtures live under `expedition/data/fixtures/labor/`.

Do not ask Mireye or Census for a headcount you can hire. If the user wants a commute question, keep it county-scale and cited.

## Relay

Name the county, cite ACS/LODES vintage when present, and say this does not claim workers are available.
