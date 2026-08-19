# Feasibility requirement ledger

**Authority:** `grilling_session.markdown`, especially Sections 12–14, 17, and 19  
**Audit date:** 2026-08-15 UTC  
**Status vocabulary:** `DOCUMENTED`, `CONFIGURED`, `TESTED_OK`, `TESTED_FAILURE`, `PARTIAL`, `INFERRED`, `BLOCKED`, `UNTESTED`, `INFEASIBLE`

This is the coverage ledger used while producing `FULL_FEASIBILITY_DIAGNOSIS.md`. A capability is not feasible merely because an API or dataset exists.

| Requirement / dependency | Required proof | Current status | Principal evidence / unresolved work |
|---|---|---|---|
| Mission compilation from structured controls | Schema, deterministic constraints, model role boundary | PARTIAL | Product contract exists; no runtime compiler test |
| Reviewed source and field manifests | Current Mireye fields, exact datasets, versioning | PARTIAL | Live catalog checked; bundled manifests drifted; proposed concise registry not implemented |
| Live Mireye integration | Auth, balance, quote, field fetch, provenance, latency | TESTED_OK | Local auth configured; balance 56; prior 2026-08-15 live receipts; no new metered call due scarce balance |
| Address / coordinate / parcel resolution | Ambiguity, precision, parcel match, retention | PARTIAL | API contract documented; coordinate and one rooftop path proven; ambiguity/cross-provider agreement not benchmarked |
| Mireye batching and partial failure | 25-location behavior, retry/absent semantics | PARTIAL | API contract documented; three-site prior batch; water/sewer and SSURGO timeouts observed |
| Candidate acquisition | Lawful live sources by Mission and truthful labels | PARTIAL | Residential RentCast documented but unconfigured; commercial/farm/data-center feed blocked; curated/user sites feasible |
| Core site screening | Small Mission-aware Mireye field sets | TESTED_OK | Home, Farm, Warehouse, Data Center screens ran on 2026-08-15; thresholds remain user/config driven |
| Flood rewind | Present facts + historical witness + DEM disagreement | TESTED_OK | San Leon/Austin controls and replay; JRC source family is shared; FABDEM receipt is noncommercial-only and must not be the default |
| Farm history | Current crop + annual CDL + rainfall | PARTIAL | Two corrected pins worked; SSURGO timed out; water rights, yield, phenology unproven |
| Grid readiness | Grid/water/fiber screen plus authority boundary | PARTIAL | Ashburn/Abilene screen works; deliverable MW and enterprise redundancy remain mandatory gaps |
| Route reality | Actual road-network time/distance | TESTED_FAILURE | Routes API service blocked; legacy Distance Matrix not enabled; no route result |
| Land change | Correct spatial fractions and independent validation | PARTIAL | Corrected Dynamic World computation ran; NLCD/ground-truth/window sensitivity not validated |
| Labor access | LODES/Census context plus routes | UNTESTED | Official data documented; not integrated or measured |
| Environmental record | Mireye screen plus ECHO drilldown | PARTIAL | Mireye fields documented; direct ECHO workflow untested |
| Climate trajectory | Historical baseline plus scenario ensemble/range | PARTIAL | One MIROC6 SSP2-4.5 path ran; ensemble and decision calibration absent |
| Scene context | Aerial lookup and 3D fallback | PARTIAL | Two ACTIVE videos, honest 404s, 3D root 200; saved signed playback URL must be removed; browser runtime unverified |
| Workstream orchestration | Parallel goal-owned jobs, cancellation, selective deepening | UNTESTED | Architecture specified; no orchestration benchmark or cancellation implementation |
| Early veto and replacement | Stop spend after veto; replace/widen lawfully | PARTIAL | Deterministic veto exists; replacement/widening not exercised end to end |
| Comparison and verdict engine | STRONG FIT / REJECT / CONDITIONAL semantics | PARTIAL | Two-case KEEP/KILL replay works; semantics and broader Mission matrix not implemented/validated |
| Skeptic Review | Detect shared source, staleness, geometry mismatch | PARTIAL | Two six-case synthetic runs passed identically; no real evidence-graph benchmark |
| Failure recovery | Timeouts, 404, quota, partials, contradiction | PARTIAL | Individual failures observed; end-to-end recovery/continuation not benchmarked |
| Agent model routing | Available model, positive/negative/ambiguous routing, latency | TESTED_FAILURE | Anthropic was callable at ~2.2 s but consistently misrouted Home into Farm; Gemini blocked; deterministic validator required |
| Scan budgets | Quick/Standard/Deep cost and latency | PARTIAL | Mireye quotes available; full wall-clock distribution and model/Routes costs not measured |
| Acquisition/verification brief | Reproducible cited output without prohibited content | PARTIAL | Flood packet exists; universal brief contract not implemented |
| Warehouse Concept Studio | Coherent placed warehouse concept and Concept Test | UNTESTED | Iteration 7 contains prebuilt visual exhibits; no geometry-grounded placement/test proof |
| Google content policy | Streaming, cache, screenshot/record/export boundaries | DOCUMENTED | Official service policies constrain storage, analysis, and recordings |
| Desktop planning UI | Tiles, cards, rail, scorecards, TODAY/FIT/FUTURE | PARTIAL | Iterations are static prototypes; no live Expedition integration or browser performance measurement |
| Two-minute truthful demo | Live steps, transparent cache, visible failures | PARTIAL | Narrow flood replay fits; full hero flow cannot honestly close Routes/availability/capacity |
| Security/privacy | Server-side secrets, provider disclosure, redaction, cache keys | PARTIAL | Some server-side key handling exists; direct static HTML/key risks and log/retention controls need hardening |
| Licensing/provenance | Source authority, independence, geometry/version, redistribution | PARTIAL | Cache schema omits fields; Google visuals presentation-only; FABDEM is CC BY-NC-SA and Aerial signed URL persistence is invalid |
| Challenge fit | Mireye core + weird source + real buyer + agent action | TESTED_OK | Flood-rewind path satisfies core brief; universal vision is viable only with narrow honest demo |
| MVP exclusions | No SaaS/auth/uploads/notifications/unrestricted discovery/CAD claims | TESTED_OK | Scope is explicit; feasibility work made no product/cloud changes |
