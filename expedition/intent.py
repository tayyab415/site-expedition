"""Natural-language Mission Plan proposal.

The model may propose. ``plan.py`` still compiles. Invalid fields are dropped.
Labor preferences are stripped for Home before compile. Deterministic parsing
always runs so replay and tests do not need a live model.
"""

from __future__ import annotations

import json
import re

from expedition.plan import (
    PREFERENCE_WEIGHTS,
    SEARCH_REGIONS,
    SITE_FORMS,
    compile_plan,
)
from expedition.regions import default_search_region, expand_allowlist, load_catalog


MISSION_HINTS = (
    (
        "data_center",
        (
            "data center",
            "data hall",
            "data-center",
            "data centre",
            "datacenter",
            "datacentre",
            "server farm",
            "server farms",
            "colocation",
            "colo",
            "gpu cluster",
            "hyperscale",
        ),
    ),
    (
        "warehouse",
        (
            "warehouse",
            "logistics",
            "distribution",
            "fulfillment",
            "industrial park",
            "light industrial",
        ),
    ),
    (
        "farm",
        (
            "farmland",
            "farming",
            "farm",
            "acreage",
            "ranch",
            "vineyard",
            "orchard",
            "plantation",
            "plantations",
            "greenhouse",
            "pasture",
            "cattle",
            "livestock",
            "hayfield",
            "hayfields",
            "hay",
            "rice",
            "corn",
            "maize",
            "soybean",
            "soybeans",
            "wheat",
            "cotton",
            "crop",
            "crops",
            "cultivat",
            "tillable",
            "agriculture",
            "agricultural",
            "horticult",
            "vegetable",
            "vegetables",
            "oranges",
            "orange grove",
            "citrus",
            "lemons",
            "grapefruit",
            "avocados",
            "apples",
            "berries",
            "peanuts",
            "sugarcane",
            "grapes",
            "vines",
            "winery",
            "chicken",
            "chickens",
            "poultry",
            "hogs",
            "pigs",
            "dairy",
            "goats",
            "sheep",
        ),
    ),
    (
        "home",
        (
            "home",
            "house",
            "housing",
            "residential",
            "a place to live",
            "lot to live",
            "homestead",
            "cabin",
        ),
    ),
)

MISSION_PREFERENCES = {
    "warehouse": frozenset(
        {"major_road_access", "route_time", "rail_access", "grid_proximity"}
    ),
    "farm": frozenset({"soil_water_capacity", "drought_context", "road_access"}),
    "home": frozenset({"hospital_access", "lower_slope", "lower_wildfire"}),
    "data_center": frozenset({"grid_proximity", "fiber_context", "lower_heat"}),
    "custom": frozenset(),
}

SIZE_BANDS = frozenset(
    {
        "flexible",
        "under_100k_sqft",
        "100k_250k_sqft",
        "250k_500k_sqft",
        "500k_plus_sqft",
        "under_100_acres",
        "100_500_acres",
        "500_2000_acres",
        "2000_plus_acres",
        "under_1500_sqft",
        "1500_2500_sqft",
        "2500_4000_sqft",
        "4000_plus_sqft",
        "under_20_acres",
        "20_50_acres",
        "50_150_acres",
        "150_plus_acres",
    }
)

PASTURE_HINTS = (
    "cattle",
    "ranch",
    "pasture",
    "grazing",
    "livestock",
    "run cattle",
    "chicken",
    "chickens",
    "poultry",
    "hens",
    "broiler",
    "hogs",
    "pigs",
    "dairy",
    "goats",
    "sheep",
    # Not CDL cropland either: aquaculture and silviculture.
    "fish farm",
    "aquaculture",
    "hatchery",
    "tree farm",
    "timber",
    "forestry",
    "christmas tree",
)

REGION_HINTS = (
    ("dallas_fort_worth", ("dallas", "fort worth", "dfw", "arlington, tx", "alliance")),
    ("houston_metro", ("houston", "galveston", "katy", "the woodlands", "pasadena, tx")),
    ("austin_san_antonio", ("austin", "san antonio", "san marcos", "hill country")),
    ("chicago", ("chicago", "joliet", "cook county")),
    ("atlanta", ("atlanta", "fulton")),
    ("phoenix", ("phoenix", "mesa, az", "maricopa", "arizona")),
    ("denver", ("denver", "aurora, co")),
    ("seattle", ("seattle", "king county", "tacoma")),
    ("los_angeles", ("los angeles", "la county", "inland empire", "long beach")),
    ("new_york", ("new york", "nyc", "manhattan", "newark")),
    ("miami", ("miami", "miami-dade", "doral")),
)

