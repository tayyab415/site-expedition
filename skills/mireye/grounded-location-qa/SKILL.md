---
name: grounded-location-qa
description: Give any support or research bot a tool that answers plain-English questions about a location — with citations, not hallucination.
---

# Grounded Location Q&A

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

1. Wire POST /v1/ask as a tool call: it takes a location (lat/lng or an address, never both) and a natural-language question.
2. Mireye's planner picks the right catalog fields, fetches them, and a synthesizer model writes a cited prose answer, plus a confidence level and a citations list grouped by source.
3. For a chat UI, swap in POST /v1/ask/stream (SSE) to stream the answer token-by-token instead of waiting for the full response — same fields, delivered incrementally.

## Example request

```bash
curl -s https://api.mireye.com/v1/ask \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"lat": 46.6, "lng": -93.7, "question": "What is the wildfire risk at this location and what fuel is on the ground?"}' | jq
```

## Example response

```json
{
  "lat": 46.6,
  "lng": -93.7,
  "question": "What is the wildfire risk at this location and what fuel is on the ground?",
  "answer": "Wildfire risk at this location (46.6, -93.7) is LOW. The land cover is classified as Grass/Forb/Herb with 0.0% tree canopy cover, meaning there is no forested fuel structure present. The terrain is essentially flat at 0.05 degrees slope, which provides no topographic amplification of fire spread.",
  "confidence": "medium",
  "citations": [
    {
      "source": "USFS_LCMS",
      "source_url": "https://data.fs.usda.gov/geodata/rastergateway/LCMS/",
      "fields": [
        "lcms_class"
      ],
      "confidence": "high"
    },
    {
      "source": "USGS_3DEP_COG",
      "source_url": "https://www.usgs.gov/3dep",
      "fields": [
        "elevation"
      ],
      "confidence": "high"
    }
  ],
  "fields_used": [
    "elevation",
    "lcms_class",
    "ndvi_change_5y",
    "ndvi_current",
    "slope_degrees",
    "tree_canopy_pct"
  ],
  "resolved_location": {
    "lat": 46.6,
    "lng": -93.7,
    "source": "coordinate"
  }
}
```
