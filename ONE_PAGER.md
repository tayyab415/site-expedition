# Site Expedition

**Mireye Build Challenge one-pager**  
Mireye gave agents eyes on the physical world. I built the harness that uses those eyes to decide whether a place can actually take the job.

## Where this came from

I went through Mireye's templates and skills, and the pitch landed. They are not a map company. They are physical-world data endpoints for agents: flood, terrain, grid, parcel, hazards, all cited. Eyes.

The gap I kept hitting is that eyes are not a search. Someone still has to say what they are trying to place (a warehouse, a house, a farm, a data hall), find candidate pins, and then actually decide. That is the expensive, slow part today: brokers, consultants, and operators bouncing between FEMA maps, utility guesses, a drive-time spreadsheet, and a pretty globe that never says no.

So the idea was simple. If you want to open a site, rent, live somewhere, or stand up a warehouse or a business, the agent should take that need, look with Mireye, cross-check with public records and Earth Engine, and tell you which pins survive.

I also made it something you can look at. Google aerial and photorealistic 3D sit on the board so you can see the place you are about to kill or keep. The UI is one board: pick a use, confirm a plan, explore pins. The globe is the view. It is not the verdict.

## Problem

Site selection still burns weeks and five-figure diligence on land that a flood map, a height witness, or a missing utility letter should have killed on day one. The money lost is option time, false starts, and signing on a pin that was never going to work.

## Buyer

Hero buyer: an industrial operator, or the broker / site-selection consultant they hire for warehouse and light industrial.

Same engine also runs Home, Farm, and Data Center, because the need is the same shape: a use, a region or a pin, a hard no, and a list of people to call.

## The combo

- **Mireye** is the cited present-state record: FEMA, terrain, utilities, parcel-grade resolve.
- **Google Earth Engine** is the independent witness over time and height: JRC water history, NASADEM vs USGS 3DEP, Dynamic World land-change.
- **Public APIs** fill discovery and follow-up: OSM for potential pins, EPA ECHO after a proximity hit, Routes for declared drive-time.
- **Google aerial and photorealistic 3D** are the view of the place, labeled presentation. They never score.

That pairing is the point. Mireye says what the official record is today. Earth Engine says whether the ground has been arguing with that record. The globe lets a human look. The verdict stays in code.

## What the agent does

1. Compiles a Mission Plan from the use (warehouse is the visual hero) before it spends a credit.
2. Discovers or accepts candidate sites. Labels stay honest: `USER SITE`, `POTENTIAL`, `LISTED` only with a real listing assertion.
3. Screens with Mireye, then calls Earth Engine and the public follow-ups the record itself makes relevant.
4. Decides in deterministic code: Reject, Conditional, or compare survivors. A model may narrate (Skeptic Review). It never changes the verdict.
5. Acts by emitting a cited verification brief: owner/broker, utility, civil, zoning. Named sources. Named next calls. Not a score.

## Demo path

Warehouse, Texas. Confirm the plan (hard gate: not mapped SFHA; route anchors to Port of Houston and a San Antonio customer). Run five pins.

San Leon Rejects on FEMA present-state. Flood-rewind is history, not the veto. San Marcos survives Conditional, with real drive times and a brief that still demands electrical capacity, truck ingress, zoning, and market availability.

TODAY aerial is up immediately. TODAY 3D and a labeled FUTURE warehouse massing are optional look, not evidence.

## Why this is not a map

A map would show you San Leon. This agent rejects it, cancels the rest of the spend, and writes the packet a human can take to the next authority.