STATE_HINTS = (
    ("TX", ("texas", " tx", "tx ", "lone star")),
    ("IL", ("illinois",)),
    ("GA", ("georgia",)),
    ("AZ", ("arizona",)),
    ("CO", ("colorado",)),
    ("WA", ("washington state", "washington,")),
    ("CA", ("california",)),
    ("NY", ("new york state",)),
    ("FL", ("florida",)),
)

PREFERENCE_HINTS = {
    "major_road_access": ("highway", "interstate", "major road", "freeway", "road access"),
    "rail_access": ("rail", "railroad", "siding"),
    "grid_proximity": ("grid", "substation", "power", "transmission"),
    "route_time": ("drive time", "route time", "to the port", "customer pin"),
    "soil_water_capacity": (
        "soil water",
        "available-water",
        "available water",
        "water availability",
        "awc",
        "irrigation",
        "soil moisture",
    ),
    "drought_context": (
        "drought",
        "arid",
        "dry weather",
        "dry summers",
        "dry climate",
        "desert",
        "hot and dry",
        "dry conditions",
    ),
    "road_access": ("road access", "highway"),
    "hospital_access": ("hospital",),
    "lower_slope": ("flat", "lower slope", "not steep"),
    "lower_wildfire": ("wildfire", "fire risk"),
    "fiber_context": ("fiber",),
    "lower_heat": ("heat", "hot summers", "cooling"),
}

FLOOD_REJECT = (
    "no flood",
    "not in a flood",
    "floodplain is a hard",
    "flood intolerant",
    "avoid flood",
    "out of flood",
)
FLOOD_ALLOW = (
    "flood ok",
    "flood is fine",
    "flood allowed",
    "flood irrigation",
    "flooded rice",
)

WATERFRONT_HINTS = (
    "riverfront",
    "river front",
    "waterfront",
    "on the river",
    "creekside",
    "bayou",
    "on the water",
)

SUPPORTED_MISSION_NOTE = (
    "This agent screens four missions: home, farm (agriculture), "
    "warehouse, and data center."
)

# "solar farm" and "wind farm" would match the farm hints, so energy terms
# are checked before missions. Refusing beats screening soil for a substation.
ENERGY_HINTS = (
    "solar farm",
    "solar farms",
    "solar field",
    "solar plant",
    "solar project",
    "wind farm",
    "wind farms",
    "wind turbine",
    "wind turbines",
    "battery storage",
    "power plant",
)

# Facilities that contain a mission word ("home", "house") but are commercial
# operations, so they must be caught before the mission scan.
FACILITY_HINTS = (
    "retirement home",
    "nursing home",
    "assisted living",
    "care home",
    "group home",
    "funeral home",
    "mobile home park",
    "trailer park",
    "rv park",
    "halfway house",
    "steakhouse",
    "steak house",
)

# Uses with no honest screening recipe. A cafe seeker must get a refusal,
# not warehouse pins. Checked only when no supported mission term matched.
UNSUPPORTED_HINTS = (
    "cafe",
    "coffee shop",
    "coffeehouse",
    "restaurant",
    "bakery",
    "food truck",
    "bar",
    "brewery",
    "hotel",
    "motel",
    "resort",
    "airbnb",
    "gym",
    "fitness studio",
    "yoga studio",
    "salon",
    "spa",
    "retail",
    "storefront",
    "boutique",
    "shopping center",
    "strip mall",
    "mall",
    "office",
    "offices",
    "coworking",
    "clinic",
    "pharmacy",
    "school",
    "daycare",
    "church",
    "apartment",
    "apartments",
    "multifamily",
    "condo",
    "condos",
    "self storage",
    "car wash",
    "gas station",
    "dealership",
    "laundromat",
)

