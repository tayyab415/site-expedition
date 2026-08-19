---
name: insurance-book-monitoring
description: Re-screen your entire book of insured properties for flood and wildfire exposure in one batch, cited to FEMA/USFS/Copernicus sources.
---

# Insurance Book Monitoring

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

1. Take the policy address list and call POST /v1/fetch once per address with preset: "flood_risk" (plus a couple of wildfire-relevant fields pulled from wildfire_underwrite), run in parallel.
2. Every value comes back cited — FEMA flood zone, coastal distance, wildfire-relevant vegetation signal — so this can be re-run on every renewal instead of trusting a stale one-time inspection.
3. When you send an address, the response carries a geocode block — check parcel_grade before trusting anything parcel-specific: false means the coordinate was estimated from the street and can be ~2.9 km out in rural areas.
4. Filter the batch for anything that now crosses a risk threshold (e.g. within_floodplain_polygon flipped to true) and route it to a manual underwriting review.

## Example request

```bash
# One request per policy address, in parallel — script this over your
# book export (note account QPS limits and add retry logic at scale).
curl -s https://api.mireye.com/v1/fetch \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{
    "address": "1600 Smith St, Houston, TX 77002",
    "preset": "flood_risk",
    "fields": ["tree_canopy_pct", "ndvi_current"]
  }' | jq
```

## Example response

```json
{
  "lat": 29.139571,
  "lng": -83.031508,
  "fetched_at": "2026-07-30T14:02:11.318204+00:00",
  "fields": {
    "within_floodplain_polygon": {
      "value": true,
      "unit": null,
      "source": "FEMA_NFHL",
      "source_url": "https://hazards.fema.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": "FEMA NFHL Flood Hazard Zones indicate Special Flood Hazard Area: Zone AE.",
      "status": "ok"
    },
    "coast_distance_m": {
      "value": 88.4,
      "unit": "meters",
      "source": "NOAA_CUSP",
      "source_url": "https://shoreline.noaa.gov/data/datasheets/cusp.html",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "tree_canopy_pct": {
      "value": 41.6,
      "unit": "percent",
      "source": "USFS_NLCD_TCC",
      "source_url": "https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    }
  },
  "partial_failures": [],
  "geocode": {
    "accuracy": 1,
    "accuracy_type": "rooftop",
    "normalized_address": "9 Elm St, Cedar Key, FL 32625",
    "provider": "geocodio",
    "parcel_grade": true,
    "precision_note": null
  },
  "resolved_location": {
    "lat": 29.139571,
    "lng": -83.031508,
    "source": "address"
  }
}
```
