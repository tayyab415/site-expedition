---
name: source-scout
description: Constrained official follow-up sources for open Verification Gaps — not web discovery and not a new scoring source.
---

# Source Scout

Use this when a Site Expedition packet has open Verification Gaps and the user needs the responsible official follow-up, not a crawl.

## Rules

- Constrained catalog only (FEMA MSC, EPA ECHO, USGS 3DEP, USFWS NWI, USDA CropScape, plus named gap authorities).
- **Not** arbitrary web discovery, scraping, or `install-python-package`.
- Follow-ups do not score. They do not corroborate a Mireye field by repeating it.
- Custom manifests may include `source-scout`. They may not append `web-crawl`.

## How to run it

Include optional investigation `source_scout` on Standard or Deep. The engine attaches official URLs from material flags on the core screen (flood, elevation, wetland, environmental, farm).

Do not invent a URL. If the catalog has no match, say so and keep the gap.

## Relay

List title, URL, and why it applies. Say not web discovery.