CROP_HINTS = {
    "cotton": ("cotton",),
    "citrus": (
        "citrus",
        "oranges",
        "orange grove",
        "grapefruit",
        "lemons",
        "lemon grove",
        "tangerine",
    ),
    "rice": ("rice",),
    "corn": ("corn", "maize"),
    "soy": ("soy", "soybean", "soybeans"),
    "wheat": ("wheat",),
    "grapes": ("vineyard", "vineyards", "wine grapes", "winery"),
    "apples": ("apples", "apple orchard"),
    "peanuts": ("peanut", "peanuts"),
    "sugarcane": ("sugarcane", "sugar cane"),
    "avocado": ("avocado", "avocados"),
    # No belt in any covered metro. US production is essentially Hawaii and
    # Puerto Rico. Detected so the triage says so instead of shrugging.
    "coffee": ("coffee",),
    "cacao": ("cacao", "cocoa"),
    "banana": ("banana", "bananas"),
    "pineapple": ("pineapple", "pineapples"),
    "tea": ("tea plantation", "tea farm", "tea estate"),
    "mango": ("mango", "mangoes"),
}

# Coarse USDA cropland-pattern belts restricted to covered metros. A miss
# only warns and defers to the farm-history witness. It never vetoes.
CROP_REGIONS = {
    "cotton": (
        "dallas_fort_worth",
        "houston_metro",
        "austin_san_antonio",
        "phoenix",
        "atlanta",
        "los_angeles",
    ),
    "citrus": ("miami", "phoenix", "los_angeles"),
    "rice": ("houston_metro",),
    "corn": ("chicago", "dallas_fort_worth", "denver", "atlanta"),
    "soy": ("chicago", "atlanta"),
    "wheat": ("denver", "dallas_fort_worth", "seattle"),
    "grapes": ("los_angeles", "seattle", "austin_san_antonio", "new_york"),
    "apples": ("seattle", "new_york"),
    "peanuts": ("atlanta",),
    "sugarcane": ("miami", "houston_metro"),
    "avocado": ("los_angeles", "miami"),
    "coffee": (),
    "cacao": (),
    "banana": (),
    "pineapple": (),
    "tea": (),
    "mango": ("miami",),
}

# US states with no locate coverage, for honest geography notes.
UNCOVERED_STATE_HINTS = (
    "alabama", "alaska", "arkansas", "connecticut", "delaware", "hawaii",
    "idaho", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "utah", "vermont", "virginia",
    "west virginia", "wisconsin", "wyoming",
)

NON_US_HINTS = (
    "toronto", "vancouver", "montreal", "canada", "canadian", "mexico city",
    "london", "paris", "berlin", "europe", "tokyo", "japan", "dubai",
    "australia", "sydney", "brazil", "sao paulo", "india",
)

INTENT_PROMPT = """You propose a Site Expedition Mission Plan. You do not decide verdicts.
Return JSON only:
{"mission":"warehouse"|"farm"|"home"|"data_center",
 "search_region": one of the known region ids or null,
 "region_allowlist": [region ids],
 "flood_intolerant": true|false,
 "require_cultivated": true|false,
 "size_band": string,
 "site_form":"either"|"existing_asset"|"developable_land",
 "preferences":[{"id":"drought_context","weight":"priority"}],
 "rationale":["one line each"]}
Known metros: houston_metro, austin_san_antonio, dallas_fort_worth, chicago, atlanta, phoenix, denver, seattle, los_angeles, new_york, miami. texas_triangle expands to the three Texas metros.
Farm size bands: flexible, under_100_acres, 100_500_acres, 500_2000_acres, 2000_plus_acres.
Farm preferences: soil_water_capacity, drought_context, road_access.
Warehouse preferences: major_road_access, route_time, rail_access, grid_proximity.
Home preferences: hospital_access, lower_slope, lower_wildfire. Never labor.
Data center preferences: grid_proximity, fiber_context, lower_heat.
Rules:
US only. Do not invent listings or metros. Unknown geography means region_allowlist [].
Crop, plantation, vineyard, orchard, greenhouse, ranch, acreage, hay, corn, soy, cattle means farm, not warehouse.
Warehouse wins only when the user is siting logistics or industrial, including warehouse next to a farm.
Farm flood_intolerant defaults false unless they reject flood. Rice or flood irrigation is not a flood veto.
Farm water availability is soil_water_capacity. Never a water right. Never must_have_water_service.
Dry, arid, or drought means drought_context. Cattle, ranch, or pasture means require_cultivated false.
Do not use demographic desirability. Do not include labor preferences for home.
"""


def _normalize(text: str) -> str:
    return f" {re.sub(r'\s+', ' ', (text or '').strip().lower())} "


