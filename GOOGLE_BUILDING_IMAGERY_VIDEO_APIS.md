# Google building shots / videos via API — research note

**Verdict:** Yes — but **not through Earth Engine**. The product that matches “API call → cinematic video of a real building” is the **Google Maps Aerial View API** (Maps Platform on GCP). Earth Engine can export **satellite time-series** video; it does **not** serve Google Earth photorealistic 3D building flyovers.

**Sources checked:** Google Maps Platform Aerial View / Map Tiles / Street View / Maps JS 3D docs; Earth Engine export-video guide; Earth Studio render docs. (Aug 2026)

---

## Want X → use Y

| Goal | Use | Callable API? |
|---|---|---|
| Drone-style **MP4 orbit of a US address / building** | **Aerial View API** | Yes — REST |
| Interactive photorealistic **3D buildings** in your app | **Photorealistic 3D Tiles** or **Maps JS `Map3DElement`** | Yes — tiles / JS; video is DIY |
| Custom cinematic flyover you **own as files** | **Earth Studio** (manual UI) | No public API |
| Street-level **facade still** | **Street View Static API** | Yes — HTTP image |
| Multi-year **satellite change** movie of a region | **Earth Engine `Export.video`** | Yes — EE Python/JS/REST |
| Old Earth Plug-in / Earth API | Deprecated / gone | No |

---

## 1. Aerial View API — best match for “building video by API”

**What you get:** Photorealistic 3D aerial videos of **US postal addresses**, simulating a drone circling overhead. Same family of 3D imagery people associate with Google Earth, delivered as short playback URIs.

**API surface (GCP):**

1. `lookupVideoMetadata` — address or `videoId` → existence / freshness / length  
2. `lookupVideo` — returns short-lived playback URIs when `state=ACTIVE`  
3. `renderVideo` — request generation if missing (can take **hours**)

Docs:

