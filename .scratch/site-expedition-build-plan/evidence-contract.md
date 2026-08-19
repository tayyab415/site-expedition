# Canonical evidence contract

**Status:** Frozen by [Define the canonical evidence contract](./issues/05-define-the-canonical-evidence-contract.md)  
**Frozen at:** 2026-08-15  
**Authorities:** [`grilling_session.markdown`](../../grilling_session.markdown) §§4, 8; [`mvp-contract.md`](./mvp-contract.md) §5; [`FULL_FEASIBILITY_DIAGNOSIS.md`](../../FULL_FEASIBILITY_DIAGNOSIS.md) §§4–5, 9, 12  
**Domain language:** [`CONTEXT.md`](../../CONTEXT.md)

This is the runtime evidence law. It does not reopen product vision. Verdict algebra, Skeptic Review procedure, and Mission manifests remain later tickets. They must consume this contract; they may not invent a second record shape.

The current harness `record()` is non-compliant: it keys cache by display slug and drops `status`, TTL, notes, and `partial_failures`. New adapters must emit Evidence Atoms. The harness may be read as a fixture source, not as the schema.

---

## 1. Atomic unit

Every adapter emits zero or more **Evidence Atoms**. There is one atom schema for Mireye, Earth Engine, official connectors, inventory, Routes, model output, and Google scene context.

Two derived objects point at atoms. They are not a parallel schema:

- **Contradiction** — two or more atoms that answer the same decision question and disagree after geometry, time, and Source Family have been inspected.
- **Verification Gap** — a required question that lacks an authoritative atom, or whose only atoms are `FAILED`, `UNKNOWN`, `PROXY` without authority, or `PRESENTATION`.

Adapters never invent vendor-specific record types for the decision graph.

---

## 2. Evidence Atom

Required fields. `null` is allowed only where listed.

| Field | Type | Rule |
|---|---|---|
| `atom_id` | string | Stable within an Expedition. Not a cache key. |
| `candidate_id` | string | The Candidate Site this atom is about. |
| `question_id` | string | The Workstream / Mission Plan question this atom answers. |
| `field_id` | string | Catalog or recipe name (`fema_flood_zone`, `jrc_monthly_water_freq`, `aerial_video_id`). |
| `kind` | enum | Exactly one of §3. |
| `status` | enum | Exactly one of §4. Feasibility labels never appear here. |
| `decision_effect` | enum | Exactly one of §5. |
| `value` | any \| null | Present for `FACT`, `PROXY`, `MODEL` when the source returned a value. Null for `ABSENT`, `FAILED`, `UNKNOWN`, `PRESENTATION` unless a handle is needed (`videoId`). |
| `unit` | string \| null | SI or source unit. Null when not applicable. |
| `source` | string | Named provider or dataset, not a vendor slogan. |
| `source_url` | string \| null | Citation URL when the source publishes one. |
| `source_family` | string | §6. Shared underlying dataset, not the API that wrapped it. |
| `independence_group` | string | §6. Same group cannot corroborate. |
| `authority` | enum | `authoritative` \| `proxy` \| `model` \| `presentation` \| `none`. |
| `support` | object | §7 Spatial Support. |
| `observed_at` | string \| null | When the source says the world was in this state. ISO-8601. |
| `fetched_at` | string | When this process retrieved the atom. ISO-8601. |
| `dataset_vintage` | string \| null | Publication / edition / map revision. |
| `ttl` | string \| null | Duration or absolute expiry from the source or recipe. |
| `confidence` | number \| string \| null | Pass through source confidence. Never invent a composite score. |
| `notes` | string \| null | Source notes. Must be preserved. |
| `failure` | object \| null | Required when `kind` is `FAILED` or `status` is `failed` / `blocked`. See §4. |
| `cost` | object | `{ "credits": number, "tokens": number, "unit": string }` — observed cost of producing this atom. Zero for replay. |
| `citation` | object | `{ "source", "source_url", "fetched_at", "dataset_vintage" }` — the public-facing subset. |
| `transform_version` | string | Recipe / normalization / computation version that produced `value` from raw. |
| `cache_identity` | string | §8. Geometry- and version-aware. Never a display slug. |
| `live_label` | enum | `live` \| `replay`. Must match `status` (`live` only when `status` is `live`). |

Optional: `partial_failures` (array of typed failures that did not kill the whole response), `recipe_id`, `license` (required when redistribution is restricted).

---

## 3. Kind

Exactly one per atom.

| Kind | Meaning | May become a pass? |
|---|---|---|
| `FACT` | Cited observation from an authorized present-state or historical source. | Yes, if `authority` is `authoritative` and `status` is `live` or unexpired `replay`. |
| `ABSENT` | The source defines this as semantic absence (not a transport miss). | No. Absence is not a pass. |
| `FAILED` | Typed transport, auth, quota, timeout, or no-coverage failure. | No. Required-gate failure → Conditional. |
| `PROXY` | Nearby infrastructure, area membership, counts, labels. | No for capacity, ingress, zoning, Market Availability, water right, or permission. May `INFORM` or `GATE` only as a lead. |
| `MODEL` | DEM, climate path, classifier, land-cover fraction, constrained reviewer label. | No as sole corroboration of a `FACT` in the same Independence Group. Disagreement creates a Verification Gap, not a chosen “better” model. |
| `PRESENTATION` | Aerial View, Maps 3D, camera path. | Never. `decision_effect` is always `NONE`. |
| `UNKNOWN` | The question ran or was skipped and remains unanswerable. | No. |