def _hint_pattern(hint: str) -> str:
    if " " in hint or "-" in hint:
        return re.escape(hint)
    if hint.endswith(("ing", "land")) or len(hint) >= 8:
        return rf"(?<![a-z0-9]){re.escape(hint)}"
    return rf"(?<![a-z0-9]){re.escape(hint)}(?![a-z0-9])"


def _mentions(blob: str, hints: tuple[str, ...] | list[str]) -> bool:
    for hint in hints:
        if hint and re.search(_hint_pattern(hint), blob):
            return True
    return False


NEGATION_WINDOW = re.compile(
    r"(?:\bno\b|\bnot\b|\bwithout\b|\bavoid(?:ing)?\b|\bskip\b|\bexcept\b"
    r"|\bdon'?t\s+(?:need|want)\b)\s+(?:[a-z0-9']+\s+){0,2}$"
)


def _mentions_affirmed(blob: str, hints: tuple[str, ...] | list[str]) -> bool:
    """True when a hint appears without a negation just before it.

    'no rail needed' must not set a rail preference; 'not in Texas' must
    not select the Texas metros.
    """
    for hint in hints:
        if not hint:
            continue
        for match in re.finditer(_hint_pattern(hint), blob):
            if not NEGATION_WINDOW.search(blob[: match.start()]):
                return True
    return False


def _pick_mission(blob: str) -> str:
    for mission, hints in MISSION_HINTS:
        if _mentions(blob, hints):
            return mission
    return "warehouse"


def detect_unsupported(text: str) -> dict | None:
    """Return a refusal payload when the stated use has no honest recipe."""
    blob = _normalize(text)
    for hint in ENERGY_HINTS:
        if _mentions(blob, (hint,)):
            return {
                "term": hint,
                "message": (
                    f"A {hint} is an energy site, not cultivated farmland. "
                    + SUPPORTED_MISSION_NOTE
                ),
            }
    for hint in FACILITY_HINTS:
        if _mentions(blob, (hint,)):
            return {
                "term": hint,
                "message": (
                    f"A {hint} is a commercial facility, not a single home "
                    "purchase. " + SUPPORTED_MISSION_NOTE
                ),
            }
    for _, hints in MISSION_HINTS:
        if _mentions(blob, hints):
            return None
    for hint in UNSUPPORTED_HINTS:
        if _mentions(blob, (hint,)):
            return {
                "term": hint,
                "message": (
                    f"'{hint}' is not a use this agent can screen honestly. "
                    + SUPPORTED_MISSION_NOTE
                ),
            }
    return None


def _pick_crop(blob: str) -> str | None:
    for crop, hints in CROP_HINTS.items():
        if _mentions(blob, hints):
            return crop
    return None


def _geography_note(blob: str) -> str | None:
    for hint in NON_US_HINTS:
        if _mentions(blob, (hint,)):
            return f"{hint.title()} is outside the US. This agent is US-only."
    for state in UNCOVERED_STATE_HINTS:
        if _mentions(blob, (state,)):
            return (
                f"{state.title()} has no locate coverage yet, "
                "so covered metros stand in."
            )
    return None


def _pick_regions(blob: str, catalog: dict) -> list[str]:
    named = []
    seen: set[str] = set()
    for region_id, hints in REGION_HINTS:
        if _mentions_affirmed(blob, hints) and region_id not in seen:
            seen.add(region_id)
            named.append(region_id)
    if named:
        return named
    for state, hints in STATE_HINTS:
        if _mentions_affirmed(blob, hints):
            return list(catalog["state_regions"].get(state) or [])
    return []


def _pick_flood(blob: str, mission: str) -> bool:
    if _mentions(blob, FLOOD_ALLOW):
        return False
    if _mentions(blob, FLOOD_REJECT):
        return True
    return mission in {"warehouse", "home", "data_center"}


def _pick_site_form(blob: str) -> str:
    if "existing" in blob or "built asset" in blob:
        return "existing_asset"
    if "developable" in blob or "vacant land" in blob or "greenfield" in blob:
        return "developable_land"
    return "either"


def _pick_require_cultivated(blob: str, mission: str) -> bool:
    if mission != "farm":
        return False
    if _mentions(blob, PASTURE_HINTS):
        return False
    return True


SIZE_QUALIFIER = re.compile(r"(?:under|less than|up to|at most|below|within)\s+$")


