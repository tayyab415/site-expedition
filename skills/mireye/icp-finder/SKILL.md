---
name: icp-finder
description: Screen a list of candidate addresses against your ideal-customer profile — bring your own list, Mireye does the enrichment and filtering.
---

# ICP Finder

## Before you start

Every request below authenticates with a Mireye API token as a bearer header.
Get one at [mireye.com/account](https://www.mireye.com/account), then set it
as an environment variable before running any example:

```bash
export MIREYE_API_TOKEN="your-token-here"
```

## Implementation guidance

- If `$MIREYE_API_TOKEN` isn't set, ask the user for their Mireye API key before making any request — they can create one at [mireye.com/account](https://www.mireye.com/account). Don't fabricate or guess a token.
- Every value in the response carries its own `source`, `source_url`, and `confidence` — when relaying a result to the user, keep at least the source name so the citation trail isn't lost.
- Treat any response status other than the cases documented above as a real failure — surface it to the user (or retry with backoff if it looks transient), never silently treat it as "no data" or a non-match.
- This skill runs one request per row in a list — mind your account's QPS limits and add retry/backoff logic before scaling to a large list.

1. Mireye has no region-search endpoint (no "find sites in the Bay Area") — start from a list of candidate addresses you already have: a parcel export, a lead list, a public assessor dataset.
2. For each candidate, call POST /v1/lookup to resolve it to a coordinate + parcel, and check disposition — "resolved" continues, "clarify"/"no_match" should go to a manual review queue, not be silently dropped.
3. Some low-confidence matches come back as an HTTP error (e.g. 404 address_too_coarse) instead of a 200 body — treat both as the same non-match outcome, but treat any OTHER error status as a real failure worth surfacing, not a screened-out candidate.
4. Call POST /v1/fetch with preset: "site_selection" on the resolved coordinate, and filter the results against your own ICP predicate (acreage, zoning, flood tolerance, grid distance — whatever "good" means for you).

## Example request

```bash
# Step 1 — resolve a candidate address to a coordinate + parcel
curl -s https://api.mireye.com/v1/lookup \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"input": "480 Berdoll Ln, Cedar Creek, TX"}' | jq

# Step 2 — screen that coordinate against your ICP fields
curl -s https://api.mireye.com/v1/fetch \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"lat": 30.199699, "lng": -97.496411, "preset": "site_selection"}' | jq

# Repeat per candidate address, then filter against your own ICP predicate
# (acreage, zoning, flood tolerance, grid distance, ...).
```

## Example response

```json
{
  "disposition": "resolved",
  "lat": 30.199699,
  "lng": -97.496411,
  "resolved_address": "480 BERDOLL LN, CEDAR CREEK, TX 78612",
  "within_floodplain": false,
  "parcel": {
    "parcel_id": "R123456",
    "area_m2": 20234.5,
    "zoning": "AG",
    "assessed_value_usd": 185000,
    "source": "REGRID"
  },
  "confidence": 0.95
}
```
