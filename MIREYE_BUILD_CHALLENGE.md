# Mireye Build Challenge

> **Combine Mireye with something weird. Solve a real problem.**

---

## Overview

The Mireye Build Challenge asks builders to create an **agent** that uses Mireye’s physical-world data APIs (and MCP server) together with some unexpected second data source — and to solve a problem that real people lose money, time, or health over today.

This is **not** a “put a map on a website” contest. The hard rule is agents: systems that **reason, decide, and act** on physical-world data.

---

## What Mireye Gives You

Mireye provides **APIs and an MCP server** for building applications for the physical world.

For any US address or coordinate, you can pull hundreds of cited facts about a place, including:

| Category | Examples |
|---|---|
| Terrain | Elevation, slope, aspect, land cover |
| Hazards | Flood zones, wildfire exposure, wetlands, coastal distance |
| Power & utilities | Transmission lines, power plants, gas pipelines, sewer service |
| Water & soil | Drainage, soil type, related land characteristics |
| Buildings & land | Parcel records, land use, jurisdiction |
| Other site context | Market/valuation signals where available via templates |

**Every value comes back with its source and a timestamp**, so what you build can show its work (citations, not vibes).

---

## The One Hard Rule: Build an Agent

You must build an **agent** — something that:

1. **Reasons** over physical-world data  
2. **Decides** (filters, ranks, recommends, flags risk, routes action)  
3. **Acts** (notifies, files, updates a system, produces an actionable output)

What they do **not** want:

- A static website with a map
- A thin UI wrapper around a single Mireye call with no decision loop
- Demo theater with no real workflow

---

## What They’re Judging

### 1. What did you combine us with?

Mireye is one input. The interesting part is what sits next to it.

Examples of “weird / adjacent” combinations they call out:

- Court filings  
- Permit databases  
- Satellite imagery  
- Ship tracking  
- eBird  
- Spot GPU pricing  
- Tax-delinquency rolls  
- Local news  

### 2. Is it a real problem?

Someone should lose **money, time, or health** today because this doesn’t exist.

### 3. Who writes the cheque?

“Developers might like this” is not a buyer.  
Name a real buyer: underwriter, wind developer, city agency, renter, lender, land buyer, etc.

---

## Prize Structure

| Place | Prize |
|---|---|
| **1st** | An internship at Mireye — come build this stuff with them |
| **2nd** | $2,500 (2.5 Million credits) |
| **3rd** | $2,000 (2 Million credits) |
| **4th** | $1,700 (1.7 Million credits) |
| **5th** | $1,400 (1.4 Million credits) |
| **6th** | $1,100 (1.1 Million credits) |
| **7th** | $800 (800k credits) |
| **8th** | $500 (500k credits) |

---

## Inspiration Ideas (Do Not Build These)

These are example directions they floated — explicitly marked as **don’t build these** (use them as inspiration only):

### Eagle-strike screening for wind developers
They know where golden eagles nest. Developers currently pay consultants five figures to learn this too late.

### Foundation forensics
Cross shrink-swell soils and bedrock depth against building age — why houses on one street crack and the next street doesn’t.

### Which way the smell blows
Prevailing wind against hazardous facilities, crossed with rental listings. Renters can’t check this today.

### Heat that kills
Wet-bulb temperature, tree canopy, and housing density, crossed with outage data. Cities are funded to answer this and often can’t.

### What’s listed under your dirt
Endangered species with critical habitat on a parcel — the thing that blocks a project after you’ve already bought it.

### Carbon-aware compute routing
Grid carbon intensity, power price, and fibre availability against spot GPU prices.

### Is the river fishable today
Live federal gauge flow, crossed with guides and weather.

---

## Getting Started

### Accounts & promo codes

| Code | What it unlocks |
|---|---|
| `GROWTH` | Free growth-tier account for **one month** |
| `BUILD` | Free build-tier account for **one month** |