def _qualified(blob: str, start: int, value: float) -> float:
    """'under 2500 sqft' belongs in the band below the stated number."""
    return value - 1 if SIZE_QUALIFIER.search(blob[:start]) else value


def _acres(blob: str) -> float | None:
    if re.search(r"\bhalf[- ]acre\b|\bhalf an acre\b", blob):
        return 0.5
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*-?\s*acres?\b", blob)
    if not match:
        return None
    return _qualified(blob, match.start(), float(match.group(1).replace(",", "")))


def _pick_size_band(blob: str, mission: str) -> str:
    acres = _acres(blob)
    if mission == "farm":
        if acres is not None:
            if acres < 100:
                return "under_100_acres"
            if acres < 500:
                return "100_500_acres"
            if acres < 2000:
                return "500_2000_acres"
            return "2000_plus_acres"
        if _mentions(blob, ("small farm", "hobby farm", "small acreage")):
            return "under_100_acres"
        if _mentions(blob, ("big farm", "large farm", "large-scale farm", "commercial farm")):
            return "500_2000_acres"
        if _mentions(blob, ("very large farm", "thousands of acres")):
            return "2000_plus_acres"
    if mission == "warehouse":
        sqft = _sqft(blob)
        if sqft is not None:
            if sqft < 100_000:
                return "under_100k_sqft"
            if sqft < 250_000:
                return "100k_250k_sqft"
            if sqft < 500_000:
                return "250k_500k_sqft"
            return "500k_plus_sqft"
    if mission == "home":
        if acres is not None:
            if acres < 20:
                return "under_20_acres"
            if acres < 50:
                return "20_50_acres"
            if acres < 150:
                return "50_150_acres"
            return "150_plus_acres"
        sqft = _sqft(blob)
        if sqft is not None:
            if sqft < 1500:
                return "under_1500_sqft"
            if sqft < 2500:
                return "1500_2500_sqft"
            if sqft < 4000:
                return "2500_4000_sqft"
            return "4000_plus_sqft"
    return "flexible"


def _sqft(blob: str) -> float | None:
    """Read '80k sq ft', '80,000 square feet', '3 million sq ft', '80000 sf',
    or bare '80k'."""
    match = re.search(
        r"(\d[\d,]*(?:\.\d+)?)\s*(million|m|k)?\s*"
        r"(?:sq\.?\s*(?:ft|feet)|square\s+(?:feet|foot)|sqft|sf)\b",
        blob,
    )
    if match:
        value = float(match.group(1).replace(",", ""))
        unit = match.group(2) or ""
        if unit == "k":
            value *= 1000
        elif unit:
            value *= 1_000_000
        return _qualified(blob, match.start(), value)
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*k\b", blob)
    if match:
        value = float(match.group(1).replace(",", "")) * 1000
        return _qualified(blob, match.start(), value)
    return None


def _pick_preferences(blob: str, mission: str) -> list[dict]:
    allowed = MISSION_PREFERENCES.get(mission) or frozenset()
    found = []
    seen: set[str] = set()
    for preference_id, hints in PREFERENCE_HINTS.items():
        if preference_id not in allowed:
            continue
        if _mentions_affirmed(blob, hints) and preference_id not in seen:
            seen.add(preference_id)
            found.append({"id": preference_id, "weight": "priority"})
    if mission == "home":
        found = [row for row in found if row["id"] not in {"labor_access", "labor"}]
    return found