- [Overview](https://developers.google.com/maps/documentation/aerial-view/overview)  
- [How to use](https://developers.google.com/maps/documentation/aerial-view/how-to)  
- [Generate video](https://developers.google.com/maps/documentation/aerial-view/generate-video)  
- [Setup](https://developers.google.com/maps/documentation/aerial-view/cloud-setup)

**Auth / enablement:** GCP project + **billing** + enable **Aerial View API** + API key (or OAuth). This is **Maps Platform**, separate from Earth Engine registration.

**Hard blockers:**

- **US addresses only** where Google can render 3D video  
- ToS: **cannot download, store, or cache** the video bytes — embed/playback only  
- You **may store `videoId`** for later lookup ([how-to](https://developers.google.com/maps/documentation/aerial-view/how-to))  
- Pre-rendered set is densest for large buildings / landmarks; other addresses may need `renderVideo`

**Fidelity:** Rooftop + surrounding 3D context; facade recognition is a stated product goal (birds-eye + Street View-like recognition of buildings). Not a true drone with your own flight path.

**Example shape:**

```bash
# Metadata / existence
curl -s "https://aerialview.googleapis.com/v1/videos:lookupVideoMetadata?address=600%20Montgomery%20St%2C%20San%20Francisco%2C%20CA&key=YOUR_KEY"

# Request render if missing
curl -X POST -H 'Content-Type: application/json' \
  -d '{"address":"500 W 2nd St, Austin, TX 78701"}' \
  "https://aerialview.googleapis.com/v1/videos:renderVideo?key=YOUR_KEY"
```

---

## 2. Photorealistic 3D Tiles (Map Tiles API)

**What you get:** OGC 3D Tiles (textured meshes) of populated areas — buildings, monuments, terrain — the data behind Earth-like 3D views.

Docs:

- [3D Tiles overview](https://developers.google.com/maps/documentation/tile/3d-tiles-overview)  
- [Getting tiles](https://developers.google.com/maps/documentation/tile/3d-tiles)  
- [Use a renderer](https://developers.google.com/maps/documentation/tile/use-renderer)

**API:** Root tileset URL → CesiumJS / deck.gl / Unreal / Unity / custom renderer:

`https://tile.googleapis.com/v1/3dtiles/root.json?key=YOUR_API_KEY`

**Video?** Not returned as MP4. You fly a camera in a renderer and **record frames yourself**. ToS/policies restrict offline bulk caching; attribution required.

**Best fit:** Custom interactive 3D, or DIY flyover pipelines (heavier than Aerial View).

---

## 3. Maps JavaScript API — 3D Maps (`Map3DElement`)

**What you get:** Browser photorealistic 3D map component (camera, tilt, range, heading) without running your own tiles renderer.

Docs:

- [3D Maps overview](https://developers.google.com/maps/documentation/javascript/3d-maps-overview)  
- [`Map3DElement` reference](https://developers.google.com/maps/documentation/javascript/reference/3d-map)

**API:** Client-side JS library (`maps3d`), not a “give me an MP4” endpoint. Exporting video would mean screen-capture / MediaRecorder on your side (ToS caution).

**Best fit:** Embed live 3D building context in a web UI.

---

## 4. Google Earth Studio

**What you get:** Browser animation tool over Google Earth satellite / 3D imagery — orbits, fly-tos, keyframes; local image-sequence render or experimental **cloud MP4** render.

Docs:

- [Earth Studio](https://www.google.com/earth/studio/)  
- [Rendering](https://earth.google.com/studio/docs/making-animations/rendering/)  
- [Cloud rendering](https://earth.google.com/studio/docs/making-animations/cloud-rendering/)

**API?** **No public programmatic API.** Manual Chrome UI; access request via Google account. Cloud render: experimental, ~18k frames/day quota, downloads expire in 10 days.

**Best fit:** One-off marketing / editorial flyovers you control as files — not an agent loop.

---

## 5. Street View Static API

**What you get:** **Still** street-level panorama crop (often building facade) via HTTP GET.

Docs: [Street View Static overview](https://developers.google.com/maps/documentation/streetview/overview)

```
https://maps.googleapis.com/maps/api/streetview?size=600x400&location=ADDRESS_OR_LATLNG&key=YOUR_KEY
```

**Not video.** Interactive panoramas via Maps JS Street View service. Coverage gaps common off main roads.

---

## 6. Google Earth Engine (you already have this)

**What you get:** `Export.video.toDrive` / `toCloudStorage` turns an **ImageCollection** (Landsat, Sentinel-2, NAIP, …) into an **MP4 time-series** over a region.

Docs: [Exporting video](https://developers.google.com/earth-engine/guides/exporting_video)

**What you do *not* get:**

- Google Earth **photorealistic 3D building meshes**  
- Facade-level “drone orbit” of one parcel  
- Earth Studio / Aerial View imagery through the EE catalog  

**Resolution reality:** Sentinel-2 ~10 m, Landsat ~30 m — city blocks, not building facades. NAIP ~0.6–1 m shows **rooftops / footprints** as aerial stills/epochs, still not Earth 3D video.

**Best fit:** “How did this site change over years?” — complementary to Mireye diligence, wrong tool for “show me the building.”

---

## 7. Deprecated / non-paths

- **Google Earth API / Earth Plug-in** — retired; do not plan on it.  
- **Earth Engine ≠ Google Earth 3D** for this use case — shared branding, different stacks.  
- Scraping Earth / Earth Studio UI — violates ToS; use Maps Platform APIs instead.

---

## Recommended path (GCP + EE on hand)

1. **Primary (building video):** Enable **Aerial View API** on the same GCP billing project → `lookupVideoMetadata` → `lookupVideo` or `renderVideo`. Embed playback URIs; persist only `videoId`.  
2. **Interactive 3D:** **Map Tiles Photorealistic 3D** or **Maps JS 3D**.  
3. **Facade still:** Street View Static.  
4. **Change-over-time science:** keep **Earth Engine** `Export.video` / reducers — do not expect building cinema from EE.

**Minimal agent flow for a US address:**

```
address → Aerial View lookupVideoMetadata
  → ACTIVE? lookupVideo → embed URIs
  → 404 in supported area? renderVideo → poll → lookupVideo
  → optional: Street View Static still as fallback thumbnail
  → optional: EE NDVI/change clip for diligence (separate product)
```

---

## Practical gotchas

- Aerial View and 3D Tiles need **Maps Platform billing**, not just EE access.  
- Aerial View videos are **stream/embed**, not your asset library.  
- Coverage is incomplete; always check metadata before promising a video in product UX.  
- Earth Studio remains the only first-party path that hands you a **downloadable** Earth-style MP4 — and it is not API-driven.