- Sign up: [https://www.mireye.com/account](https://www.mireye.com/account)  
- Need more credits? Email **founders@mireye.com** — they’d rather you had room to work.

### Starter skills / templates

Nine copy-paste starter skills: [https://www.mireye.com/templates](https://www.mireye.com/templates)

Each template is a real problem + real endpoint + working skill file you can drop into an agent’s skills folder.

| Template | What it does | Pattern |
|---|---|---|
| **Land Read** | Terrain and land-cover facts for one address (elevation, slope, soil, land cover), every value cited | Single address / batch |
| **Power Read** | Grid & utility facts — nearest transmission line + voltage, power plant, gas pipeline distance, sewer service | Single address / batch |
| **Hazards Read** | Flood, wetland, wildfire exposure (FEMA / NOAA / USFWS / Copernicus citations) | Single address / batch |
| **ICP Finder** | Screen candidate addresses against an ideal-customer profile; enrich + filter | Bring-your-own list |
| **Property Diligence Copilot** | Full dossier — jurisdiction, hazard flags, parcel record in one call | Single address |
| **Lending & Appraisal Support** | Opportunity-zone status, county market trends, parcel valuation history | Single address |
| **CRM Address Cleanup** | Clean messy CRM/lead addresses into canonical records + review queue | Bring-your-own list |
| **Insurance Book Monitoring** | Re-screen a book of insured properties for flood/wildfire exposure | Bring-your-own policy list |
| **Grounded Location Q&A** | Plain-English location Q&A with citations (not hallucination) | Single query / streaming chat |

---

## Timeline

| Milestone | Date |
|---|---|
| **Deadline** | 15 August 2026 |
| **Winners announced** | 20 August 2026 |

---

## Submission Form Fields

Submit via the Google Form:

[Mireye Build Challenge Form](https://docs.google.com/forms/d/e/1FAIpQLScSRW3GBJyH-lyKAhpIJFNi-ca-LkWIXYLSfKZF3PAut7lvuw/viewform)

| Field | Required | Notes |
|---|---|---|
| **Name** | Yes | |
| **Email** | Yes | |
| **Git Repo Link** | Yes | Public (or accessible) repo with your agent |
| **One Pager Link** | Yes | Short write-up of problem, buyer, combo, and how it works |
| **2 Minute Demo Video Link** | Optional (recommended) | Best way to show the agent reasoning and acting |
| **Feedback for Mireye** | Yes | Product/API feedback |

---

## Submission Checklist (Practical)

Use this when you’re ready to ship:

- [ ] Agent uses Mireye as a core physical-world input (API and/or MCP)
- [ ] Agent combines Mireye with at least one non-obvious second source
- [ ] Clear real-world problem (money / time / health)
- [ ] Named buyer who would pay
- [ ] Agent loop: reason → decide → act (not just display)
- [ ] Citations / sources surfaced where claims are made
- [ ] Git repo linked and runnable / documented
- [ ] One-pager explains problem, buyer, data combo, and demo path
- [ ] (Recommended) ≤2 minute demo video
- [ ] Form feedback filled out
- [ ] Submitted before **15 August 2026**

---

## One-Pager Outline (Suggested)

A tight structure that matches how they’re judging:

1. **Problem** — Who loses what today?  
2. **Buyer** — Who writes the cheque?  
3. **Weird combo** — Mireye + what else? Why that pairing?  
4. **Agent behavior** — What it reasons over, what it decides, what action it takes  
5. **Demo path** — One concrete scenario end-to-end  
6. **Why this couldn’t be a dumb map** — Decision/action that makes it an agent  

---

## Quick Links

| Resource | URL |
|---|---|
| Challenge form | https://docs.google.com/forms/d/e/1FAIpQLScSRW3GBJyH-lyKAhpIJFNi-ca-LkWIXYLSfKZF3PAut7lvuw/viewform |
| Sign up / account | https://www.mireye.com/account |
| Starter templates | https://www.mireye.com/templates |
| Extra credits | founders@mireye.com |

---

*Source: Mireye Build Challenge Google Form + mireye.com/templates (as of document creation).*
