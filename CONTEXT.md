# Universal Site Selection

This context describes how the product represents a user's intended use, the places being considered, and the evidence-backed result of screening them.

## Language

**Mission**:
The activity the user intends to place on or perform at a site, such as living, farming, warehousing, or operating a data center.
_Avoid_: Property type, vertical

**Mission Plan**:
The agent-compiled requirements, decision roles, evidence needs, and investigation strategy for a Mission. A user confirms the Mission Plan before candidate screening begins.
_Avoid_: Questionnaire, prompt, chat transcript

**Site Form**:
The physical form the user will consider: an existing built asset, developable land, or either.
_Avoid_: Mission, property category

**Search Region**:
The geographic area within which the product may discover candidate sites. A Search Region is not itself a property or candidate.
_Avoid_: Candidate, property

**Find a Site**:
The entry path that begins with a Search Region and Mission, sources Candidate Sites, and then analyzes them.
_Avoid_: Discovery mode, browse mode

**Check a Site**:
The entry path that begins with a user-supplied address or pin and analyzes that Candidate Site directly.
_Avoid_: Analysis mode, property lookup

**Candidate Site**:
A particular parcel, building, or listing that can be screened for a Mission.
_Avoid_: Search Region, general location

**Market Availability**:
A timestamped assertion from an authorized source that a Candidate Site is offered for sale or lease. Market Availability is distinct from vacancy, physical suitability, and legal authorization.
_Avoid_: Empty land, available-looking, purchasable

**Listed Site**:
A Candidate Site whose Market Availability is established by a named authorized provider with a listing identity and last-seen time. The UI label is `LISTED`.
_Avoid_: Available-looking parcel, assessor record, Potential Site

**User Site**:
A Candidate Site supplied by the user as an address or pin. A User Site is not Market Availability. The UI label is `USER SITE`.
_Avoid_: Listing, discovered inventory

**Potential Site**:
A promising parcel or location for which Market Availability has not been established. The UI label is `POTENTIAL`.
_Avoid_: Listing, available property

**Strong Fit**:
A Candidate Site that passes every supported mandatory requirement and compares favorably on the user's preferences.
_Avoid_: Safe, approved, certified

**Reject**:
A Candidate Site contradicted by reliable evidence on at least one user-declared mandatory requirement.
_Avoid_: Bad property, universally unsuitable

**Conditional**:
A potentially suitable Candidate Site with a material Verification Gap that prevents a final supported result.
_Avoid_: Pass, probably approved

**Verification Gap**:
A missing authoritative fact that must be supplied by a responsible authority, provider, professional, owner, or broker.
_Avoid_: Pass, minor caveat

**Evidence Atom**:
One cited answer to one decision question about one Candidate Site, including its kind, authority, Spatial Support, clocks, and allowed decision effect.
_Avoid_: API response, score, packet row

**Source Family**:
The underlying dataset an Evidence Atom is drawn from, regardless of which API wrapped it.
_Avoid_: Vendor, provider brand

**Independence Group**:
The corroboration key shared by Evidence Atoms that are not independent of each other. Atoms in the same Independence Group cannot corroborate.
_Avoid_: Second source, confirmation

**Spatial Support**:
The geometry and scale an Evidence Atom actually describes: point, buffer, parcel, building, watershed, region, or network.
_Avoid_: Location, pin, parcel (when the metric is a buffer)

**Semantic Absence**:
A source-defined “not present” result, distinct from a failed or unknown retrieval.
_Avoid_: Missing data, error, pass

**Evidence Coverage**:
The proportion of decision-relevant requirements supported by usable evidence. Evidence Coverage is distinct from Mission fit.
_Avoid_: Confidence score, suitability score

**Scan Budget**:
The user-approved limit on investigation depth, latency, and external-data cost. The standard levels are Quick, Standard, and Deep.
_Avoid_: Subscription tier, suitability level

**Investigation**:
A budgeted, adaptive sequence of evidence collection, contradiction checks, and follow-up tests chosen by the agent for a Mission Plan and Candidate Site.
_Avoid_: Fixed report, data dump

**Site Expedition**:
One goal-directed run that may investigate a single site, multiple cities, a corridor, or a wider Search Region and returns compared Candidate Sites and evidence-backed results.
_Avoid_: Search request, report run

**Workstream**:
A parallel, goal-owned part of a Site Expedition that chooses and adapts its own Investigation. Workstreams are defined by questions or hypotheses, not by individual data providers.
_Avoid_: API call, tool wrapper, role-playing agent

**Skeptic Review**:
An independent attempt to disqualify a leading Candidate Site, expose missing authority or correlated evidence, and compare it with the strongest alternative.
_Avoid_: Summary, second opinion without new tests

**Pre-design Model**:
An editable conceptual design grounded in the known site geometry, selected program, and stated assumptions. It is not a permit-ready architectural or engineering design.
_Avoid_: Final CAD, approved plan, permit set

**Concept Test**:
The agent's evaluation of whether a Pre-design Model can plausibly fit a Candidate Site under the known physical constraints and stated assumptions.
_Avoid_: Building approval, permit check, final design
