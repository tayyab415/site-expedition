---
name: mireye-earth
version: 0.7.1
description: Provenance-tagged geospatial data for any US coordinate or street address. Ask natural-language questions, fetch named fields by name or preset, resolve an address to a coordinate, and discover the catalog — every value carries source provenance.
homepage: https://mireye.com
docs: https://docs.mireye.ai
metadata: {"api_base": "https://api.mireye.com"}
---

# Mireye Earth

You are an AI agent. Mireye Earth gives you authoritative, citation-backed geospatial data for any US coordinate — terrain and soils, flood and wildfire risk, land cover, buildings and roads, the electric grid and gas network, water supply, solar and wind resource, natural hazards (seismic, wind, tornado, hail, landslide), parcels, and political boundaries. Every value comes with the source identifier, the upstream URL, the dataset vintage, the timestamp, and a confidence rating. You can ask a free-text question, fetch named fields directly, resolve a US street address to a coordinate, or pull the full catalog. Every data endpoint takes either a coordinate or an address.

**Base URL:** `https://api.mireye.com`
**Docs:** [docs.mireye.ai](https://docs.mireye.ai)
**Field catalog (machine-readable):** `GET /v1/meta/fields`
**Full docs index for LLMs:** [docs.mireye.ai/llms.txt](https://docs.mireye.ai/llms.txt)

---

## Before You Start

Three scenarios — know which one you're in:

1. **You know the exact fields you want** (e.g. `elevation`, `within_floodplain_polygon`). Skip to [`/v1/fetch`](#post-v1fetch-named-fields-with-provenance). Deterministic, 1–3 s warm.
2. **You have a question but don't know which fields answer it** (e.g. "Is this property at flood risk?"). Use [`/v1/ask`](#post-v1ask-natural-language-questions). A planner picks the fields, a synthesizer writes a cited prose answer. 2–6 s warm, up to 60 s on cold start. Want it token-by-token? Use [`/v1/ask/stream`](#post-v1askstream-streaming-answers).
3. **You're not sure what's even available.** Call [`GET /v1/meta/fields`](#get-v1metafields-discover-the-catalog) once at startup to enumerate all 250+ fields, their units, sources, and the 15 preset bundles. ETag-cached — re-fetch with `If-None-Match` is free.

Cutting across all three: **if the user gave you a street address rather than a coordinate, you do not have to resolve it first.** `/v1/ask`, `/v1/ask/stream` and `/v1/fetch` all take `address` in place of `lat`+`lng`. Resolve it yourself via [`POST /v1/geocode`](#post-v1geocode-address-to-coordinate) only when you want the coordinate on its own. Either way, read the `geocode` block that comes back — a geocoded coordinate can land on the wrong parcel. If the input might be ambiguous, isn't a clean address (a coordinate or an APN), or you want a parcel attached, use [`POST /v1/lookup`](#post-v1lookup-canonical-join-keys) instead of `/v1/geocode`.

---

## How It Works

Mireye Earth is a thin orchestrator over authoritative geospatial sources. When you request fields, Mireye fetches them in parallel from their respective upstreams, wraps each value with provenance metadata, and returns the bundle. Sources span federal agencies — USGS, NOAA, USDA, USFS, USFWS, FEMA, EPA, EIA, NREL, LBNL, FHWA, FAA, FCC, BTS, US Census, HUD, BLM, and USACE — plus open and commercial datasets like Sentinel-2, JRC Global Surface Water, Overture Maps, Regrid, USWTDB, and USPVDB.

### Core operations

- **`POST /v1/ask`** — natural-language Q&A. You send a coordinate + question; a planner LLM picks the relevant catalog fields, Mireye fetches them, a synthesizer LLM writes a cited prose answer. Use this when you don't know the schema in advance. `POST /v1/ask/stream` streams the same answer over Server-Sent Events.
- **`POST /v1/fetch`** — structured field access. You name the fields (or a preset bundle); Mireye returns each one with `value`, `unit`, `source`, `source_url`, `confidence`, `dataset_vintage`, `fetched_at`, `ttl_seconds`, `status`, and `notes`. Use this when you know what you want.
- **`POST /v1/fetch/batch`** — the batch form of `/v1/fetch`: one field selection applied to up to 25 locations. Results are index-aligned with the request; one bad location becomes an `ok: false` entry instead of failing the batch. Use this when you're screening a list.
- **`POST /v1/runs`** — the async form. Submit a job, get a `run_id` immediately, poll or stream its progress from anywhere, and download the finished result as CSV or GeoJSON. Use this when the work is too long to hold a connection open for.
- **`POST /v1/geocode`** — address to coordinate. You send a US street address; Mireye returns `lat`/`lng` plus how that coordinate was derived (`accuracy_type`, `provider`, `source`). Use this when you want the coordinate on its own — `/v1/ask` and `/v1/fetch` accept an `address` directly.
- **`POST /v1/lookup`** — address/coordinate to canonical join keys. Unlike `/v1/geocode`, it detects genuine ambiguity across multiple candidate matches instead of trusting a single top result, and attaches a parcel (owner, boundary) when the geocode is parcel-quality. Use this instead of `/v1/geocode` when the input might be ambiguous or you want a parcel. (APN-shaped input is detected but not yet resolved — returns a clean `no_match`.)
- **`GET /v1/meta/fields`** — the machine-readable catalog of every field and preset. Public, no auth, ETag-cached.
- **`POST /v1/field-requests`** — order a field the catalog doesn't have yet, described in plain language. It is matched against the catalog first, so an ask an existing field already answers comes back answered rather than queued. Use this instead of giving up when a field you need isn't in the catalog.

`/v1/ask`, `/v1/fetch` and `/v1/meta/fields` share the same 250+-field catalog and the same provenance shape on every value.

There's also a **Sites** surface (`/v1/sites`, `/v1/ask-site`) for registering a named location once and asking repeated questions against it — see [Sites](#sites-persistent-locations) below.

### Resource hierarchy

```
Catalog (GET /v1/meta/fields)
├── 250+ named fields across 7 layers
│   ├── Terrain           (elevation, slope, soils, hydrology, wetlands, coast, floodplain)
│   ├── Land Cover        (LCMS, land use, NLCD canopy, NDVI, USDA CDL)
│   ├── Built Environment (buildings, roads, bridges, turbines, solar facilities, opportunity zones)
│   ├── Utilities & Energy (power plants, transmission, substations, gas, water, broadband, interconnection queue, prices)
│   ├── Climate & Resource (solar GHI/DNI/PV yield, wind speed/density/CF, temperature, humidity, drought, snow)
│   ├── Hazards           (seismic, design wind, tornado, hail, lightning, landslide, dams, brownfields, superfund, air quality)
│   └── Parcels & Boundaries (divisions, Census, PAD-US protected areas, critical habitat, easements, Regrid parcels)
└── 15 presets that expand to curated field bundles
    └── terrain, flood_risk, wildfire_underwrite, land_cover, site_selection,
        building_lookup, utilities, boundaries, natural_hazard, grid_interconnect,
        data_center_siting, solar_siting, wind_siting, storage_siting,
        points_of_interest
```

### Coverage

US only. Accepted envelope: `lat ∈ [18, 72]`, `lng ∈ [-180, -65]`. Covers CONUS, Alaska, Hawaii, and US territories. Out-of-bounds requests return `400 coord_out_of_bounds`. Pull the live envelope from `GET /v1/meta/fields` under `us_envelope` if you want to validate client-side.

---

## Quick Start

### Step 1: Pick a coordinate

Anywhere in the US. For this guide we'll use lower Manhattan:

```
lat = 40.7128
lng = -74.0060
```

### Step 2: Ask a question

```bash
curl -s https://api.mireye.com/v1/ask \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "lat": 40.7128,
    "lng": -74.0060,
    "question": "Is this property in a flood zone?"
  }' | jq
```

**Response (abridged):**

```json
{
  "answer": "This Manhattan address is not currently in a designated 100-year floodplain per FEMA NFHL data, but it sits 412 m from the East River shoreline at an elevation of only 13.15 m.",
  "confidence": "high",
  "citations": [
    {
      "source": "FEMA_NFHL",
      "source_url": "https://hazards.fema.gov/femaportal/wps/portal/NFHLWMS",
      "fields": ["within_floodplain_polygon"],
      "fetched_at": "2026-06-24T22:00:00Z",
      "confidence": "high"
    }
  ],
  "fields_used": ["within_floodplain_polygon", "elevation", "coast_distance_m"]
}
```

The `answer` is prose. The `citations` array is the audit trail — one entry per source used. `fields_used` lists the catalog field names the answer depends on; use it to re-verify deterministically via `/v1/fetch`.

### Step 3: Fetch raw fields directly

When you know the field names, skip the planner and ask for them by name:

```bash
curl -s https://api.mireye.com/v1/fetch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "lat": 40.7128,
    "lng": -74.0060,
    "fields": ["elevation", "coast_distance_m", "within_floodplain_polygon"]
  }' | jq
```

Each field comes back as a self-contained record with its value, unit, source, source URL, confidence, dataset vintage, fetch timestamp, TTL, and status.

### Step 4: Use a preset

When you want a curated bundle for a common workflow, pass a preset name instead of (or in addition to) a `fields` array:

```bash
curl -s https://api.mireye.com/v1/fetch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{"lat": 29.7604, "lng": -95.3698, "preset": "flood_risk"}' | jq '.fields | keys'
```

Fifteen presets ship today: `terrain`, `flood_risk`, `wildfire_underwrite`, `land_cover`, `site_selection`, `building_lookup`, `utilities`, `boundaries`, `natural_hazard`, `grid_interconnect`, `data_center_siting`, `solar_siting`, `wind_siting`, `storage_siting`, `points_of_interest`. See [Presets](#presets) below for full expansions.

### Step 5: Discover the catalog

Once, at startup, fetch the machine-readable catalog (no auth required):

```bash
curl -s https://api.mireye.com/v1/meta/fields | jq
```

Cache the response body and the `ETag` header. On subsequent boots, send `If-None-Match: <etag>` — a `304 Not Modified` means your cached copy is still valid. The catalog only changes on schema-version bumps (field renames, type changes, new fields), so a single fetch at startup is usually enough.

You're done. The rest of this document is reference.

---

## Rules

### Coordinate scope

- **US only.** Mireye is built on US-focused source datasets. Coordinates outside `lat ∈ [18, 72]`, `lng ∈ [-180, -65]` return `400 coord_out_of_bounds`. If a human gives you a non-US location, tell them Mireye doesn't cover it — don't fabricate.
- **Coordinates are in decimal degrees, WGS84.** Latitude before longitude. `+` for north and east, `-` for south and west.

### Provenance and confidence

- **Every value carries provenance.** Never present a Mireye value to a human without surfacing at least the `source` and ideally the `source_url`, `dataset_vintage`, and `fetched_at`. That's the whole point of using Mireye instead of guessing.
- **Respect confidence ratings.** Each value is `high`, `medium`, `low`, or `unknown` (lowercase). For regulatory, underwriting, or audit workflows, filter to `high` before quoting a value as definitive. `low` should be flagged for human review.
- **Read the per-field `status`.** `/v1/fetch` stamps each field with `status: "ok"` (a real value is present) or `status: "absent"` (the source confirmed there's *no* value at that coordinate — e.g., asking for a crop class on a city block). An `absent` field is **not a failure**: `value` is `null`, `confidence` is `unknown`, and `notes` explains why. Don't retry — the answer is "no data exists here." Fields that genuinely *failed* to fetch never appear under `fields`; they go to `partial_failures`.
- **Check `partial_failures` on every `/v1/fetch` response.** A 200 can still contain failed fields. If `retryable: true`, the source had a transient issue — retry. If `retryable: false`, the source returned a permanent error — don't. (`/v1/ask` has no `partial_failures` array — its prose answer flags any field it couldn't get.)

### Honesty about data

- **Don't fabricate values Mireye didn't return.** If a field is `absent`, missing, or in `partial_failures`, say so explicitly. The cited prose answer from `/v1/ask` already does this — preserve that behavior when summarizing for a human.
- **Don't drop citations.** When you summarize a Mireye result back to a human, keep at least the source names. The citation chain is the trust contract.

---

## Authentication

`/v1/meta/fields` is public so agents can inspect the catalog without a token. `/v1/ask`, `/v1/ask/stream`, `/v1/fetch`, `/v1/fetch/batch`, `/v1/runs` (submit and every read), `/v1/geocode`, `/v1/lookup`, `/v1/field-requests`, and the Sites endpoints require a Mireye bearer token:

```
Authorization: Bearer YOUR_MIREYE_TOKEN
```

Three ways to get one:

- **Local MCP (Claude Desktop, Cursor, custom agents):** run `mireye-mcp login` once — a device flow prints a verification URL and code, and stores a token locally. Or set `MIREYE_BEARER_TOKEN`.
- **Hosted MCP (Claude Code):** point your client at `https://api.mireye.com/mcp` and complete the browser OAuth 2.1 + PKCE flow — no manual token handling.
- **Direct HTTP:** create an API token from the Mireye account settings page and send it as a bearer header.

**401 vs 403:** `401` means no token, or the token is expired/revoked — re-authenticate. `403` means the token is valid but the account is not permitted by backend policy — that's an account issue, not a bad key.

### Pricing and credits

Every call costs a fixed number of credits. Machine-readable plan catalog: `GET https://api.mireye.com/v1/meta/plans` (public, no auth). Your own balance: `GET /v1/users/me/usage` (bearer token — an agent can check its own remaining credits before starting an expensive sweep).

| Call | Credits |
| ---- | ------- |
| `/v1/geocode` | 1 |
| `/v1/fetch` | 1 per field per location |
| `/v1/ask` | 10 |
| `/v1/lookup` (parcel record) | 300 per location — 150 on Scale, charged only on a successful match |

Free tier is 5,000 credits/month at 20 req/min, no card. Paid plans run $19 / $99 / $499 a month (25,000 / 120,000 / 750,000 credits at 60 / 300 / 600 req/min). Extra credits are always $1.00 per 1,000 on every paid plan, and all allowances reset on the 1st of each month (UTC). Batch requests count as one call against the rate limit and bill per location. Full table: [mireye.com/pricing](https://www.mireye.com/pricing).

### Request correlation

Every response includes an `X-Request-ID` header. If you supply one yourself, Mireye echoes it back unchanged — useful for correlating your application logs against Mireye's server logs. When reporting a `500 internal` error, always include the `X-Request-ID` value, the request body, and the approximate UTC timestamp.

---

## API Reference

### `POST /v1/ask` — natural-language questions

Send a US coordinate and a free-text question. A planner model picks relevant fields from the catalog, fetches them in parallel, and a synthesizer model writes a cited prose answer.

```bash
curl -X POST https://api.mireye.com/v1/ask \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "lat": 40.7128,
    "lng": -74.0060,
    "question": "Is this property in a flood zone?",
    "include_trace": false
  }'
```

| Field           | Type    | Required | Description                                                                                |
| --------------- | ------- | -------- | ------------------------------------------------------------------------------------------ |
| `lat`           | number  | One of   | Latitude in `[18, 72]`. Requires `lng`.                                                    |
| `lng`           | number  | One of   | Longitude in `[-180, -65]`. Requires `lat`.                                                |
| `address`       | string  | One of   | US street address, 1–256 chars. Resolved server-side. Send `lat`+`lng` **or** `address`, never both and never neither — either mistake is `422 invalid_locator`. |
| `question`      | string  | Yes      | Free-text geospatial question. Max 2000 chars.                                             |
| `include_trace` | boolean | No       | When `true`, includes a `trace` object with planner reasoning and the model names used.     |

**Response (200) — key fields:**

```json
{
  "lat": 40.7128,
  "lng": -74.006,
  "question": "Is this property in a flood zone?",
  "answered_at": "2026-06-24T22:00:00Z",
  "answer": "...prose answer with implicit citations...",
  "confidence": "high",
  "citations": [
    {
      "source": "USGS_3DEP",
      "source_url": "https://epqs.nationalmap.gov/",
      "fields": ["elevation"],
      "fetched_at": "2026-06-24T22:14:01.882Z",
      "confidence": "high"
    }
  ],
  "fields_used": ["elevation", "within_floodplain_polygon", "coast_distance_m"]
}
```

- `answer` — prose. Cite-aware; references sources by name and explicitly flags any field it couldn't get. Note `/v1/ask` does **not** return a `partial_failures` array (that's a `/v1/fetch` field) — gaps surface in the prose answer instead.
- `confidence` — `high | medium | low | unknown`. Reflects the *weakest* citation used. Any `medium` or `low` field pulls the overall down.
- `citations` — one entry per source, with the list of `fields` that source contributed.
- `fields_used` — flat array of catalog field names. Use this to re-verify the answer deterministically via `/v1/fetch`.
- `trace` (only with `include_trace: true`) — planner reasoning, the planner & synthesizer model names, requested fields, and any preset expansion. Useful when debugging "why did it pick those fields?"
- `geocode` (only when you sent an `address`) — how the coordinate was derived. Same block [`/v1/fetch`](#post-v1fetch-named-fields-with-provenance) returns; read `parcel_grade` before trusting any parcel-specific claim in the answer.

**When the address could only be estimated**, the caveat is appended to the `answer` prose itself, not just left in the `geocode` block. That is deliberate and it is done by the API, not the model — an answer relayed onward without its JSON still carries the uncertainty. Do not strip it.

**Latency:** 2–6 s warm, up to 60 s on cold start. Add up to 5.5 s if you send an `address` instead of a coordinate (see [`/v1/geocode`](#post-v1geocode-address-to-coordinate)); a repeat address is cached and adds effectively nothing.

### `POST /v1/ask/stream` — streaming answers

Same request body as `/v1/ask` (`lat`+`lng` **or** `address`, plus `question` and `include_trace`), but the answer streams back as **Server-Sent Events** so you can render tokens as they arrive. Events carry incremental `answer` text plus the accumulating `citations`; a final event delivers the complete record (`answer`, `confidence`, `citations`, `fields_used`, `answered_at`). Use this to drive a responsive UI; use `/v1/ask` when you just want the final JSON.

**If you sent an `address`, you must read the `final` event.** The `geocode` block — and the imprecision caveat appended to `answer` — arrive only on `final`. The `delta` frames carry the synthesizer's raw text, so a client that renders deltas and never reconciles against `final` displays an answer with the caveat missing.

```bash
curl -N -X POST https://api.mireye.com/v1/ask/stream \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{"lat": 40.7128, "lng": -74.0060, "question": "Wildfire risk here?"}'
```

### `POST /v1/fetch` — named fields with provenance

Request specific catalog fields (or a preset bundle). Returns each one with full provenance. Failed fields go to `partial_failures` — successful (and validly absent) ones are still returned in a 200 response.

```bash
# Named fields
curl -X POST https://api.mireye.com/v1/fetch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "lat": 40.7128,
    "lng": -74.0060,
    "fields": ["elevation", "coast_distance_m", "within_floodplain_polygon"]
  }'

# Preset
curl -X POST https://api.mireye.com/v1/fetch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{"lat": 29.7604, "lng": -95.3698, "preset": "flood_risk"}'

# Preset + extra named fields (deduplicated, max 50 total after expansion)
curl -X POST https://api.mireye.com/v1/fetch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "lat": 29.7604,
    "lng": -95.3698,
    "preset": "flood_risk",
    "fields": ["tree_canopy_pct"]
  }'
```

| Field    | Type     | Required                         | Description                                                                                                    |
| -------- | -------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `lat`    | number   | One of `lat`+`lng` / `address`   | Latitude in `[18, 72]`. Requires `lng`.                                                                        |
| `lng`    | number   | One of `lat`+`lng` / `address`   | Longitude in `[-180, -65]`. Requires `lat`.                                                                    |
| `address`| string   | One of `lat`+`lng` / `address`   | US street address, 1–256 chars. Resolved server-side; the response gains a `geocode` block.                    |
| `fields` | string[] | One of `fields`/`preset`         | Named catalog fields. See [Field catalog](#field-catalog) or call `/v1/meta/fields` for the live list.         |
| `preset` | string   | One of `fields`/`preset`         | Preset name. Expands server-side, unioned with `fields`, deduplicated. Max 50 fields after expansion.          |

**You can send a US street address instead of a coordinate.** `/v1/ask` and
`/v1/fetch` accept `address` in place of `lat`+`lng` — exactly one of the two;
both or neither is a `422 invalid_locator`. The response then carries a
`geocode` block:

```json
"geocode": {
  "accuracy_type": "rooftop",
  "provider": "geocodio",
  "source": "City of New York",
  "normalized_address": "350 5th Ave, New York, NY 10118",
  "parcel_grade": true,
  "precision_note": null
}
```

**Check `parcel_grade` before trusting parcel-specific fields.** `false` means
the coordinate was estimated along a street centerline rather than matched to a
building — up to ~2,872 m out in rural areas, far enough to describe a
neighbouring property. Compare `normalized_address` against what the user typed;
the geocoder resolves to the closest match it can find, which may be a different
street or town. On `/v1/ask` that caveat is appended to the answer text too.

**Budget an extra 5.5 s when you send an `address`.** The coordinate is resolved
before the field fan-out starts, and that resolution is worst-case 3 s (primary
provider) + 2.5 s (fallback) on top of the normal fetch time. A repeat address
is cached and adds effectively nothing.

Use [`POST /v1/geocode`](#post-v1geocode-address-to-coordinate) directly when you
want the coordinate on its own — to inspect before spending a fetch, or to reuse
across many calls.

**Response (200) — per-field shape:**

```json
{
  "lat": 40.7128,
  "lng": -74.006,
  "fetched_at": "2026-06-24T22:15:11.420Z",
  "fields": {
    "elevation": {
      "value": 13.15,
      "unit": "meters",
      "source": "USGS_3DEP",
      "source_url": "https://epqs.nationalmap.gov/",
      "confidence": "high",
      "dataset_vintage": "2023",
      "fetched_at": "2026-06-24T22:15:10.110Z",
      "ttl_seconds": 31536000,
      "status": "ok",
      "notes": null
    }
  },
  "partial_failures": []
}
```

- `value` — typed per the catalog (`float`, `int`, `bool`, or `string`); `null` when `status` is `absent`.
- `unit` — SI string like `"meters"`, `"percent"`, or `null` for dimensionless and enum fields.
- `source`, `source_url` — source identifier and canonical upstream URL (always HTTPS). Use `source_url` to independently re-fetch and verify any value.
- `confidence` — `high | medium | low | unknown`.
- `dataset_vintage` — the edition/year of the upstream dataset the value came from (e.g. `"2024"`), or `null` when the source doesn't expose one. Distinct from `fetched_at`.
- `fetched_at` — when *Mireye* hit the upstream source. Authoritative "as-of" time for the value.
- `ttl_seconds` — how long the value is considered fresh, derived from the upstream update cadence. Use this for your own cache TTL. Ranges from 1 day to 1 year (USGS elevation, Census boundaries).
- `status` — `"ok"` (real value) or `"absent"` (source confirmed no data here; a valid semantic null, not an error). Failed fields never appear here — they go to `partial_failures`.
- `notes` — human-readable caveats (e.g., cloud-screening for NDVI, geometric-overlap confidence for building joins, why a field is absent), or `null`.

**Partial failures:**

```json
{
  "partial_failures": [
    {
      "field": "lcms_class",
      "source": "USFS_LCMS",
      "error": "TimeoutError: source timed out after 10s",
      "retryable": true
    }
  ]
}
```

Check `partial_failures` on every call. `retryable: true` → transient upstream blip, retry. `retryable: false` → permanent (e.g., no coverage), don't.

**Latency:** 1–3 s warm; up to 5.5 s more when the location is an `address` rather than a coordinate.

### `POST /v1/fetch/batch` — many locations, one field selection

The batch form of `/v1/fetch`: one field selection applied to a list of locations, each `lat`+`lng` or `address`. Use it to screen a candidate list — a supplier book, a portfolio, a set of parcels — in one call.

```bash
curl -X POST https://api.mireye.com/v1/fetch/batch \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "locations": [
      {"lat": 40.7128, "lng": -74.0060},
      {"address": "350 5th Ave, New York, NY 10118"}
    ],
    "fields": ["elevation", "within_floodplain_polygon"]
  }'
```

| Field       | Type     | Required                 | Description                                                                                                     |
| ----------- | -------- | ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `locations` | object[] | Yes                      | 1–25 entries. Each is the exact locator contract of `/v1/fetch`: `lat`+`lng` **or** `address`, never both, never neither. |
| `fields`    | string[] | One of `fields`/`preset` | Named catalog fields, applied to every location.                                                                |
| `preset`    | string   | One of `fields`/`preset` | Preset name, applied to every location. Same 50-field cap on explicitly named fields as `/v1/fetch`.            |

**The field selection is batch-wide, not per-location.** The batch exists for "the same screen over a list of candidate properties", and per-location field lists would make the response shape unpredictable for exactly the clients — agents, spreadsheets — the batch serves.

**Response (200) — key fields:**

```json
{
  "fetched_at": "2026-08-03T18:02:11.004Z",
  "results": [
    {
      "index": 0,
      "ok": true,
      "lat": 40.7128,
      "lng": -74.006,
      "fetched_at": "2026-08-03T18:02:10.882Z",
      "fields": { "elevation": { "value": 13.15, "unit": "meters", "status": "ok" } },
      "partial_failures": [],
      "resolved_location": { "lat": 40.7128, "lng": -74.006, "source": "coordinate" }
    },
    {
      "index": 1,
      "ok": false,
      "error": { "error": "address_too_coarse", "message": "...", "retryable": false }
    }
  ]
}
```

- `results` is **index-aligned with the `locations` you sent**, and every entry repeats its own `index` — so a partly-failed batch is still unambiguous.
- An `ok: true` entry is the same shape as a `/v1/fetch` response body, `partial_failures` included. Read that array per location exactly as you would on the single endpoint (Gotcha 4 applies per entry, not per batch). An entry whose locator was an `address` also carries the `geocode` block.
- An `ok: false` entry carries the same error object the single endpoint would have returned for that location. **One bad location never fails the batch.**
- An unknown field name is the one exception: it's the caller's mistake and identical for every location, so it fails the whole request up front rather than returning 25 copies of the same error.
- Running out of credits mid-batch keeps the results already produced and returns `credits_exhausted` entries for the rest.

**Billing:** one call against your rate limit, and credits for `fields × locations` — charged only for locations that actually run.

**Latency:** locations run 4 at a time, so a full 25-location batch of cold locations can take ~84 s worst case. That bound is why the cap is 25; size your client timeout for it.

### `POST /v1/runs` — submit a job, collect it later

The async form of the long-running endpoints. Submit returns `202` with a `run_id` immediately and the work continues server-side, so you can read its state from anywhere — the worker answering your poll is rarely the worker doing the work. Use it when the job is too long to hold a connection open for, or when the client that submits isn't the client that collects.

```bash
curl -X POST https://api.mireye.com/v1/runs \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "kind": "fetch_batch",
    "request": {
      "locations": [{"lat": 40.7128, "lng": -74.0060}],
      "preset": "flood_risk"
    }
  }'
```

```json
{
  "run_id": "run_...",
  "status": "queued",
  "poll": "/v1/runs/run_...",
  "events": "/v1/runs/run_.../events"
}
```

| Field     | Type   | Required | Description                                                                       |
| --------- | ------ | -------- | --------------------------------------------------------------------------------- |
| `kind`    | string | Yes      | `fetch_batch` — the only kind today.                                              |
| `request` | object | Yes      | The `/v1/fetch/batch` request shape, with the same validation and the same limits. |

**Caller mistakes fail at submit, not minutes later.** Field names and locators are validated synchronously, so a bad request is an error on the POST rather than a failed run you have to go read.

**`GET /v1/runs/{run_id}` — poll.** The source of truth. Returns status and progress, plus the result or error once terminal:

| Field                                            | Notes                                                                            |
| ------------------------------------------------ | -------------------------------------------------------------------------------- |
| `status`                                         | `queued` → `running` → `done` or `failed`. `done` and `failed` are terminal.      |
| `progress`                                       | `{"done": n, "total": n}`.                                                        |
| `result`                                         | The full `/v1/fetch/batch` response body once `done`; `null` before that.          |
| `error`                                          | Set on `failed`.                                                                  |
| `kind` / `request` / `created_at` / `updated_at` / `expires_at` | Echoed back.                                                       |

**`GET /v1/runs/{run_id}/events` — stream (SSE).** A `status` frame on every state or progress change, and a terminal `final` frame carrying the full run body. It's a convenience over polling, not a second source of truth: the stream is capped at 15 minutes, after which it emits a retryable `events_timeout` and you go back to the poll endpoint.

**`GET /v1/runs/{run_id}/artifacts/{fmt}` — download.** `csv` (one row per location, spreadsheet-ready values) or `geojson` (a FeatureCollection, one Point per location). Rendered on read, so the artifact exists exactly as long as the run does. A run still `queued` or `running` is `409 run_not_ready` (retryable — keep polling); a run that produced no result is `409 run_failed` (resubmit it).

**Ownership and expiry.** A run belongs to the account that submitted it — someone else's `run_id` reads as `404 run_not_found`, never a `403`, so the endpoint can't be used to test whether an id exists. Runs expire **30 days** after submission, and their artifacts expire with them.

**Billing:** priced identically to the synchronous `/v1/fetch/batch` it wraps — asking for the work asynchronously doesn't dodge the meter. The rate-limit slot is spent at submit and the per-location credits as the run executes, so a run interrupted mid-flight bills only the locations it completed. The three reads are unmetered.

### Presets

Fifteen presets ship today. Pass the name as `preset` on `/v1/fetch`.

**The `Fields` column is a sample, not the expansion.** Counts are live as of this writing; the membership itself changes as the catalog grows, and an exhaustive list here would be wrong within a release — it already was. Read `GET /v1/meta/fields` under `presets` for the authoritative expansion.

| Preset                | What it's for | Fields |
| --------------------- | ------------- | ------ |
| `terrain` | Topography & soils basics (6 fields) | `elevation`, `slope_degrees`, `aspect_cardinal`, `coast_distance_m`, `soil_drainage_class`, `bedrock_depth_cm` |
| `flood_risk` | Floodplain, wetlands, water (13 fields) | `elevation`, `coast_distance_m`, `within_floodplain_polygon`, `intersects_nhd_area`, `intersects_wetland`, `wetland_type`, … (+7 more) |
| `wildfire_underwrite` | Wildfire fuel & terrain (6 fields) | `lcms_class`, `tree_canopy_pct`, `ndvi_current`, `ndvi_change_5y`, `slope_degrees`, `elevation` |
| `land_cover` | Land use & crops (5 fields) | `lcms_class`, `land_use_class`, `tree_canopy_pct`, `cdl_class`, `dominant_crop_5y` |
| `site_selection` | General development screen (54 fields) | `elevation`, `slope_degrees`, `lcms_class`, `within_floodplain_polygon`, `intersects_wetland`, `wetland_type`, … (+48 more) |
| `building_lookup` | Primary structure attributes (4 fields) | `primary_building_overture_class`, `primary_building_height_m`, `primary_building_num_floors`, `primary_building_footprint_sqm` |
| `utilities` | Power, transmission, gas (18 fields) | `nearest_power_plant_name`, `nearest_power_plant_distance_m`, `nearest_power_plant_primary_fuel`, `nearest_power_plant_capacity_mw`, `nearest_transmission_line_distance_m`, `nearest_transmission_line_voltage_kv`, … (+12 more) |
| `boundaries` | Jurisdiction & Census (4 fields) | `political_region`, `political_county`, `political_locality`, `tract_geoid` |
| `natural_hazard` | Multi-peril hazard screen (14 fields) | `seismic_pga_2pct_50yr_g`, `seismic_design_category`, `design_wind_speed_mph`, `wildfire_annual_frequency`, `tornado_annual_frequency`, `hail_annual_frequency`, … (+8 more) |
| `grid_interconnect` | Transmission & interconnection (29 fields) | `nearest_substation_distance_m`, `nearest_substation_max_voltage_kv`, `nearest_substation_status`, `electric_utility_service_territory`, `interconnection_queue_active_capacity_county_mw`, `wind_least_cost_interconnect_distance_m`, … (+23 more) |
| `data_center_siting` | Power, water, cooling, fiber, risk (90 fields) | `nearest_substation_distance_m`, `nearest_substation_max_voltage_kv`, `nearest_substation_status`, `electric_utility_service_territory`, `avg_retail_electricity_price_industrial_usd_per_kwh`, `egrid_subregion`, … (+84 more) |
| `solar_siting` | PV resource & land (27 fields) | `ghi_annual_kwh_m2_day`, `dni_annual_kwh_m2_day`, `pv_capacity_factor_pct`, `pv_specific_yield_kwh_per_kw`, `optimal_fixed_tilt_degrees`, `surface_albedo_annual`, … (+21 more) |
| `wind_siting` | Wind resource & land (26 fields) | `mean_wind_speed_100m_ms`, `mean_wind_speed_120m_ms`, `mean_wind_speed_160m_ms`, `wind_power_density_100m_wm2`, `prevailing_wind_direction_100m_cardinal`, `weibull_k_100m`, … (+20 more) |
| `storage_siting` | Battery storage siting (20 fields) | `nearest_substation_distance_m`, `nearest_substation_max_voltage_kv`, `nearest_substation_status`, `electric_utility_service_territory`, `avg_retail_electricity_price_industrial_usd_per_kwh`, `egrid_co2_output_rate_kg_per_mwh`, … (+14 more) |
| `points_of_interest` | Nearby amenities and landmarks (23 fields) | `nearest_hospital_distance_m`, `nearest_hospital_name`, `nearest_fire_station_distance_m`, `nearest_fire_station_name`, `nearest_school_distance_m`, `nearest_school_name`, … (+17 more) |
You can combine a preset with extra named `fields` in the same request — Mireye unions and deduplicates them. The 50-field cap applies to fields you name EXPLICITLY; preset members are exempt, because a preset the API ships must always be fetchable through its own `preset` parameter. So `data_center_siting` (90 fields) is a single valid call, and you still have all 50 explicit slots on top of it.

### `POST /v1/geocode` — address to coordinate

Resolve a US street address to a coordinate, **plus how that coordinate was
derived**. Most of the time you do not need this: `/v1/ask` and `/v1/fetch`
accept `address` directly. Use it when you want the coordinate on its own — to
inspect before spending a fetch, or to reuse across many calls.

```bash
curl -X POST https://api.mireye.com/v1/geocode \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"address": "350 5th Ave, New York, NY 10118"}'
```

```json
{
  "lat": 40.748377,
  "lng": -73.984854,
  "accuracy": 1.0,
  "accuracy_type": "rooftop",
  "match_type": "building_centroid",
  "normalized_address": "350 5th Ave, New York, NY 10118",
  "provider": "geocodio",
  "source": "City of New York"
}
```

**`accuracy_type` is the field that matters**, and you must branch on it:

| value | grade | meaning |
| --- | --- | --- |
| `rooftop`, `nearest_rooftop_match` | parcel | on the building. Safe for parcel-level work. |
| `point`, `range_interpolation`, `intersection`, `street_center` | street | **estimated**. Up to ~2,872 m out in rural areas. |
| `place`, `county`, `state` | centroid | rejected — you will never receive one. |

`accuracy` is a different question: how confident the provider is it matched the
**right** address, not how precisely it placed it. Below `0.8` is rejected.

`source` names the authority behind the coordinate — `City of New York`,
`TIGER/Line® from the US Census Bureau`. A municipal parcel layer and a federal
street-centerline file are not equally good, so it is a second quality signal
independent of `accuracy_type`.

**Things that are refused rather than guessed at**, because a confident wrong
coordinate is worse than an error:

- an address that resolves only to a ZIP/city/county centroid → `404 address_too_coarse`
- a low-confidence match → same code (the provider was guessing)
- a PO box, carrier route, military APO/FPO, general delivery → `422 address_form_unsupported`; these are mail destinations with no parcel
- an address outside the US → `404 address_not_found`

**The fallback, and what `provider` tells you.** If the primary provider exceeds
its 3 s deadline, Mireye falls back to the free US Census geocoder rather than
failing the request — on **timeout only**, never on a missing key, an auth
failure, or a no-match, because those must surface rather than be papered over
with a lower-precision answer. The fallback is a real degradation: it always
reports `accuracy_type: "range_interpolation"`, and it publishes no similarity
score, so `accuracy` comes back `null` (absent, not zero — do not treat it as a
failing score). `provider: "census"` is your signal that you are on that path.

**Known limitation.** In Puerto Rico and Guam, provider coverage is thin and its
confidence score does not reflect that — a wrong street or ZIP can come back at
0.99. Compare `normalized_address` against what the user typed; for territory
addresses treat that as required.

**Limits:**

- **One address per request.** No batching — loop client-side.
- **256 characters maximum.** Over that is rejected, never truncated, so a long
  address can never be silently shortened into a different one.
- **Cached: 30 days on success, 24 hours on "no such address."** A repeat lookup
  of the same address within the window is free and instant. 30 days is not a
  performance choice — the cache holds the matched address, so it expires on the
  same clock as everything else address-derived (below). The cache key
  normalizes form only —
  case, spacing, accents, punctuation — but deliberately does **not** treat
  `Avenue` and `Ave` as the same word, so two spellings of one address cost
  two lookups. The short negative TTL is on purpose: an address the provider has
  not ingested yet starts working as soon as it does.
- **US only.** Feed the coordinate to `/v1/fetch` or `/v1/ask`, which enforce the
  US envelope.

**Latency:** worst case 5.5 s (3 s primary + 2.5 s fallback). Set your client
timeout above that. A cached address returns effectively instantly.

**The address is recorded, for 30 days.** If you are passing along an end user's
address, tell them, or do not pass it.

Mireye stores the address as sent, the coordinate it resolved to, and the
`geocode` block, so that a disputed result can be audited later — with only a
coordinate and an answer there is no way to distinguish a bad match from a typo.

Two stores hold it, and every copy is removed on the same 30-day clock.
Neither removal depends on a scheduled job staying configured:

- **The audit record** — address as typed, coordinate, `geocode` block. The API
  strips the address fields out of its own stored rows on a rolling check once
  they pass 30 days. The emptied row is cleared later by a partition drop, so
  the record itself can persist 30 to about 60 days — but it holds no address
  by then. The drop is storage housekeeping; the removal above is the part that
  concerns you.
- **The result cache** — the matched address and coordinate, keyed by a digest
  of what you sent, kept so a repeat lookup does not re-bill. Expires at 30 days
  via the store's own TTL.

Nothing is kept beyond that.

**If Mireye cannot remove expired addresses, it stops recording them.** That
removal runs inside the serving process, and accepting an address is
conditional on it demonstrably working — if the process ever cannot strip
expired addresses, it refuses to store new ones until it can. The component
that accepts your address is the component that deletes it, so the promise
cannot outlive the machinery behind it.

Not done: no hash of the address is stored beside it (over an address space this
small a hash is a lookup key, not anonymity), and the address is held in one
structured field rather than copied into logs.

**Opt out by geocoding client-side** and calling `/v1/fetch` or `/v1/ask` with
`lat`/`lng`. A coordinate request stores no address, because none was sent.

### `POST /v1/lookup` — canonical join keys

`/v1/geocode` answers "where is this address." `/v1/lookup` answers a
different question: "what are the canonical join keys for this place, and how
confident should I be" — and it takes any of an address, a `"lat,lng"` pair, or
an APN, not just a clean address. Use it when the input might be ambiguous,
when you want a parcel attached, or when you don't already know the input's
shape.

```bash
curl -s https://api.mireye.com/v1/lookup \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"input": "480 Berdoll Ln, Cedar Creek TX"}' | jq
```

```json
{
  "disposition": "resolved",
  "lat": 30.199699,
  "lng": -97.496411,
  "resolved_address": "480 BERDOLL LN, CEDAR CREEK, TX 78612",
  "county_fips": "48021",
  "county": "Bastrop County",
  "tract_geoid": "48021950400",
  "parcel": {
    "parcel_id": "R123456",
    "apn": "...",
    "geometry": "...",
    "owner": "PECAN GROVE FARMS #1 LLC",
    "source": "REGRID",
    "match_distance_m": 4.2
  },
  "match_method": "geocode_rooftop+point_in_parcel",
  "confidence": 0.95
}
```

Every response says how it resolved, via `disposition`:

| value | meaning |
| --- | --- |
| `resolved` | a coordinate, plus a parcel when the geocode cleared parcel-quality accuracy. |
| `clarify` | the input is genuinely ambiguous — multiple plausible matches at comparable confidence. You get `candidates` (up to 5), never a silent pick. |
| `no_match` | an honest failure, with a `reason`. |

**Why `clarify` exists.** An unqualified "1100 King St W, Toronto" can land on
Toronto, Ontario *or* Toronto, Ohio at similar confidence — a single top-ranked
geocode result can never reveal that a comparably-good alternative existed.
`/v1/lookup` checks multiple candidates specifically so it can tell you when
that's happened:

```json
{
  "disposition": "clarify",
  "candidates": [
    { "resolved_address": "1100 King St W, Toronto, ON, Canada", "lat": 43.6394, "lng": -79.4223, "confidence": 0.82 },
    { "resolved_address": "1100 King St W, Toronto, OH 45871", "lat": 41.0284, "lng": -84.3247, "confidence": 0.80 }
  ]
}
```

Present the candidates to the user (or use a disambiguation hint you have —
state, county) rather than picking the first one.

**A parcel-lookup failure never demotes a good geocode.** If the parcel vendor
is unavailable — including a plan/quota issue on Mireye's end — the geocode
still comes back honestly, just without a parcel:

```json
{
  "disposition": "resolved",
  "lat": 38.8977,
  "lng": -77.0365,
  "resolved_address": "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC",
  "parcel_unavailable": true,
  "parcel_unavailable_reason": "regrid_quota_exhausted",
  "match_method": "geocode_rooftop",
  "confidence": 0.95
}
```

This never becomes a 5xx and never demotes `disposition` away from `resolved`
— only the parcel attempt failed, and the response says exactly why
(`regrid_quota_exhausted`, `no_parcel_at_point`, `parcel_match_too_far`,
`parcel_lookup_transient_error`, `parcel_lookup_malformed_response`). Below
parcel-quality accuracy, the parcel lookup is never even attempted — the same
`accuracy_type` gate that protects `/v1/geocode`.

**Swapped coordinates are a hard error, never a nearest-match.** `"-73.9,40.7"`
(lng,lat instead of lat,lng) returns `422 resolve_coord_bounds` rather than a
plausible-looking wrong point — a transposed lat/lng is a caller bug, not an
ambiguous location.

**APN-only lookup is not supported yet.** Regrid's only wired integration here
is a point (lat/lng) lookup, so an APN-shaped input returns a clean `no_match`
with `reason: "apn_not_supported_in_v1"`.

**Response fields:**

| Field | Notes |
| --- | --- |
| `disposition` | `resolved`, `clarify`, or `no_match`. |
| `lat` / `lng` | present on `resolved`. |
| `resolved_address` | the address the geocoder actually matched, when input was an address. |
| `county_fips` / `county` / `tract_geoid` | best-effort, from the free Census Geocoder — `null` if it's unreachable; never fails the request. |
| `parcel` | present only when a parcel-quality geocode found a trustworthy parcel. |
| `parcel_unavailable` / `parcel_unavailable_reason` | see above. |
| `match_method` / `confidence` | present on `resolved`. One confidence scale throughout. |
| `candidates` | present only on `clarify`. |
| `reason` / `hint` | present only on `no_match`. |

**Errors specific to this endpoint:**

| Error code | HTTP | Retryable | Meaning |
| --- | --- | --- | --- |
| `resolve_coord_bounds` | 422 | no | coordinate outside any plausible bound, incl. swapped lat/lng. |
| `resolve_invalid_input` | 422 | no | input didn't parse as an address, coordinate, or APN-shaped token. |
| `resolve_busy` | 429 | yes | per-worker overload gate — resolve has its own, separate from `/v1/geocode`'s. `Retry-After: 3`. |
| `resolve_timeout` | 504 | yes | did not complete within the endpoint's deadline. `Retry-After: 5`. |

A propagated address-leg failure shares `/v1/geocode`'s error taxonomy exactly
(`address_form_unsupported`, `geocode_unconfigured`, `geocode_forbidden`,
`geocode_timeout`, `geocode_upstream_error`) — a parcel-leg failure never is
one of these; it degrades the response instead, as above.

**Limits:** one input per request (no batching); 256 characters maximum,
rejected rather than truncated; US only; address-leg caching follows
`/v1/geocode`'s rules exactly (same cache backs both) — see its Limits section
above; parcel data depends on Regrid, and there is no free parcel tier.

**Retention matches `/v1/geocode`** (above): the input you send, when it's an
address, is recorded alongside the coordinate it resolved to, for 30 days, so
a result can be audited later. Opt out the same way — resolve client-side and
call `/v1/fetch` or `/v1/ask` with `lat`/`lng` instead.

### `GET /v1/meta/fields` — discover the catalog

Returns the complete machine-readable catalog: all 250+ fields (each with `name`, `type`, `unit`, `description`, `interpretation_hints`, `layer`, `source`, `source_url`, `ttl_seconds`, `lifecycle`, `nullable`, `null_meaning`, and `presets` membership), the 15 preset expansions, and the US envelope. Public (no auth), served from memory, sub-50 ms, ETag-cached.

```bash
curl -i https://api.mireye.com/v1/meta/fields
```

Subsequent requests should use the ETag:

```bash
curl -i https://api.mireye.com/v1/meta/fields \
  -H 'if-none-match: "abc123..."'
# 304 Not Modified means your cached body is still valid
```

**Response headers:**

| Header          | Value                                                                |
| --------------- | -------------------------------------------------------------------- |
| `ETag`          | SHA-256 of the body as a quoted string.                              |
| `Cache-Control` | `public, max-age=3600` — safe to cache up to one hour.               |

**Response body (abridged):**

```json
{
  "version": "0.14.0",
  "us_envelope": { "lat_min": 18, "lat_max": 72, "lng_min": -180, "lng_max": -65 },
  "fields": [
    {
      "name": "elevation",
      "type": "float",
      "unit": "meters",
      "description": "Ground elevation above the NAVD88 vertical datum at the queried point. Sourced from USGS 3DEP / EPQS at ~10m native resolution.",
      "interpretation_hints": "Below 10m within 5km of the coast → storm-surge exposure relevant. Above 3000m → alpine permitting, snow loads. Combine with coast_distance_m and within_floodplain_polygon for flood-zone reasoning.",
      "layer": "terrain",
      "source": "USGS_3DEP",
      "source_url": "https://epqs.nationalmap.gov/",
      "ttl_seconds": 31536000,
      "lifecycle": "stable",
      "nullable": false,
      "null_meaning": null,
      "presets": ["terrain", "flood_risk", "site_selection", "wildfire_underwrite", "..."]
    }
  ],
  "presets": {
    "flood_risk": ["elevation", "coast_distance_m", "within_floodplain_polygon", "..."]
  }
}
```

For long-running clients: fetch once at startup, store the ETag, send `If-None-Match` on every subsequent request. The catalog only changes on schema-version bumps.

### Field catalog

250+ fields across 7 layers. Fields in the same layer fetch in parallel — asking for more fields from the same layer adds no extra latency. The live catalog at `GET /v1/meta/fields` is the authoritative source; the names below are a snapshot.

**Layer 1 — Terrain** (USGS 3DEP / NHDPlus HR / WBD, USDA SSURGO / STATSGO, USFWS NWI, NOAA CUSP, JRC GSW, FEMA NFHL)

`elevation`, `slope_degrees`, `aspect_degrees`, `aspect_cardinal`, `coast_distance_m`, `soil_drainage_class`, `soil_map_unit_name`, `bedrock_depth_cm`, `prime_farmland_classification`, `soil_shrink_swell_class`, `intersects_nhd_area`, `nearest_flowline_name`, `nearest_waterbody_name`, `huc_12_name`, `within_floodplain_polygon`, `surface_water_permanence_pct`, `intersects_wetland`, `wetland_type`, `wetland_subtype`, `wetland_acres`, `nearest_wetland_distance_m`, `wetlands_within_100m_count`, `wetlands_within_500m_count`

**Layer 2 — Land Cover** (USFS LCMS, NLCD TCC, Sentinel-2, USDA CDL)

`lcms_class`, `land_use_class`, `tree_canopy_pct`, `ndvi_current`, `ndvi_change_5y`, `cdl_class`, `is_cultivated`, `dominant_crop_5y`

**Layer 3 — Built Environment** (Overture Buildings & Transportation, FHWA NBI, USWTDB, USPVDB, EPA Repowering, HUD Opportunity Zones)

`primary_building_height_m`, `primary_building_num_floors`, `primary_building_footprint_sqm`, `primary_building_overture_class`, `nearest_major_road_name`, `nearest_major_road_distance_m`, `nearest_bridge_name`, `nearest_wind_turbine_distance_m`, `nearest_wind_turbine_hub_height_m`, `nearest_wind_turbine_total_height_m`, `nearest_wind_project_capacity_mw`, `nearest_utility_solar_facility_distance_m`, `nearest_utility_solar_facility_capacity_mw`, `nearest_repowering_site_distance_m`, `in_opportunity_zone`, `opportunity_zone_tract_geoid`

**Layer 4 — Utilities & Energy** (EIA Atlas / 860M / power / prices / gas / shale, EPA eGRID / SDWIS / CWS, LBNL Queued Up, FAA NASR, FCC ASR / BDC, BTS NTAD / Ports, US Census urban, USGS NWIS / thermoelectric / sedimentary basins / IWAA)

`nearest_power_plant_name`, `nearest_power_plant_distance_m`, `nearest_power_plant_primary_fuel`, `nearest_power_plant_capacity_mw`, `nearest_transmission_line_distance_m`, `nearest_transmission_line_voltage_kv`, `nearest_transmission_line_voltage_class`, `nearest_transmission_line_voltage_basis`, `nearest_transmission_line_status`, `nearest_transmission_line_owner`, `max_transmission_line_voltage_kv_within_radius`, `max_transmission_line_voltage_class_within_radius`, `transmission_lines_within_radius_count`, `nearest_substation_distance_m`, `nearest_substation_max_voltage_kv`, `nearest_substation_status`, `electric_utility_service_territory`, `egrid_subregion`, `egrid_co2_output_rate_kg_per_mwh`, `avg_retail_electricity_price_industrial_usd_per_kwh`, `interconnection_queue_active_capacity_county_mw`, `nearest_proposed_generator_distance_m`, `nearest_gas_pipeline_distance_m`, `nearest_gas_compressor_distance_m`, `nearest_gas_storage_distance_m`, `nearest_lng_terminal_distance_m`, `natural_gas_citygate_price_usd_per_mcf`, `natural_gas_industrial_price_usd_per_mcf`, `in_shale_play`, `nearest_shale_play_name`, `sedimentary_basin_name`, `nearest_public_water_system_name`, `public_water_system_population_served`, `surface_water_supply_use_index_huc12`, `huc12_thermoelectric_consumptive_use_m3_per_day`, `nearest_groundwater_well_depth_to_water_m`, `fiber_provider_count`, `fiber_broadband_available`, `mobile_5g_coverage_class`, `nearest_urban_area_distance_m`, `nearest_rail_line_distance_m`, `nearest_airport_name`, `nearest_airport_distance_m`, `nearest_port_name`, `nearest_antenna_structure_distance_m`, `nearest_antenna_structure_height_m`, `nearest_antenna_structure_type`, `nearest_antenna_structure_owner`, `antenna_structures_within_500m_count`, `antenna_structures_within_2km_count`

**Layer 5 — Climate & Resource** (NREL NSRDB / PVWatts / Wind Toolkit / reV / Solar Resource, NOAA NCEI nClimGrid & Normals / NSIDC MODIS snow-cover duration / ASCE wind, US Drought Monitor)

`ghi_annual_kwh_m2_day`, `dni_annual_kwh_m2_day`, `pv_capacity_factor_pct`, `pv_specific_yield_kwh_per_kw`, `optimal_fixed_tilt_degrees`, `surface_albedo_annual`, `mean_wind_speed_100m_ms`, `mean_wind_speed_120m_ms`, `mean_wind_speed_160m_ms`, `wind_power_density_100m_wm2`, `prevailing_wind_direction_100m_cardinal`, `weibull_k_100m`, `wind_capacity_factor_pct`, `wind_least_cost_interconnect_distance_m`, `design_wet_bulb_temperature_0_4pct_degc`, `mean_annual_dry_bulb_temperature_degc`, `mean_annual_relative_humidity_pct`, `days_above_32c_annual_count`, `mean_annual_snow_cover_days`, `drought_category`

**Layer 6 — Hazards** (USGS NSHM seismic / landslide / DesignMaps ASCE7, FEMA NRI, NOAA ASCE wind vectors, USACE NID dams, EPA FRS RMP / SEMS / ACRES / Green Book, US Census)

`seismic_design_category`, `seismic_pga_2pct_50yr_g`, `design_wind_speed_mph`, `wildfire_annual_frequency`, `tornado_annual_frequency`, `hail_annual_frequency`, `lightning_annual_flash_days`, `landslide_susceptibility_index`, `nearest_dam_distance_m`, `nearest_dam_hazard_potential`, `high_hazard_dams_within_10km`, `nearest_hazardous_facility_distance_m`, `nearest_hazardous_facility_name`, `nearest_brownfield_distance_m`, `brownfields_within_radius_count`, `nearest_superfund_distance_m`, `superfund_sites_within_radius_count`, `in_air_quality_nonattainment`, `air_quality_nonattainment_pollutants`, `air_quality_worst_classification`, `housing_units_within_1km`, `housing_units_density_per_km2`

**Layer 7 — Parcels & Boundaries** (Overture Divisions, US Census TIGERweb & Geocoder, USGS PAD-US, Regrid, USFWS Critical Habitat & Golden Eagle, BLM SMA & Solar PEIS, FAA SUA)

`political_region`, `political_county`, `political_locality`, `tract_geoid`, `parcel_id`, `parcel_apn`, `parcel_owner`, `parcel_address`, `parcel_zoning`, `parcel_area_m2`, `parcel_geometry_wkt`, `parcel_boundary_geojson`, `parcel_data_source`, `parcel_match_type`, `parcel_match_distance_m`, `parcel_match_radius_m`, `intersects_conservation_easement`, `easement_holder`, `easement_type`, `easement_purpose`, `easement_acres`, `easement_year_established`, `intersects_protected_area`, `protected_area_name`, `protected_area_gap_status`, `protected_area_designation`, `protected_area_manager`, `protected_area_public_access`, `intersects_critical_habitat`, `critical_habitat_status`, `critical_habitat_species`, `critical_habitat_listing_status`, `surface_management_agency`, `blm_solar_application_land_status`, `special_use_airspace_type`, `golden_eagle_nest_density_index`

The live catalog at `GET /v1/meta/fields` is the authoritative source. Common naming mistakes:

- `elevation_m` → `elevation` (no unit suffix in the name)
- `flood_zone` → `within_floodplain_polygon` (use the full predicate name)
- `slope` → `slope_degrees` (unit suffix *is* required when ambiguous)
- `solar` / `ghi` → `ghi_annual_kwh_m2_day`, `dni_annual_kwh_m2_day` (resource fields carry the full unit)
- `wind_speed` → `mean_wind_speed_100m_ms` (hub height + unit are part of the name)
- `substation` → `nearest_substation_distance_m` / `nearest_substation_max_voltage_kv`
- `primary_building` → `primary_building_overture_class`, `primary_building_height_m`, `primary_building_num_floors`, `primary_building_footprint_sqm`
- `conservation_easement` → `intersects_conservation_easement` or `easement_holder`

### `POST /v1/field-requests` — order a field the catalog doesn't have

When the catalog doesn't answer your question, this is the surface that does something about it: you describe the field you need in plain language at 1–10 example locations, and Mireye matches the ask against the catalog **before** anything is built.

```bash
curl -X POST https://api.mireye.com/v1/field-requests \
  -H 'authorization: Bearer YOUR_MIREYE_TOKEN' \
  -H 'content-type: application/json' \
  -d '{
    "description": "Distance to the nearest active railroad grade crossing",
    "example_locations": [{"lat": 30.1997, "lng": -97.4964}],
    "idempotency_key": "your-stable-key"
  }'
```

| Field               | Type     | Required | Description                                                                                                                   |
| ------------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `description`       | string   | Yes      | The field you need, in plain language.                                                                                        |
| `example_locations` | object[] | Yes      | 1–10 entries; each carries exactly one of `address`, `lat`+`lng`, or `polygon`.                                                |
| `idempotency_key`   | string   | No       | **Always send one from an agent.** The same key replays the existing request's state instead of filing a second build; the same key with a *different* ask is a `409`. |
| `use_case` / `decision_threshold` | string | No | What decision this feeds, and the value that flips it. Optional, but both sharply improve match quality and build speed.        |
| `context_blob`      | string   | No       | Free-text context. Excluded from the idempotency fingerprint.                                                                 |
| `callback`          | object   | No       | Where to notify you when the build lands. Also excluded from the fingerprint, so repairing a webhook URL doesn't fork a second request. |

Only `description` and `example_locations` are required. Unknown keys are rejected rather than ignored — see [docs.mireye.ai/api-reference/field-requests](https://docs.mireye.ai/api-reference/field-requests) for the full entry shape and the rarer structured fields.

**Four outcomes, and only one of them builds anything:**

- `matched_existing` / `partial` — a catalog field already answers the ask. You get the value now with its citation, and no build is spent.
- `near_miss_confirm` — something close exists. You accept or reject it; it is never silently substituted.
- `accepted_new` — a genuine gap. The field is queued to build and you get a `request_id`, a queue position, and an `estimated_ready_at`.
- `rejected` — a typed `rejection_code` plus a `routing_hint`, never a bare no.

A genuinely ambiguous example location returns a stateless `clarify` with candidates and creates **no** request state — re-POST with a disambiguated location. If screening can't finish inside its ~10 s budget the response is `received` plus the `request_id` and screening completes in the background; nothing is ever queued without being screened.

**`GET /v1/field-requests/{request_id}` — poll.** Status, queue position, the event history, the promised `estimated_ready_at` (fixed at acceptance, never recomputed on poll), and — once the status is `live` — a `resume` blob: a ready-to-send `/v1/fetch` request that answers the original ask.

Status vocabulary: `received` / `screening` (still being screened — check `waiting_on`; `operator` means a human has to look), `matched` (the catalog already answered it — use `resume`), `awaiting_confirm` (a near miss or a clarify is waiting on you), `queued` / `claimed` / `building` / `in_review` / `approved` / `publishing` (a build is in progress), `live` (done), and the terminal `rejected` / `blocked` / `expired`.

**Store the `request_id` in durable task state, not conversation context.** Builds run on a scale of hours, so the session that filed the request will likely be gone before one finishes.

Requests are visible only to the credential that filed them. An id that doesn't exist — or that belongs to someone else — is the same `404`, never a `403`.

**Billing:** filing a request spends no fetch credits. Each plan carries its own included build allowance.

### Sites — persistent locations

For workflows that ask many questions about the *same* place, register it once and reference it by ID instead of re-sending the geometry each time.

- **`POST /v1/sites`** — register a site (point or area) and get back a `site_id`.
- **`GET /v1/sites/{site_id}`** — retrieve the stored site and its computed dossier.
- **`POST /v1/ask-site`** — natural-language Q&A scoped to a registered site: `{ "site_id": "...", "question": "..." }`. Same cited-answer shape as `/v1/ask`.

All three require a bearer token; sites are scoped to your account. Use the point queries (`/v1/ask`, `/v1/fetch`) for one-off lookups and Sites when you're building a persistent dossier.

### Error responses

| Status | Error code            | Meaning                                                                                                      |
| ------ | --------------------- | ------------------------------------------------------------------------------------------------------------ |
| 400    | `coord_out_of_bounds` | Coordinate outside `lat ∈ [18, 72]`, `lng ∈ [-180, -65]`.                                                    |
| 400    | `fields_unknown`      | One or more field names not in the catalog. Response includes `fields_unknown: [...]` listing the offenders. |
| 400    | `fields_too_many`     | More than 50 fields after preset expansion. Split into multiple requests.                                    |
| 400    | `no_fields_requested` | `/v1/fetch` called without `fields` or `preset`.                                                             |
| 401    | `unauthorized`        | Missing, expired, or revoked bearer token. Re-authenticate.                                                  |
| 403    | `forbidden`           | Valid token, but the account is not permitted by backend policy.                                             |
| 404    | `address_not_found`   | Geocoding: the provider processed the address and has no match. Not retryable.                               |
| 404    | `address_too_coarse`  | Geocoding: resolved only to a ZIP/city/county centroid, or matched with low confidence. Ask the user for a fuller address — retrying will not help. |
| 422    | `address_form_unsupported` | Geocoding: a PO box, carrier route (RR/HC), military APO/FPO or general delivery. These are mail destinations with no parcel; ask for a street address. |
| 422    | `invalid_locator`     | Gave BOTH `lat`+`lng` and `address`, or neither. Send exactly one.                                           |
| 402    | `credits_exhausted`   | The account's monthly credits are spent. Body carries `plan`, `used`, `included`, `resets_at`, `upgrade_url`. Not retryable until the reset (or an upgrade) — stop the sweep and surface `upgrade_url` to your user. |
| 429    | (rate limit)          | Requests-per-minute limit for the plan exceeded (20 / 60 / 300 / 600 rpm). Retry after `Retry-After`.        |
| 429    | `geocode_busy`        | Geocoding overload gate. Retry after `Retry-After` (2 s).                                                    |
| 502    | `geocode_upstream_error` | The geocoding provider returned 5xx or dropped the connection. Retryable — retry after `Retry-After` (2 s). |
| 503    | `geocode_forbidden`   | The geocoding provider refused — usually a usage limit or a missing plan entitlement. **Not a bad key.** Retryable after `Retry-After` (1 h; the cap resets daily). |
| 503    | `geocode_unconfigured` | Mireye is missing its geocoding credential. An operator problem, not a bad request, and **not retryable** — report it. Mireye deliberately does not degrade to the free lower-precision tier here, which would look healthy while serving street-interpolated coordinates. |
| 504    | `geocode_timeout`     | Both the primary geocoder and the fallback exceeded their deadlines. Retryable after `Retry-After` (5 s).    |
| 422    | (validation)          | Request body failed schema validation (e.g., `lat`/`lng` wrong type, `question` empty).                      |
| 500    | `internal`            | Orchestrator crash. Response includes `request_id`; quote it when reporting.                                 |

Shape:

```json
{ "error": "fields_unknown", "message": "Unknown field names: ['flood_zone']", "fields_unknown": ["flood_zone"] }
```

Every retryable geocoding failure carries a `Retry-After` header; the non-retryable ones deliberately do not, so the header's presence is itself the signal.

An *imprecise* geocode is **not** an error: a street-interpolated coordinate comes back `200` labelled `range_interpolation`, and reading `accuracy_type` / `parcel_grade` is the caller's job. Only a centroid-grade or low-confidence match is refused.

Partial failures inside a `/v1/fetch` 200 response are *not* errors — they're a `partial_failures` array entry. Always check it. (`/v1/ask` reports gaps in its prose answer instead, not a `partial_failures` array.)

---

## MCP integration

If you're running inside an MCP-aware host (Claude Desktop, Claude Code, Cursor, custom agent), you can use the Mireye Earth MCP server instead of calling HTTP directly. It exposes seven native tools: `mireye_ask`, `mireye_fetch`, `mireye_geocode`, `mireye_lookup`, `mireye_proximity`, `mireye_request_field`, and `mireye_field_request_status` (prefixed so they don't collide with generic tools of the same name from other MCP servers). There are two ways to connect.

### Hosted remote endpoint (recommended for Claude Code)

Mireye runs a hosted MCP server at **`https://api.mireye.com/mcp`** over Streamable HTTP with native OAuth 2.1 + PKCE. This is the simplest path for Claude Code — no local install, browser sign-in:

```bash
claude mcp remove mireye-earth -s user   # only if an old stdio entry exists
claude mcp add --transport http --scope user mireye-earth https://api.mireye.com/mcp
```

Restart Claude Code, run `/mcp`, and complete the browser OAuth flow.

### Local stdio package (Claude Desktop, Cursor, custom agents)

The local adapter ships as its own slim PyPI package — **`mireye-mcp`** — with only `httpx` and the `mcp` SDK as dependencies. No GDAL, no native builds. `uvx` fetches it on demand:

```bash
uvx mireye-mcp
```

Authenticate once with the device flow (or set `MIREYE_BEARER_TOKEN` for non-interactive hosts):

```bash
mireye-mcp login      # prints a verification URL + code; approve in your account page
mireye-mcp status     # inspect stored credentials
mireye-mcp logout     # clear (add --revoke to also revoke server-side)
```

Add to your host's MCP config (e.g. `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, or `~/.cursor/mcp.json` for Cursor):

```json
{
  "mcpServers": {
    "mireye-earth": {
      "command": "uvx",
      "args": ["mireye-mcp"]
    }
  }
}
```

Restart the host. The `mireye_ask` and `mireye_fetch` tools appear under the plug menu. Point at a self-hosted deployment with `"env": { "MIREYE_BASE_URL": "https://your-deploy.example.com" }`. Stored credentials are bound to the `MIREYE_BASE_URL` they were created against.

### Tools, resources, and prompts

MCP keeps tools, resources, and prompts in three separate namespaces. To *do* something (fetch data, ask a question), call a **tool** via `tools/call`. The prompts below are starting templates a user invokes; they're not the call surface.

- **Tools** (the call surface — `tools/call`): `mireye_ask`, `mireye_fetch`, `mireye_geocode`, `mireye_lookup`, `mireye_proximity`, `mireye_request_field` (order a missing field), `mireye_field_request_status` (poll one). The batch and run surfaces are HTTP-only — there is no MCP tool for them.
- **Catalog resources** (read these instead of a `list_fields` tool): `mireye://catalog/fields`, `mireye://catalog/presets`, `mireye://catalog/us-envelope`, `mireye://field/{name}`, `mireye://preset/{name}`. Backed by `GET /v1/meta/fields` with a 1-hour ETag-aware cache.
- **Workflow prompts** (these are MCP *prompts*, fetched via `prompts/get` — not tools): `mireye_ask`, `mireye_fetch`, `mireye_site_report`, `mireye_flood_check`, `mireye_wildfire_underwrite`, `mireye_pick_fields`. The `mireye_ask` / `mireye_fetch` names appear in both lists — same name, different MCP primitive. Claude Code surfaces prompts as slash commands of the form `/mcp__mireye-earth__<prompt>`; the model still calls the underlying *tool* to actually run the request.

The server is also published to the [Official MCP Registry](https://registry.modelcontextprotocol.io) as **`com.mireye/earth`**, carrying both the PyPI distribution and the hosted remote — so registry-aware clients can discover and install it without manual config.

See [docs.mireye.ai/mcp/installation](https://docs.mireye.ai/mcp/installation) and [docs.mireye.ai/mcp/tools](https://docs.mireye.ai/mcp/tools) for full setup.

---

## Critical Gotchas

Read these once. They'll save you.

1. **US only.** Coordinates outside the envelope return `400`. Don't try to "approximate" by snapping to the nearest US point — tell the human Mireye doesn't cover that location.
2. **All data endpoints need a bearer token.** Only `GET /v1/meta/fields` is public. `/v1/ask`, `/v1/ask/stream`, `/v1/fetch`, `/v1/geocode`, `/v1/lookup`, and Sites require `Authorization: Bearer …`.
3. **`/v1/ask` cold start can be 60 s.** Warm is 2–6 s. If you're driving a UI, set a client timeout of **at least 120 s** (the server's own deadline is 110 s, so a shorter one aborts requests the server is still working on and will still bill) and surface a loading state — or use `/v1/ask/stream` to render tokens as they arrive.
4. **`/v1/fetch` partial failures live inside 200 responses.** Always read its `partial_failures` array — don't assume success just because the HTTP status is 200. (`/v1/ask` has no such array; it flags missing fields in the prose answer.)
5. **`status: "absent"` ≠ failure.** It means "the source has no value here." `value` is `null`, `confidence` is `unknown`. Don't retry. Show it to the human as "no data at this location." Truly failed fields are in `partial_failures`, not under `fields`.
6. **Confidence is lowercase and bucketed.** `high | medium | low | unknown`. For regulatory/audit work, gate on `high`. For screening, `medium` is usually fine. Flag `low` for human review.
7. **Per-field provenance is the product.** Never strip `source` / `source_url` / `dataset_vintage` / `fetched_at` when summarizing for a human. The citation chain is what separates Mireye from a hallucination.
8. **Cache the catalog, don't re-fetch.** `GET /v1/meta/fields` is sub-50 ms but ETag-cached for a reason — pull once at startup and reuse.
9. **`/v1/ask` picks fields nondeterministically.** Different runs of the same question can pick different fields. If you need determinism, capture `fields_used` from one run and replay via `/v1/fetch`.
10. **The `data_center_siting` preset is 90 fields, and that is fine.** The 50-field cap counts only fields you name explicitly; preset members are exempt. Request it on its own and add up to 50 more by name.

---

## Ideas — What You Can Do With Mireye

- **Data center siting.** The `data_center_siting` preset pulls power (substation distance, voltage, interconnection-queue headroom), electricity & gas prices, eGRID emissions, cooling (design wet-bulb, humidity, hot-day counts), water supply, fiber & 5G availability, and hazards/contamination in one call — the full first-pass screen for a hyperscale site.
- **Renewable energy siting.** `solar_siting` and `wind_siting` combine NREL resource data (GHI/DNI, PV yield, wind speed at hub height, capacity factor) with land constraints (slope, farmland, BLM status, protected areas, eagle-nest density) and the least-cost interconnect distance. `storage_siting` and `grid_interconnect` cover battery and transmission screens.
- **Property insurance underwriting.** Pull `flood_risk`, `wildfire_underwrite`, or `natural_hazard` for a coordinate, gate on `high` confidence, store the citation chain as part of the underwriting record. See [docs.mireye.ai/use-cases/insurance](https://docs.mireye.ai/use-cases/insurance).
- **Mortgage & title due diligence.** `flood_risk` + `boundaries` + `intersects_conservation_easement` + `easement_holder` for floodplain status, jurisdiction, and recorded easements with source citations. See [docs.mireye.ai/use-cases/lending](https://docs.mireye.ai/use-cases/lending).
- **Agent reasoning grounded in source data.** Wire Mireye into an agent that has to make claims about physical locations. Cited, reproducible, auditable. See [docs.mireye.ai/use-cases/agents](https://docs.mireye.ai/use-cases/agents).
- **Address-list screening — the national-screen recipe.** Given ANY list of US street addresses (a supplier list, an insurance book, fleet depots, school districts, a portfolio): loop `POST /v1/fetch` with `address` plus the fields that define fragility for that domain, collect each field's `value` (and the `partial_failures` array), percentile-rank the results, and return the tail with its citation chain intact. This is how [mireye's research series Issue 01](https://www.mireye.com/blog/cold-chain-fragility-us-meat-plants) screened all 7,185 federally-inspected US meat, poultry and egg plants in one afternoon: a sustained 190 addresses per minute, 14,400 API calls, zero server errors, about $4 of marginal data cost. The full pipeline (~200 lines) is at [github.com/Mireye-Labs/cold-chain-fragility](https://github.com/Mireye-Labs/cold-chain-fragility) — clone it and point it at your CSV. Keep client concurrency modest (≤12) and read every `partial_failures` array (Gotcha 4).
- **Re-verification pipelines.** Ask `/v1/ask` once, capture `fields_used`, re-run `/v1/fetch` on those exact field names months later, diff. Detect changes (e.g., a parcel newly added to a floodplain) without writing dataset-specific code.

---

## Learn More

- **Quickstart:** [docs.mireye.ai/quickstart](https://docs.mireye.ai/quickstart)
- **Introduction:** [docs.mireye.ai/introduction](https://docs.mireye.ai/introduction)
- **Authentication:** [docs.mireye.ai/authentication](https://docs.mireye.ai/authentication)
- **Full API reference:** [/v1/ask](https://docs.mireye.ai/api-reference/ask), [/v1/fetch](https://docs.mireye.ai/api-reference/fetch), [/v1/fetch/batch](https://docs.mireye.ai/api-reference/fetch-batch), [/v1/runs](https://docs.mireye.ai/api-reference/runs), [/v1/field-requests](https://docs.mireye.ai/api-reference/field-requests) ([status](https://docs.mireye.ai/api-reference/field-requests-status)), [/v1/meta/fields](https://docs.mireye.ai/api-reference/meta-fields)
- **Field catalog:** [docs.mireye.ai/api-reference/field-catalog](https://docs.mireye.ai/api-reference/field-catalog)
- **Errors:** [docs.mireye.ai/api-reference/errors](https://docs.mireye.ai/api-reference/errors)
- **Pricing and credits:** [mireye.com/pricing](https://www.mireye.com/pricing) · machine-readable: [api.mireye.com/v1/meta/plans](https://api.mireye.com/v1/meta/plans)
- **MCP setup:** [docs.mireye.ai/mcp/installation](https://docs.mireye.ai/mcp/installation), [docs.mireye.ai/mcp/tools](https://docs.mireye.ai/mcp/tools), [docs.mireye.ai/mcp/troubleshooting](https://docs.mireye.ai/mcp/troubleshooting)
- **Use cases:** [building agents](https://docs.mireye.ai/use-cases/agents), [insurance](https://docs.mireye.ai/use-cases/insurance), [lending](https://docs.mireye.ai/use-cases/lending)
- **Full docs index for LLMs:** [docs.mireye.ai/llms.txt](https://docs.mireye.ai/llms.txt)
- **OpenAPI spec:** [api.mireye.com/v1/openapi.json](https://api.mireye.com/v1/openapi.json)
- **MCP source:** [github.com/Mireye-Labs/mireye-earth-mcp](https://github.com/Mireye-Labs/mireye-earth-mcp) — the live source mirror, snapshot-synced from the monorepo on every release (currently v0.3.0). Same name as, but not to be confused with, the abandoned `mireye-earth-mcp` PyPI package; the package you install is `mireye-mcp`.
