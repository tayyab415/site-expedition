# Iteration 7 — Eyes (photorealistic 3D × Earth Engine)

The robot **aims** at the dirt (Google Photorealistic 3D Tiles), then **cross-examines** it (Earth Engine witnesses + the Mireye cited record). Verdict still comes from code. Google pixels never enter the packet.

## Look

Full-bleed Cesium scene. Pin flip San Leon (KILL) ↔ Winfield Cove (KEEP). Overlay chips:

| Chip | Source | In the packet? |
|---|---|---|
| **3D mesh** | [Photorealistic 3D Tiles](https://developers.google.com/maps/documentation/tile/3d-tiles) via Map Tiles API | No — context / listing-photo of the marsh |
| **Water 1984–21** | JRC Global Surface Water occurrence | Yes — TIME witness |
| **NAIP aerial** | USDA NAIP 2021–22 (Texas vintage ends 2022) | Yes — public aerial |
| **FABDEM height** | Bare-earth DEM, 0–10 m stretch | Yes — HEIGHT witness |
| **Land change** | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` 2017→2024, `1 − cosine` | Yes — fingerprint moved |

Aerial View MP4s **404** at both pins (and at Texas City / Galveston city names). Downtown Austin `500 W 2nd St` has an ACTIVE 40s orbit — the wrong building. 3D tiles are the Google eye that actually exists on this dirt.

## Run

Needs `GOOGLE_MAPS_API_KEY` (Map Tiles API) in the environment or `~/.config/mireye-challenge-maps.env`. Earth Engine via ADC + project `gen-lang-client-0261050164`.

```bash
# optional: refresh NAIP/JRC/FABDEM stills
.venv-ee/bin/python iteration-7/generate_exhibits.py

.venv-ee/bin/python iteration-7/serve.py
# http://127.0.0.1:8027/
```

## What this is not

A globe product. The 3D scene is layer 1 (eyes). The fights and KEEP/KILL stamp are the product.