def parse_intent(text: str) -> dict:
    blob = _normalize(text)
    catalog = load_catalog()
    mission = _pick_mission(blob)
    allowlist = _pick_regions(blob, catalog)
    flood_intolerant = _pick_flood(blob, mission)
    site_form = _pick_site_form(blob)
    preferences = _pick_preferences(blob, mission)
    size_band = _pick_size_band(blob, mission)
    require_cultivated = _pick_require_cultivated(blob, mission)
    crop = _pick_crop(blob) if mission == "farm" else None
    geography_note = _geography_note(blob)
    crop_note = None
    if crop:
        belt = list(CROP_REGIONS.get(crop) or ())
        if not belt:
            crop_note = (
                f"No covered metro is a typical {crop} region in USDA "
                "cropland patterns — US production is essentially Hawaii "
                "and Puerto Rico. Treat any candidate as speculative for "
                "this crop."
            )
        elif not allowlist and belt:
            allowlist = belt
            crop_note = (
                f"No covered metro named, so the {crop} belt among covered "
                "metros stands in: " + ", ".join(belt) + "."
            )
        elif allowlist and belt and not (set(allowlist) & set(belt)):
            crop_note = (
                f"{crop.title()} is not a typical crop near "
                + ", ".join(allowlist)
                + " in USDA cropland patterns. The farm-history witness "
                "checks what actually grows there."
            )
    search_region = default_search_region(allowlist)
    rationale = [
        f"Mission {mission.replace('_', ' ')} from the stated use.",
    ]
    if allowlist:
        rationale.append(
            "Geography limited to " + ", ".join(allowlist) + "."
        )
    else:
        rationale.append("No metro named, so every locate metro is a candidate.")
    if geography_note:
        rationale.append(geography_note)
    if crop_note:
        rationale.append(crop_note)
    if flood_intolerant and _mentions(blob, WATERFRONT_HINTS):
        rationale.append(
            "Waterfront and a flood veto usually conflict; expect floodplain rejects."
        )
    rationale.append(
        "Mapped floodplain is a hard no."
        if flood_intolerant
        else "Mapped floodplain is not a hard no."
    )
    if size_band != "flexible":
        rationale.append(f"Size band {size_band.replace('_', ' ')}.")
    if mission == "farm" and not require_cultivated:
        rationale.append("Pasture/ranch: cultivated CDL is not required.")
    for row in preferences:
        rationale.append(f"{row['id'].replace('_', ' ')} set to {row['weight']}.")
    if mission == "home":
        rationale.append("Home ranking ignores labor and demographic facts.")
    if mission == "farm" and any(row["id"] == "soil_water_capacity" for row in preferences):
        rationale.append("Soil water is AWC context, not a water right.")
    return {
        "mission": mission,
        "crop": crop,
        "search_region": search_region,
        "region_allowlist": allowlist,
        "flood_intolerant": flood_intolerant,
        "require_cultivated": require_cultivated,
        "require_water_service": False,
        "site_form": site_form,
        "preferences": preferences,
        "size_band": size_band,
        "budget_band": "flexible",
        "scan_budget": "standard",
        "geography_band": "selected_region",
        "rationale": rationale,
        "source": "deterministic",
    }


def _validate_model_payload(raw: dict, fallback: dict) -> dict:
    out = dict(fallback)
    prior_mission = fallback.get("mission")
    mission = str(raw.get("mission") or fallback["mission"]).replace(" ", "_").lower()
    if mission in {"warehouse", "farm", "home", "data_center"}:
        out["mission"] = mission
    if out["mission"] != prior_mission and "flood_intolerant" not in raw:
        out["flood_intolerant"] = out["mission"] in {"warehouse", "home", "data_center"}
    if out["mission"] != prior_mission and "require_cultivated" not in raw:
        out["require_cultivated"] = out["mission"] == "farm"
    region = raw.get("search_region")
    if isinstance(region, str) and region in SEARCH_REGIONS:
        out["search_region"] = region
    allow = raw.get("region_allowlist")
    inventory = set(load_catalog()["locate_inventory"])
    if isinstance(allow, list):
        cleaned = [
            item
            for item in allow
            if isinstance(item, str) and (item in inventory or item in SEARCH_REGIONS)
        ]
        named = [item for item in cleaned if item != "texas_triangle"]
        if named:
            out["region_allowlist"] = named
        elif any(item == "texas_triangle" for item in cleaned):
            out["region_allowlist"] = expand_allowlist(["texas_triangle"])
        elif not cleaned and not fallback.get("region_allowlist"):
            out["region_allowlist"] = []
    if isinstance(raw.get("flood_intolerant"), bool):
        out["flood_intolerant"] = raw["flood_intolerant"]
    if isinstance(raw.get("require_cultivated"), bool):
        out["require_cultivated"] = raw["require_cultivated"]
    if isinstance(raw.get("require_water_service"), bool):
        out["require_water_service"] = raw["require_water_service"]
        if out["mission"] == "farm":
            out["require_water_service"] = False
    size_band = raw.get("size_band")
    if isinstance(size_band, str) and size_band in SIZE_BANDS:
        out["size_band"] = size_band
    site_form = raw.get("site_form")
    if site_form in SITE_FORMS:
        out["site_form"] = site_form
    prefs = raw.get("preferences")
    allowed = MISSION_PREFERENCES.get(out["mission"]) or frozenset()
    if isinstance(prefs, list):
        cleaned_prefs = []
        seen: set[str] = set()
        for row in prefs:
            if not isinstance(row, dict):
                continue
            pid = row.get("id")
            weight = row.get("weight")
            if not isinstance(pid, str) or weight not in PREFERENCE_WEIGHTS or pid in seen:
                continue
            if allowed and pid not in allowed:
                continue
            seen.add(pid)
            cleaned_prefs.append({"id": pid, "weight": weight})
        out["preferences"] = cleaned_prefs
    if out["mission"] == "home":
        out["preferences"] = [
            row for row in out["preferences"] if row["id"] not in {"labor_access", "labor"}
        ]
        out["require_cultivated"] = False
    rationale = raw.get("rationale")
    if isinstance(rationale, list):
        notes = [str(item).strip() for item in rationale if str(item).strip()]
        if notes:
            out["rationale"] = notes[:8]
    out["source"] = "model"
    return out


