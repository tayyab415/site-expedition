"""Property vetting agent — pin in, verdict out.

    .venv-ee/bin/python harness/vet.py --site san_leon
    .venv-ee/bin/python harness/vet.py --name "..." --lat .. --lng .. [--live]

The record (Mireye, cited) is cross-examined by independent witnesses
(Earth Engine). Verdict rules are code, not model vibes:

  TIME_FIGHT    breakpoint exists AND latest freq >= max(3x baseline, +0.05)
                AND observed monthly water >= 1.5x the recorded permanence
  HEIGHT_FIGHT  |FABDEM - recorded elevation| >= 1.0 m
  aggravator    flood zone A/AE/VE + wetland intersect (context, not a fight)

  2+ fights -> KILL   1 fight -> HUMAN   0 -> KEEP
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eyes import mireye_eye, earth_eye  # noqa: E402

HERE = Path(__file__).parent

SITES = {
    "san_leon": {
        "name": "San Leon, TX (Galveston Bay shore)",
        "lat": 29.475732,
        "lng": -94.966533,
    },
    "keep_control": {
        "name": "3605 Winfield Cove, Austin TX",
        "lat": 30.2363775,
        "lng": -97.7807633,
        "slug": "3605_winfield_cove_austin_tx",
    },
}


def judge(record: dict, witness: dict) -> dict:
    fights = []

    w = witness["water"]
    recorded_pct = record["surface_water_permanence_pct"]["value"] or 0.0
    observed_pct = w["latest_freq_2021"] * 100
    baseline = w["baseline_freq_1985_1999"]
    if (
        w["breakpoint_year"] is not None
        and w["latest_freq_2021"] >= max(3 * baseline, baseline + 0.05)
        and observed_pct >= 1.5 * recorded_pct
    ):
        fights.append({
            "fight": "TIME",
            "claim": f"record says water {recorded_pct:.0f}% of the time",
            "witness": (
                f"JRC monthly history: dry {1985}-{w['breakpoint_year'] - 1} "
                f"(baseline {baseline * 100:.2f}% of months), wetting since "
                f"{w['breakpoint_year']}, {observed_pct:.1f}% of months by 2021"
            ),
            "numbers": {
                "recorded_permanence_pct": recorded_pct,
                "observed_2021_pct": round(observed_pct, 1),
                "baseline_pct": round(baseline * 100, 2),
                "breakpoint_year": w["breakpoint_year"],
            },
        })

    h = witness["height"]
    rec_elev = record["elevation_m"]["value"]
    gap = abs(h["fabdem_m"] - rec_elev)
    zone = record["fema_flood_zone"]["value"]
    coast = (record.get("coast_distance_m") or {}).get("value")
    height_counts = rec_elev is not None and (
        rec_elev < 10 or zone in ("A", "AE", "VE", "AO", "AH")
    )
    if gap >= 1.0 and height_counts:
        where = (
            f"this close to the shore ({coast:.0f} m)"
            if isinstance(coast, (int, float)) and coast < 5000
            else f"in flood zone {zone}"
        )
        direction = "lower" if h["fabdem_m"] < rec_elev else "higher"
        fights.append({
            "fight": "HEIGHT",
            "claim": f"record says ground at {rec_elev:.2f} m ({record['elevation_m']['source']})",
            "witness": (
                f"FABDEM says {h['fabdem_m']:.2f} m — {gap:.2f} m {direction}; "
                f"NASADEM says {h['nasadem_m']:.2f} m. Flood-depth math flips "
                f"on a {gap:.1f} m disagreement {where}."
            ),
            "numbers": {
                "record_m": rec_elev,
                "fabdem_m": round(h["fabdem_m"], 2),
                "nasadem_m": round(h["nasadem_m"], 2),
                "gap_m": round(gap, 2),
                "height_gated": True,
            },
        })

    zone = record["fema_flood_zone"]["value"]
    aggravators = []
    if zone in ("A", "AE", "VE") and record["intersects_wetland"]["value"]:
        aggravators.append(
            f"already zone {zone} ({record['fema_flood_zone']['vintage']}) and intersects a mapped wetland"
        )

    verdict = "KILL" if len(fights) >= 2 else ("HUMAN" if fights else "KEEP")
    return {"verdict": verdict, "fights": fights, "aggravators": aggravators}


def sparkline_svg(timeline: list, breakpoint_year) -> str:
    w, h, pad = 740, 120, 4
    n = len(timeline)
    bw = (w - 2 * pad) / n
    top = max(t["water_freq"] for t in timeline) or 1
    bars = []
    for i, t in enumerate(timeline):
        bh = (t["water_freq"] / top) * (h - 30)
        x = pad + i * bw
        red = breakpoint_year and t["year"] >= breakpoint_year
        bars.append(
            f'<rect x="{x:.1f}" y="{h - 20 - bh:.1f}" width="{bw - 1.5:.1f}" '
            f'height="{max(bh, 0.5):.1f}" fill="{"#c0392b" if red else "#7f8c8d"}"/>'
        )
        if t["year"] % 5 == 0:
            bars.append(
                f'<text x="{x:.1f}" y="{h - 6}" font-size="9" fill="#555">{t["year"]}</text>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<text x="{pad}" y="12" font-size="11" fill="#333">share of observed months with standing water '
        f'(JRC GSW monthly history, 60 m buffer)</text>{"".join(bars)}</svg>'
    )


def write_packet(out: Path, site: dict, record: dict, witness: dict, ruling: dict):
    out.mkdir(parents=True, exist_ok=True)
    (out / "verdict.json").write_text(json.dumps(
        {"site": site, "ruling": ruling, "record": record, "witness_summary": {
            "water": {k: v for k, v in witness["water"].items() if k != "timeline"},
            "height": witness["height"],
        }}, indent=2))
    (out / "evidence.json").write_text(json.dumps(witness, indent=2))
    (out / "water_timeline.svg").write_text(
        sparkline_svg(witness["water"]["timeline"], witness["water"]["breakpoint_year"]))

    r, v = record, ruling
    lines = [
        f"# Due-diligence advisory — {site['name']}",
        f"**Verdict: {v['verdict']}**  ·  {date.today().isoformat()}  ·  "
        f"pin {site['lat']:.6f}, {site['lng']:.6f}",
        "",
        "Prepared for the buyer's agent of record. This advisory cross-examines the "
        "official cited record against independent public satellite evidence. It is "
        "not a survey, appraisal, or legal advice.",
        "",
        "## The record (as cited)",
        "| Fact | Value | Source | Vintage |",
        "|---|---|---|---|",
    ]
    for label, key in [
        ("Ground elevation", "elevation_m"),
        ("FEMA flood zone", "fema_flood_zone"),
        ("Intersects wetland", "intersects_wetland"),
        ("Surface-water permanence", "surface_water_permanence_pct"),
        ("Soil drainage", "soil_drainage_class"),
    ]:
        f = r[key]
        val = f["value"]
        if isinstance(val, float):
            val = f"{val:.2f}"
        if f.get("unit"):
            val = f"{val} {f['unit']}"
        lines.append(
            f"| {label} | {val} | [{f['source']}]({f['source_url']}) | {f['vintage'] or '—'} |")
    lines += ["", "## Where the record and the Earth disagree", ""]
    for i, f in enumerate(v["fights"], 1):
        lines += [
            f"### Fight {i}: {f['fight']}",
            f"- **The record claims:** {f['claim']}",
            f"- **The witness says:** {f['witness']}",
            f"- **Numbers:** `{json.dumps(f['numbers'])}`",
            "",
        ]
    if v["aggravators"]:
        lines += ["**Aggravating context:** " + "; ".join(v["aggravators"]), ""]
    lines += [
        "## Evidence",
        "- `water_timeline.svg` — 37-year monthly-water history at the pin "
        "(JRC/GSW1_4/MonthlyHistory, red bars = post-breakpoint years)",
        "- `evidence.json` — full year-by-year values and both elevation models "
        f"({', '.join(witness['height']['datasets'])})",
        "- All record values above carry their federal source and retrieval "
        "timestamp via the Mireye API.",
        "",
        "## Recommendation",
        {
            "KILL": "Advise the client to withdraw. Two independent public witnesses "
                    "contradict the record this parcel would be priced on. If the "
                    "client proceeds regardless, price the contradiction, not the record.",
            "HUMAN": "One material contradiction found — escalate to a licensed "
                     "surveyor/engineer before proceeding.",
            "KEEP": "No material contradiction between the record and the public "
                    "satellite archive at this pin.",
        }[v["verdict"]],
    ]
    (out / ("kill_letter.md" if v["verdict"] == "KILL" else "advisory.md")).write_text(
        "\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=SITES.keys())
    ap.add_argument("--name")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    ap.add_argument("--live", action="store_true",
                    help="spend Mireye credits / recompute EE instead of cache")
    a = ap.parse_args()

    if a.site:
        site = {k: v for k, v in SITES[a.site].items() if k != "slug"}
        slug = SITES[a.site].get("slug", a.site)
    elif a.name and a.lat is not None and a.lng is not None:
        slug = a.name.lower().replace(" ", "_").replace(",", "")[:40]
        site = {"name": a.name, "lat": a.lat, "lng": a.lng}
    else:
        ap.error("--site or (--name --lat --lng)")

    print(f"[1/4] Mireye record for {site['name']} ...")
    record = mireye_eye.record(slug, site["lat"], site["lng"], live=a.live)
    print(f"[2/4] Earth Engine witnesses (time + height) ...")
    witness = earth_eye.witness(slug, site["lat"], site["lng"], live=a.live)
    print(f"[3/4] Judging ...")
    ruling = judge(record, witness)
    out = HERE / "runs" / slug
    print(f"[4/4] Writing packet -> {out}/")
    write_packet(out, site, record, witness, ruling)

    print(f"\nVERDICT: {ruling['verdict']}  ({len(ruling['fights'])} fight(s))")
    for f in ruling["fights"]:
        print(f"  - {f['fight']}: {f['witness']}")


if __name__ == "__main__":
    main()
