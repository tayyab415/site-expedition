---
name: crm-address-cleanup
description: Turn a messy list of CRM or lead addresses into clean, canonical records — with an explicit review queue for anything ambiguous.
---

# CRM Address Cleanup

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

1. Take the raw address list (a CRM export, a lead form dump, a spreadsheet) and call POST /v1/lookup once per row, in parallel.
2. Split results by disposition: "resolved" rows get a clean canonical record (coordinate + jurisdiction); "clarify" rows carry multiple candidates for a human to pick between; "no_match" rows need manual research — including some that arrive as an HTTP error status rather than a 200 body, treated the same way, but any OTHER error status is a real failure, not a non-match.
3. Write the clean list and the review-queue list back to the CRM as two separate buckets instead of one merged list of uncertain quality — never silently guess on an ambiguous row.

## Example request

```bash
# Run once per row from your CRM export, in parallel (note account QPS
# limits and add retry logic when scripting this over a large list).
curl -s https://api.mireye.com/v1/lookup \
  -H "Authorization: Bearer $MIREYE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"input": "480 Berdoll Ln, Cedar Creek TX"}' | jq '.disposition, .resolved_address'

# A geocode-quality failure can arrive as a 404 address_too_coarse instead of
# a 200 body with disposition: "no_match" — treat both the same way. Any
# other error status (401/403 auth, 429 rate limit, 5xx) is a real failure,
# not a non-match, and must not be swallowed as one.
```

## Example response

```json
{
  "clean": [
    {
      "disposition": "resolved",
      "resolved_address": "480 BERDOLL LN, CEDAR CREEK, TX 78612",
      "lat": 30.199699,
      "lng": -97.496411,
      "confidence": 0.95
    }
  ],
  "review_queue": [
    {
      "disposition": "no_match",
      "input": "1100 King St W, Toronto",
      "reason": "address_too_coarse",
      "hint": "resolved only to place, which is not specific enough to identify a property."
    },
    {
      "disposition": "no_match",
      "input": "not a real address",
      "reason": "unaddressed_or_no_match",
      "hint": "No plausible match for this input. Check spelling, or supply an exact coordinate."
    }
  ]
}
```
