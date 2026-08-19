Label: wayfinder:map
Status: open

# Site Expedition Challenge MVP — Wayfinder Map

## Destination

A reviewed, implementation-ready technical specification and sequenced build checklist for the Mireye Site Expedition challenge MVP. It must let a build agent implement and verify the product without reopening the approved product vision, inventing unsupported claims, or guessing at service, data, agent, UI, or demo contracts.

## Notes

- Domain: US-only, desktop-first, single-user Site Expedition decision support for operational real estate, with Warehouse / Light Industrial as the hero Mission and Home, Farm, and Data Center as thinner proof recipes.
- Product authority: [Complete Grilling Session Record](../../grilling_session.markdown).
- Feasibility authority: [Full Feasibility Diagnosis](../../FULL_FEASIBILITY_DIAGNOSIS.md), [Requirement Ledger](../../feasibility/REQUIREMENT_LEDGER.md), and [Primary Source Audit](../../feasibility/PRIMARY_SOURCE_AUDIT.md).
- The product grilling is complete. Do not reopen approved product direction; the first ticket only freezes it into a concise implementation contract and reconciles feasibility wording.
- Domain language: [Universal Site Selection Context](../../CONTEXT.md). Use its terms exactly; sharpen it with `/domain-modeling` when a ticket resolves a new domain distinction.
- Every session should consult `/wayfinder`; use `/grilling` plus `/domain-modeling` for human decisions and `/prototype` when behavior or appearance needs a concrete artifact.
- This map plans; it does not implement the product. Only tickets explicitly typed `task` may perform bounded prerequisite work needed to settle a decision.
- Consequential feasibility claims must distinguish documented, configured, tested, failed, partial, inferred, blocked, untested, and infeasible.
- Unknown, absent, stale, failed, contradictory, or low-authority evidence can never silently become a pass.
- Use names, not bare ticket numbers, in human-facing narration and resolution summaries.
- No new external research ticket is open initially because the exhaustive feasibility investigation already covers the current frontier. Create one only when a later decision exposes a genuinely missing fact.

## Decisions so far

- [Freeze the approved challenge MVP contract](./issues/01-freeze-the-approved-challenge-mvp-contract.md) — Warehouse hero, thin secondary Missions, honest fallbacks, and Concept Studio as a proof-gated claim are frozen in [mvp-contract.md](./mvp-contract.md).
- 2026-08-15 grilling close: US-wide Check-a-Site; 20k/25k Mireye caps; Routes via ADC; Vertex Flash-Lite default with Luna optional; held-out verification corpus; implementation started in [`expedition/`](../../expedition/). See [`expedition/DECISIONS.md`](../../expedition/DECISIONS.md).
- [Define the canonical evidence contract](./issues/05-define-the-canonical-evidence-contract.md) — one Evidence Atom schema, Independence Groups, Spatial Support, and three clocks are frozen in [evidence-contract.md](./evidence-contract.md).

## Not yet specified

- Exact remediation decisions for failures discovered by the first integrated Expedition prototype; these cannot be phrased until that behavior is designed and tested.
- Final submission capture, repository presentation, and judge-facing evidence packaging; their exact questions depend on the truthful demo contract and implemented verification results.
- Whether any secondary Mission deserves promotion beyond a thin proof recipe if the hero Expedition finishes with substantial schedule or credit headroom.

## Out of scope

- Collaboration, invitations, teams, roles, shared editing, accounts, signup, email, notifications, and production background-job infrastructure.
- User evidence uploads, unrestricted live-source discovery, arbitrary code installation, and unsupported nationwide commercial/farm/data-center inventory.
- Permit-ready CAD/IFC, engineering or architectural certification, existing-building interior reconstruction, and ten live-generated architectural presets.
- Claims of utility headroom, redundant enterprise fiber, water rights/capacity, zoning approval, listing availability, vacancy, building condition, title, permits, or legal permission without the responsible authority.
- Machine interpretation, geometry extraction, prohibited caching, or prohibited export of Google imagery and 3D content.
- Production SaaS persistence, private Vault, broad export suites, and account-bound history.
- Building the product itself; execution begins only after this map reaches its destination and the resulting specification is approved.