There is no `SCORE` kind and no `PASS` kind.

---

## 4. Runtime status

Feasibility words (`DOCUMENTED`, `TESTED_OK`, `INFEASIBLE`, …) stay in planning documents. Runtime `status` is only:

| Status | Meaning |
|---|---|
| `live` | Retrieved in this Expedition from the live provider. |
| `replay` | Source-valid cache, still inside TTL / recipe freshness, visibly timestamped. |
| `stale` | Cached past TTL or past the source’s own freshness rule. Display the clocks. Do not treat as live. Refresh if the budget allows; otherwise downgrade authority. |
| `blocked` | Credential, key restriction, or policy stop (`403`, Routes key, credit ceiling). No substitute metric may be relabeled as equivalent. |
| `partial` | Some requested fields arrived; others failed. Keep successful atoms. Attach `partial_failures`. |
| `failed` | The request failed after bounded retry. |
| `absent` | Semantic absence as defined by the source. |

A cache hit is never `live`. `replay` and `stale` are both cached; they differ by freshness.

`failure` object when applicable:

```text
{ "class": "auth" | "quota" | "timeout" | "no_coverage" | "unsupported" | "ambiguous" | "other",
  "http_status": number | null,
  "retryable": boolean,
  "message_public": string }   // no secrets, no raw provider dumps
```

---

## 5. Decision effect

Locked on the atom so verdict code cannot reinterpret a field.

| Effect | May do | Must not do |
|---|---|---|
| `VETO` | Justify Reject when the atom is a reliable `FACT` that contradicts a user-declared mandatory condition. | Fire on `PROXY`, `MODEL` disagreement alone, `PRESENTATION`, `FAILED`, or `UNKNOWN`. |
| `GATE` | Block Strong Fit. If unmet, failed, stale, or unknown → Conditional. | Silently pass. |
| `INFORM` | Rank preferences after required gates are supported. | Rescue a failed gate. |
| `UNKNOWN` | Record a hole. | Count toward Evidence Coverage as support. |
| `NONE` | Display, narrate, or cite as context. | Enter Mission fit or Evidence Coverage as support. |

Rules:

- `PRESENTATION` → `NONE`.
- `FAILED` on a required gate → treat the condition as `UNKNOWN` / Conditional.
- `PROXY` may be `GATE` or `INFORM`, never `VETO` for capacity, truck ingress, zoning, Market Availability, water right, or legal permission.
- `MODEL` disagreement → Verification Gap, not `VETO` by picking the favorable model.
- Same Independence Group cannot supply a second `VETO` or corroborating `GATE` for the same question.

---

## 6. Source Family and Independence Group

`source_family` names the underlying dataset. `independence_group` is the corroboration key. Two atoms in the same group cannot corroborate each other.

Committed groups for the hero path:

| Family | Typical producers | Independence group | Notes |
|---|---|---|---|
| `JRC_GSW` | Mireye water permanence; EE `JRC/GSW1_4/MonthlyHistory` | `JRC_GSW` | Temporal transform adds information, not a second family. |
| `USGS_3DEP` | Mireye `elevation`; EE USGS 3DEP | `USGS_3DEP` | Same family through two APIs. |
| `FEMA_NFHL` | Mireye flood zone / floodplain; direct FEMA NFHL | `FEMA_NFHL` | Direct FEMA adds edition detail, not a new family. |
| `USFWS_NWI` | Mireye wetland; NWI | `USFWS_NWI` | Non-regulatory. |
| `USDA_CDL` | Mireye crop; EE CDL | `USDA_CDL` | |
| `GOOGLE_VISUAL` | Aerial View, Photorealistic 3D Tiles, Maps | `GOOGLE_VISUAL` | Presentation only. |
| `GOOGLE_ROUTES` | Routes Matrix | `GOOGLE_ROUTES` | Currently `blocked` until a later ticket closes it. |
| `MIREYE_INFRA` | Road/rail/substation/fiber/water-area proxies | `MIREYE_INFRA` | Proxy family. Not capacity. |
| `EPA_ECHO` | Mireye hazardous proximity; ECHO/FRS | `EPA` until a distinct facility record is attached | Drilldown may refine, not duplicate, the same facility. |
| `DEM_OTHER` | NASADEM or a separately cleared second DEM | its own group | Never default FABDEM. FABDEM is not in the production family set. |

A later official connector joins an existing family if it reprints the same dataset. It gets a new group only when the source, geometry, and time are independently collected.

Skeptic Review reads `independence_group`, not the vendor name.

---

## 7. Spatial Support

