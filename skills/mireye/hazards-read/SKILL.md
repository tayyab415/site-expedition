---
name: hazards-read
description: Flood, wetland, and wildfire exposure for one address, cited to FEMA/NOAA/USFWS/Copernicus sources.
---

# Hazards Read

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

1. Send an address (or lat/lng) to POST /v1/fetch with preset: "flood_risk" plus fields: ["tree_canopy_pct", "ndvi_current"] pulled in from the wildfire_underwrite preset.
2. Get back FEMA flood zone status, coastal distance, wetland intersection, and wildfire-relevant vegetation signals in one call.
3. When you send an address, the response carries a geocode block — check parcel_grade before trusting anything parcel-specific: false means the coordinate was estimated from the street and can be ~2.9 km out in rural areas.
4. Use this to pre-screen a book of properties before a manual underwriting review, flagging anything that needs a closer look.

## Example request

```bash
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
  "lat": 29.7604,
  "lng": -95.3698,
  "fetched_at": "2026-07-30T14:02:11.318204+00:00",
  "fields": {
    "within_floodplain_polygon": {
      "value": false,
      "unit": null,
      "source": "FEMA_NFHL",
      "source_url": "https://hazards.fema.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": "FEMA NFHL Flood Hazard Zones intersect, but not an SFHA: Zone X.",
      "status": "ok"
    },
    "coast_distance_m": {
      "value": 2014.1,
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
    "intersects_wetland": {
      "value": false,
      "unit": null,
      "source": "USFWS_NWI",
      "source_url": "https://fwspublicservices.wim.usgs.gov",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "elevation": {
      "value": 14.38,
      "unit": "meters",
      "source": "USGS_3DEP_COG",
      "source_url": "https://www.usgs.gov/3dep",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "tree_canopy_pct": {
      "value": 8.2,
      "unit": "percent",
      "source": "USFS_NLCD_TCC",
      "source_url": "https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "ndvi_current": {
      "value": 0.31,
      "unit": null,
      "source": "COPERNICUS_S2_SR_HARMONIZED",
      "source_url": "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED",
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
    "normalized_address": "1600 Smith St, Houston, TX 77002",
    "provider": "geocodio",
    "parcel_grade": true,
    "precision_note": null
  },
  "resolved_location": {
    "lat": 29.7604,
    "lng": -95.3698,
    "source": "address"
  }
}
```
