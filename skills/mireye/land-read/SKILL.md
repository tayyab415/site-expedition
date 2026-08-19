---
name: land-read
description: Terrain and land-cover facts for one address, every value cited to its federal source.
---

# Land Read

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

1. Send an address (or lat/lng) to POST /v1/fetch with preset: "terrain" plus fields: ["lcms_class", "land_use_class"] pulled in from the land_cover preset — one request, capped at 50 explicitly-named fields (preset members are exempt from that cap).
2. Mireye returns elevation, slope, aspect, soil drainage, and land-cover class for that point, each with its own source, source_url, and confidence.
3. When you send an address, the response carries a geocode block — check parcel_grade before trusting anything parcel-specific: false means the coordinate was estimated from the street and can be ~2.9 km out in rural areas.
4. For a list of addresses (a portfolio, a lead list), call this once per row — loop over the list.

## Example request

```bash
curl -s https://api.mireye.com/v1/fetch \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{
    "address": "1600 Smith St, Houston, TX 77002",
    "preset": "terrain",
    "fields": ["lcms_class", "land_use_class"]
  }' | jq
```

## Example response

```json
{
  "lat": 29.7604,
  "lng": -95.3698,
  "fetched_at": "2026-07-30T14:02:11.318204+00:00",
  "fields": {
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
    "slope_degrees": {
      "value": 0.6,
      "unit": "degrees",
      "source": "USGS_3DEP_COG",
      "source_url": "https://www.usgs.gov/3dep",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "aspect_cardinal": {
      "value": "SE",
      "unit": null,
      "source": "USGS_3DEP_COG",
      "source_url": "https://www.usgs.gov/3dep",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "soil_drainage_class": {
      "value": "Somewhat poorly drained",
      "unit": null,
      "source": "USDA_SSURGO",
      "source_url": "https://sdmdataaccess.sc.egov.usda.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "lcms_class": {
      "value": "Barren or Impervious",
      "unit": null,
      "source": "USFS_LCMS",
      "source_url": "https://data.fs.usda.gov/geodata/rastergateway/LCMS/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "land_use_class": {
      "value": "Developed",
      "unit": null,
      "source": "USFS_LCMS",
      "source_url": "https://data.fs.usda.gov/geodata/rastergateway/LCMS/",
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
