# Sharpened objective — what to build

**Date:** 12 Aug 2026  
**Status:** decision record (statutes + Earth Engine probe + GCP/AWS pass)  
**Probe:** `ee-explore/objective_sharpen/` (labeled Austin reroof permits vs neighbor control)

---

## One sentence

Build a **nonrenewal challenge agent**: the homeowner (or their public adjuster) drops in the carrier’s cancellation/nonrenewal notice; the agent reads the state’s aerial-imagery rules, checks the carrier’s image date against the legal clock, attaches an independent USDA NAIP timeline with capture dates, cites Mireye site facts, and emits a challenge packet with the cure deadline.

Not “we dated your shingles from space.”

---

## Why this, not the other skins

| Candidate | Verdict | Why |
|---|---|---|
| **Counter-Adjuster as roof CSI** | **Do not build** | EE cannot reliably date a like-for-like reroof at house scale. 10 m embeddings do not separate a reroof from the neighbor. Sentinel-2 cannot. NAIP can *sometimes* show a material change (shingle→metal) and often cannot (same-color redeck). Texas NAIP in EE currently ends mid-2022, so a 2023 reroof has no public after-image yet. |
| **Counter-Adjuster as statute-vs-record agent** | **BUILD THIS** | 2024–26 state law created a *checkable* workflow that does not need roof CSI. Georgia and Indiana require date-stamped images, a max age, a 60-day cure, and renewal if the homeowner fixes the listed condition. That is an agent loop: parse notice → apply rulebook → attach public dated imagery → emit packet. |
| **Title Pirate** | Second, later | Vacant-land change is the right *scale* for satellites, but “untouched = fraud” is neglect vs care, not title vs pirate. No labeled fraud set in this pass. Different buyer (title underwriter), different liability. Same forensic engine later. |
| **Shadow Scout / methane** | Hold / killed | Unchanged. |

The 2024–26 wave is **aerial-imagery due process on nonrenewal**, not a new claims market. Claims (hail/flood) are a different fight; AWS NEXRAD can wait.

---

## The fight (be precise)

**Nonrenewal / cancellation of an owner-occupied homeowners policy, where the carrier used aerial or satellite images to name a property condition.**

Not: a hail/wind claim file. Not: new-business underwriting of an applicant who was never a customer. Those may reuse the engine later.

Money on the table: keep the policy, or buy time (60 days) to repair and force a renewal offer. Public adjusters already get paid when a denial/nonrenewal is reversed; they are the buyer. Homeowners are the user. Roofers are a channel.

---

## The checkable hook (primary sources)

### Hard statutes (the product spec)

