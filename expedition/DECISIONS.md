# Site Expedition — frozen build decisions

**Frozen:** 2026-08-15  
**Authority:** grilling rounds + [`FULL_FEASIBILITY_DIAGNOSIS.md`](../FULL_FEASIBILITY_DIAGNOSIS.md) + [`.scratch/site-expedition-build-plan/mvp-contract.md`](../.scratch/site-expedition-build-plan/mvp-contract.md)  
**Status:** Implementation authorized.

This addendum does not reopen product vision. It records the decisions that unblocked the first commit.

## Product

- US-wide Check-a-Site. Find-a-Site means a user-supplied or curated list, never a fake national listing feed.
- Labels: `LISTED` only with a licensed assertion; otherwise `USER SITE` or `POTENTIAL`.
- Warehouse is the visual hero. Home, Farm, and Data Center use the same backend and a thinner board.
- No accounts, collaboration, uploads, notifications, or production SaaS.

## Spend

- Soft cap: **20,000** Mireye credits for this build + verification.
- Hard stop: **25,000**. The ledger refuses the next metered call at 25,000.
- Default Expedition cap: **150** ordinary credits. Parcel-group fields are opt-in only.
- Quote before every metered Mireye call. Live vs replay labels are mandatory.

## Routes

- Working via Application Default Credentials + quota project `gen-lang-client-0261050164`.
- The Maps key stays restricted to tiles / Aerial / Maps. Do not send Routes through it.

## Models

- Default: Vertex `gemini-3.5-flash-lite` with `thinking_level=MINIMAL`.
- Fallback: Vertex `gemini-3.7-flash` with `thinking_level=LOW`.
- Optional: Azure OpenAI / GPT-5.6 Luna when configured and when a reviewer bake-off prefers it.
- Swappable. Verdicts stay in deterministic code. The model never sees held-out gates.

## Evaluation

- Expected gates live only in `verify/gates.json`.
- The engine, UI, and any Expedition sub-agent never import that file.
- Scorer compares a finished Expedition packet to the gate after the run.

## Concept Studio

- One parametric, rights-cleared warehouse asset generated in-repo (`assets/warehouse.gltf`).
- Three-case Concept Test passed 2026-08-15 with no Google tiles and no parcel fetch (`concept.py`).
- `FUTURE` may appear as a labeled visual concept. `FIT` stays deferred (no independently licensed parcel envelope).

## Flood / height

- Default height witness is USGS 3DEP (Mireye) vs NASADEM (Earth Engine).
- FABDEM is not on the default path.
- JRC-through-Mireye and JRC-through-Earth-Engine share independence group `JRC_GSW`.