def _complete_intent(text: str) -> dict:
    from expedition.adapters.model import complete

    return complete(INTENT_PROMPT + "\nUser:\n" + text[:2000], prefer="luna")


def propose_intent(text: str, *, live_model: bool = False) -> dict:
    """Map free text to a compiled Mission Plan plus a region allowlist."""
    text = (text or "").strip()
    if not text:
        raise ValueError("intent text is required")
    if len(text) > 4000:
        raise ValueError("intent text is too long")
    blocked = detect_unsupported(text)
    if blocked:
        return {
            "ok": False,
            "error": "unsupported_use",
            "term": blocked["term"],
            "message": blocked["message"],
            "supported": ["home", "farm", "warehouse", "data_center"],
        }
    proposed = parse_intent(text)
    if live_model:
        try:
            result = _complete_intent(text)
            if result.get("ok") and result.get("text"):
                blob = result["text"]
                start, end = blob.find("{"), blob.rfind("}") + 1
                parsed = json.loads(blob[start:end])
                if isinstance(parsed, dict):
                    proposed = _validate_model_payload(parsed, proposed)
                    proposed["model"] = result.get("model")
                    proposed["provider"] = result.get("provider")
        except Exception:
            proposed["source"] = "deterministic"
    if proposed["mission"] == "home":
        proposed["preferences"] = [
            row for row in proposed["preferences"] if row["id"] not in {"labor_access", "labor"}
        ]
        proposed["require_cultivated"] = False
    allowlist = proposed.get("region_allowlist") or []
    triangle_ok = proposed["search_region"] == "texas_triangle" and set(allowlist) <= set(
        load_catalog()["state_regions"].get("TX") or []
    )
    if allowlist and proposed["search_region"] not in allowlist and not triangle_ok:
        proposed["search_region"] = default_search_region(allowlist)
    plan = compile_plan(
        proposed["mission"],
        scan_budget=proposed.get("scan_budget") or "standard",
        site_form=proposed.get("site_form") or "either",
        flood_intolerant=proposed["flood_intolerant"],
        require_cultivated=proposed.get("require_cultivated"),
        search_region=proposed["search_region"],
        geography_band=proposed.get("geography_band") or "selected_region",
        size_band=proposed.get("size_band") or "flexible",
        budget_band=proposed.get("budget_band") or "flexible",
        preferences=proposed.get("preferences") or [],
        require_water_service=bool(proposed.get("require_water_service")),
    )
    return {
        "ok": True,
        "source": proposed.get("source") or "deterministic",
        "rationale": proposed.get("rationale") or [],
        "controls": {
            "mission": plan.mission,
            "search_region": plan.search_region,
            "geography_band": plan.geography_band,
            "size_band": plan.size_band,
            "budget_band": plan.budget_band,
            "scan_budget": plan.scan_budget,
            "site_form": plan.site_form,
            "flood_intolerant": plan.flood_intolerant,
            "require_cultivated": plan.require_cultivated,
            "require_water_service": plan.require_water_service,
            "preferences": proposed.get("preferences") or [],
            "region_allowlist": allowlist,
        },
        "region_allowlist": allowlist,
        "open_inventory": not bool(allowlist),
        "crop": proposed.get("crop"),
        "plan": plan.to_dict(),
        "model": proposed.get("model"),
        "provider": proposed.get("provider"),
    }