**Georgia — O.C.G.A. § 33-9-45**, added by [HB 1344](https://gov.georgia.gov/document/2026-signed-legislation/hb-1344/download) (signed 12 May 2026, **effective 1 Jan 2027**). When an admitted insurer uses aerial *or* satellite images as the basis for cancellation/nonrenewal of owner-occupied residential coverage, it **shall**:

1. Put **date-stamped copies** (or access instructions) in the notice, plus the steps and repair standards to reverse the decision. Images **must have been taken within 12 months** of the notice.
2. Name a point of contact and a process to submit proof of repair.
3. Provide an appeal process for errors/misunderstandings.
4. Give **at least 60 days to cure**, even if that outruns the ordinary nonrenewal notice in § 33-24-46.
5. **Offer renewal or rescind** if the owner proves the listed condition is cured.

Georgia’s separate SB 35 (60-day nonrenewal notice, eff. 1 Jan 2026) is *not* the aerial law. SB 409 is a leftover bill; HB 1344 is the enacted aerial section.

**Indiana — IC 27-7-12-6.5**, [HEA 1260](https://iga.in.gov/pdf-documents/124/2026/house/bills/HB1260/HB1260.06.ENRS.pdf) (**effective 1 Jul 2026**). If aerial images are the **sole reason** for nonrenewal: photos **within 24 months**; notice must say how to request copies; point of contact for proof of repairs; appeal process; **60 days to remedy**; insurer must offer renewal if the listed defects are resolved (may still nonrenew for an unrelated reason).

**Louisiana — R.S. 22:1339** ([Act 151 / SB 242](https://legis.la.gov/Legis/Law.aspx?d=1389148), eff. 22 May 2024). Insurer **shall not solely rely** on aerial images (explicitly including satellites) to identify the condition behind cancellation/nonrenewal **unless those images are within 24 months**. Images used only to *locate* the property have no age cap. Weaker than GA/IN: no mandatory disclosure, no 60-day cure, no forced renewal. Still a checkable “sole reliance + image age” test *if the notice or file shows what they used*.

### Bulletins (softer, still usable as a checklist)

Michigan DIFS [Bulletin 2025-12-INS](https://www.michigan.gov/difs/legal/bulletins/2025-bulletins) (6 Jun 2025): imagery must be accurate/current; cosmetic roof discoloration is not sole grounds; share images and allow challenge. **This is a bulletin, not a statute** — the verdict overstated it.

Nearmap’s own [state tracker](https://www.nearmap.com/solutions/insurance-regulations-by-state) (updated 14 Jul 2026) is a vendor secondary source, but it matches the primary texts above and adds: CO Bulletin B-5.57 (12-month underwriting imagery, Mar 2026); KY (12-month date stamp, satellite-alone insufficient, Mar 2026); RI (15-month, Aug 2025). Treat those as v1.1 geographies after GA/IN.

**Correction to `DEEP_RESEARCH_VERDICT.md`:** “LA 24-mo / MI disclosure / GA 60-day” mixed three different instruments. The real gold standard is **GA § 33-9-45 and IN § 6.5** (disclose + max age + cure + must-renew). LA is sole-reliance-plus-age only. MI is guidance.

---

## What Earth Engine actually proved (12 Aug 2026)

Labeled set: City of Austin issued building permits (`3syk-w9eu`) for reroofs in 2022–23, plus the next-door neighbor of the shingle→metal house. Collection `USDA/NAIP/DOQQ` + `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` + Sentinel-2 SR. Thumbs in `ee-explore/objective_sharpen/thumbs/`.

| Site | Known event | NAIP 2020→2022 roof Δ | yard Δ | Embedding 2018→2024 roof L2 | Read |
|---|---|---|---|---|---|
| 3611 Winfield Cv | shingle→metal, 2022-03-24 | **9.05** | 4.79 | 0.291 | Modest roof>yard; same-season pair (both 8 Jun) |
| 3605 Winfield Cv | **control**, no roof permit | **2.97** | 4.39 | 0.308 | Neighbor, same dates — embeddings match the reroof |
| 2505 Redleaf Ln | full redeck, 2022-03-16 | 5.13 | **5.73** | 0.301 | Like-for-like redeck **invisible** |
| 4302 Far West Blvd | metal reroof, **2023-06-30** | 20.23 | 19.38 | 0.301 | Event is *after* last NAIP — pair is not the reroof |
| 2609 Ellise Ave | re-roof, 2022-01-05 | 27.69 | 22.01 | 0.318 | 2020 capture is **18 Oct**, 2022 is **8 Jun** — season, not shingles |

Other hard facts from the same run:

- Austin NAIP in EE: 2005…**2022**. Latest capture **2022-06-08** (one tile 2022-06-11). Catalog global max is 2023-11-17; Texas is behind. A public exhibit is often 12–24 months stale — which is exactly why the *carrier’s* 12-month clock matters and why we must print **capture dates**, not “current aerial.”
- Every NAIP year we pulled has an ISO capture date. That date is the exhibit. USDA NAIP is public domain.
- 10 m annual embeddings: reroof roof L2 ≈ 0.29–0.32, control 0.31. **Cannot carry a reroof claim.**
- Sentinel-2 10 m NDVI 2021→2023: noise. **Cannot carry a reroof claim.**
- Tree canopy occludes roofs in the NAIP thumbs. Mireye `tree_canopy_pct` is a caveat, not a decoration.
- Early NAIP (e.g. 2006 San Leon) is RGBN with no `B` band — don’t mosaic blindly.

**Satellite job for v1**

| Must do | Optional | Must not claim |
|---|---|---|
| Independent public timeline with **capture dates** (NAIP; S2 as coarse extra) | Side-by-side thumbs when a material change is obvious | “We dated this reroof” / embedding CSI / Sentinel saw new shingles |
| State that the latest public epoch may be older than the carrier’s image | Flag “color/material change consistent with a reroof” only when roof Δ ≫ yard Δ *and* same season | That NAIP is as fresh as EagleView/Nearmap |

---

## How the pieces fit (Mireye × EE × GCP × AWS)

```
notice PDF ──► Gemini / Document AI
                 extract: address, effective date, stated defect,
                          carrier image date (GA/IN put it in the notice)
                      │
                      ▼
              Mireye lookup/fetch
                 political_region → which statute
                 parcel + building + tree_canopy_pct + flood/wildfire
                 every value cited
                      │
                      ▼
              Earth Engine
                 NAIP epochs + capture dates + public-domain thumbs
                 (optional S2; skip embeddings for the claim)
                      │
                      ▼
              rule engine
                 image_age_ok?  disclosed?  cure_clock?  cosmetic_only?
                      │
                      ▼
              ACT: challenge packet
                 covering letter citing § 33-9-45 / IC 6.5 / RS 22:1339
                 deadline calendar (60-day cure, notice period)
                 NAIP exhibit with dates
                 Mireye citation page
                 DOI / insurer appeal checklist
                 notify the PA
```

**Mireye (identity + jurisdiction + cited record).** Credits on the free plan were exhausted during this pass (`402 credits_exhausted`, reset 1 Sep 2026) — use the challenge `BUILD`/`GROWTH` codes. Fields that actually feed this workflow: `political_region` / `political_county` (rulebook), `parcel_*` (identity), `primary_building_*`, `tree_canopy_pct`, `ndvi_current` / `ndvi_change_5y` (context, not roof age), `fema_flood_zone` / wildfire / hail frequency (why the carrier may be jumpy). Do not rebuild FEMA/wildfire — that’s already their Insurance Book Monitoring template, inverted.

**Earth Engine.** The forensic layer is **time + public-domain pixels**, not a 10 m embedding. Export thumbs to GCS. NAIP ToS: public domain — you *may* attach the bytes. That is the opposite of Google Aerial View.

**GCP that changes the product**

- **Gemini on Vertex (or Document AI custom extractor)** — the notice is the input. Without parsing the carrier’s image date, the 12/24-month clock cannot run. This is the “weird second source”: the **adverse-action document**, not another satellite.
- Cloud Run — reason → decide → act.
- Cloud Storage — NAIP exhibits.
- Gmail/SendGrid/Slack — deliver the packet to the PA.

**Google Maps Aerial View / Street View / Earth 3D.** Demo candy only. [Aerial View ToS](https://developers.google.com/maps/documentation/aerial-view/how-to): cannot download, store, or cache the video. You may store `videoId`. Do not put Google pixels in the legal exhibit.

**AWS.** NEXRAD on `s3://unidata-nexrad-level2` (no-sign-request) is the right third source for a *claims* “did hail hit this roof?” agent. That is product #2. Do not drag it into v1 — it changes the buyer, the statute, and the demo. Sentinel-on-AWS is a worse Earth Engine.

---

## Agent behavior (reason → decide → act)

1. **Reason** over: parsed notice fields, Mireye jurisdiction + citations, NAIP capture dates, the statute text for that state.
2. **Decide** one of: `CLOCK_FAIL` (image older than the cap) / `DISCLOSURE_FAIL` (no date-stamped copies) / `CURE_OPEN` (clock running, list the repair standard) / `COSMETIC` (streaking/discoloration as sole basis, bulletin states) / `PASS` (carrier appears compliant; still attach the public timeline).
3. **Act:** write the packet; start the 60-day calendar; email/Slack the PA; optionally file a DOI consumer complaint *draft* (human sends it — do not auto-file, unauthorized practice / licensing).

Stay behind the line: this is a **checklist + exhibit assembler**, not legal advice and not a filing robot.

---

## Demo path (one concrete run)

Indiana or Georgia (pick the state whose law is already in force on demo day: IN as of 1 Jul 2026; GA as of 1 Jan 2027 — if demo is still Aug 2026, **demo Indiana** or Louisiana Act 151).

1. Synthetic notice: “nonrenewal effective 15 Oct 2026 for roof condition; aerial image dated **March 2024**.”
2. Address: a real GA/IN/LA house (or Austin as the imagery stand-in with a banner that the statute is IN).
3. Agent: image age = 19 months → Indiana 24-month cap *passes*, Georgia 12-month cap *fails*. Show both rulebooks. Attach NAIP 2020-06-08 vs 2022-06-08 with those dates printed.
4. Packet: “request copies; 60-day cure; here is the public timeline; here is Mireye’s cited flood/canopy record.”
5. Video: the decision flip when you change the carrier image date from 8 months to 19 months. That is the agent. Not a map.

---

## Why this could not be a dumb map

The output is a **deadline and a letter**. Moving the carrier’s image date changes the decision. The map is an exhibit inside the packet.

---

## Open questions only a build (not more reading) can close

1. Can Gemini extract `image_date` + `stated_defect` from a real (redacted) nonrenewal PDF at usable accuracy?
2. Does Georgia/Indiana NAIP in EE have a 2023 epoch (Austin does not)?
3. One real PA: will they use a packet that leads with statute clocks rather than “new shingles”?

Roof-dating more houses will not change the objective. The probe already killed that as the load-bearing claim.
