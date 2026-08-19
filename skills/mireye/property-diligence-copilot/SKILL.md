---
name: property-diligence-copilot
description: A full canonical dossier for one address — jurisdiction, hazard flags, and parcel record in a single call.
---

# Property Diligence Copilot

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

1. Send an address, coordinate, or APN to POST /v1/lookup.
2. Get back canonical coordinates, county/tract/CBSA/congressional district, FEMA flood zone + elevation, opportunity-zone status, and — when the geocode clears parcel-quality accuracy — a full parcel record: owner, zoning, land use, assessed value, sale history.
3. Check disposition before trusting the result: "resolved" is a clean match, "clarify" means multiple plausible matches were found (surface candidates to a human, never silently pick one), "no_match" is an honest failure with a reason — note some low-confidence matches arrive as an HTTP error status rather than a 200 body; treat both the same, but treat any other error status as a real failure.

## Example request

```bash
curl -s https://api.mireye.com/v1/lookup \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"input": "480 Berdoll Ln, Cedar Creek TX"}' | jq
```

## Example response

```json
{
  "disposition": "resolved",
  "lat": 30.199699,
  "lng": -97.496411,
  "resolved_address": "480 BERDOLL LN, CEDAR CREEK, TX 78612",
  "county": "Bastrop County",
  "cbsa_name": "Austin-Round Rock-San Marcos, TX Metro Area",
  "elevation_m": 152.3,
  "fema_flood_zone": "X",
  "within_floodplain": false,
  "county_market": {
    "population": 106822,
    "population_growth_1yr_pct": 4.1,
    "hpi_yoy_pct": 3.8,
    "employment_yoy_pct": 2.9,
    "median_household_income_usd": 78500
  },
  "in_opportunity_zone": false,
  "parcel": {
    "parcel_id": "R123456",
    "owner": "PECAN GROVE FARMS #1 LLC",
    "zoning": "AG",
    "land_use": "Agricultural",
    "assessed_value_usd": 185000,
    "last_sale_date": "2019-03-14",
    "last_sale_price_usd": 210000,
    "source": "REGRID"
  },
  "confidence": 0.95
}
```
