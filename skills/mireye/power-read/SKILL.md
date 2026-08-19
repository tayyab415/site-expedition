---
name: power-read
description: Grid and utility infrastructure facts for one address — nearest transmission line and its voltage, nearest power plant, gas pipeline distance, sewer service area.
---

# Power Read

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

1. Send an address (or lat/lng) to POST /v1/fetch with preset: "utilities".
2. Get back the nearest power plant, nearest transmission line + its voltage class, gas pipeline distance, and sewer service area — the same data our internal power-tiering pipeline uses, packaged as a single call.
3. When you send an address, the response carries a geocode block — check parcel_grade before trusting anything parcel-specific: false means the coordinate was estimated from the street and can be ~2.9 km out in rural areas.
4. Loop this over a candidate list to rank sites by grid proximity before anyone opens a map.

## Example request

```bash
curl -s https://api.mireye.com/v1/fetch \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{
    "address": "1600 Smith St, Houston, TX 77002",
    "preset": "utilities"
  }' | jq
```

## Example response

```json
{
  "lat": 29.7604,
  "lng": -95.3698,
  "fetched_at": "2026-07-30T14:02:11.318204+00:00",
  "fields": {
    "nearest_power_plant_name": {
      "value": "Deepwater Generating Station",
      "unit": null,
      "source": "EIA_POWER",
      "source_url": "https://atlas.eia.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "nearest_power_plant_distance_m": {
      "value": 4820.3,
      "unit": "meters",
      "source": "EIA_POWER",
      "source_url": "https://atlas.eia.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "nearest_transmission_line_distance_m": {
      "value": 612.4,
      "unit": "meters",
      "source": "EIA_POWER",
      "source_url": "https://atlas.eia.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "nearest_transmission_line_voltage_kv": {
      "value": 138,
      "unit": "kilovolts",
      "source": "EIA_POWER",
      "source_url": "https://atlas.eia.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": null,
      "status": "ok"
    },
    "max_transmission_line_voltage_kv_within_radius": {
      "value": 345,
      "unit": "kilovolts",
      "source": "EIA_POWER",
      "source_url": "https://atlas.eia.gov/",
      "confidence": "high",
      "fetched_at": "2026-07-30T14:02:11.000Z",
      "dataset_vintage": null,
      "ttl_seconds": 31536000,
      "notes": "Highest numeric voltage within ~2km.",
      "status": "ok"
    },
    "nearest_gas_pipeline_distance_m": {
      "value": 1830.9,
      "unit": "meters",
      "source": "EIA_PIPELINES",
      "source_url": "https://atlas.eia.gov/",
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