```text
{
  "kind": "point" | "buffer" | "parcel" | "building" | "watershed" | "region" | "network",
  "crs": "EPSG:4326" | "local_projected",
  "lat": number | null,
  "lng": number | null,
  "radius_m": number | null,
  "radius_purpose": string | null,
  "parcel_id": string | null,
  "parcel_grade": boolean | null,
  "match_type": string | null,
  "match_distance_m": number | null,
  "boundary_source": string | null,
  "boundary_version": string | null,
  "huc": string | null,
  "geometry_hash": string | null
}
```

Rules:

- WGS84 for stored points. Projected meters only inside a Concept Test.
- A buffer must name `radius_m` and `radius_purpose`. A 60 m water buffer is not a parcel fraction.
- Parcel claims require `parcel_grade` true and a match method. Parcel failure may degrade a good geocode without invalidating the point; it opens a parcel Verification Gap.
- `local_projected` is allowed only for Concept Test geometry that never came from Google tiles.
- Wrong support is a defect. Skeptic Review must flag buffer-labeled-as-parcel.

---

## 8. Cache identity

`cache_identity` is the hash of, in order:

1. provider
2. dataset or API version
3. field / recipe / `transform_version`
4. `geometry_hash` or parcel id (not a display slug, not geohash alone)
5. Spatial Support kind + radius + purpose
6. date window
7. scale
8. mask / cloud / orbit / polarization settings when used
9. `question_id` when the same field is computed under different questions

Replay may reuse an atom only when this identity matches and `status` is set to `replay` or `stale`. Observed time and fetch time are stored separately. Cached evidence is never labeled `live`.

---

## 9. Contradiction

```text
{
  "contradiction_id": string,
  "candidate_id": string,
  "question_id": string,
  "atom_ids": [string, string, ...],
  "same_independence_group": boolean,
  "geometry_aligned": boolean,
  "time_aligned": boolean,
  "resolution": "keep_both" | "verification_gap",
  "notes": string
}
```

Rules:

- Keep both atoms. Do not drop the less favorable value.
- If `same_independence_group` is true, this is not corroboration and not a second witness.
- If geometry or time is not aligned, do not call it a site-level contradiction; call it a support mismatch.
- Usual `resolution` is `verification_gap`. Never resolve by selecting the model that helps the Candidate Site.
- A Contradiction of two `FACT`s in *different* groups on a user-declared mandatory condition may feed Reject only through verdict rules in a later ticket — this contract only forbids silent resolution.

---

## 10. Verification Gap

```text
{
  "gap_id": string,
  "candidate_id": string,
  "question_id": string,
  "missing_authority": string,
  "blocking": boolean,
  "atom_ids": [string],
  "action": string
}
```

`blocking` true means Strong Fit is impossible until the named authority supplies a fact. Hero defaults that stay gaps unless a later ticket closes them: route time, Market Availability, electrical capacity, water right, zoning/permission, truck ingress.

`action` is the sentence that belongs on the acquisition/verification brief (who to call, what artifact to obtain). It is not a pass.

---

## 11. Google presentation

Aerial View and Maps 3D emit `PRESENTATION` atoms only.

- Retain `videoId` when lookup is ACTIVE. Never persist signed playback URLs or video bytes.
- 404 / no coverage → `FAILED` with `class: "no_coverage"` and immediate 3D fallback atom. Not an Expedition failure.
- `decision_effect`: `NONE`. `authority`: `presentation`. `independence_group`: `GOOGLE_VISUAL`.
- Pixels, meshes, and camera paths never enter Concept Test geometry, Evidence Coverage, or Mission fit.
- Reports may link to a live scene. They must not redistribute tiles or screenshots as evidence.

---

## 12. Cost, citation, confidence

- `cost` is observed, not estimated. Quote-before-fetch belongs to the budget ticket; the atom records what was actually spent.
- `citation` is the only subset a UI or brief may show as provenance. It must include source, URL when present, `fetched_at`, and `dataset_vintage`.
- `confidence` is pass-through. It must not be averaged into a site score.
- Evidence Coverage counts questions with a usable `FACT` or an honest `ABSENT`, divided by decision-relevant questions. `FAILED`, `UNKNOWN`, `stale` without refresh, `PROXY` without authority, and `PRESENTATION` do not count as coverage.

---

## 13. Invariants (must be testable)

1. Unknown, absent, failed, stale, contradictory, or low-authority atoms never become a pass.
2. A required-source `FAILED` or `blocked` atom makes that gate Conditional, never Strong Fit.
3. Same `independence_group` cannot corroborate.
4. `PRESENTATION` never has a non-`NONE` effect.
5. Cache identity never uses a display slug alone.
6. A replay atom is never `status: live`.
7. Buffer metrics are never named parcel metrics.
8. FABDEM is not a default `source_family`.
9. Partial provider responses preserve successful atoms and `partial_failures`.
10. Address retention: prefer coordinates; if an address was sent, the atom notes that a provider may retain it.

---

## 14. What this contract does not decide

Numeric credit ceilings; which Texas Candidate Sites exist; Mission Plan compiler details; Workstream DAG; the exact Reject / Conditional / Strong Fit predicate; Skeptic Review prompt; Concept Test geometry math; UI chrome. Those tickets must import this schema.
