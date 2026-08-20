"""Deterministic Mission Plan compiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


MISSIONS = ("home", "farm", "warehouse", "data_center", "custom")
SCAN_BUDGETS = frozenset({"quick", "standard", "deep"})
SITE_FORMS = frozenset({"either", "existing_asset", "developable_land"})
GEOGRAPHY_BANDS = frozenset({"selected_region", "adjacent_regions", "statewide"})
SEARCH_REGIONS = frozenset({
    "texas_triangle", "houston_metro", "austin_san_antonio", "dallas_fort_worth",
    "chicago", "atlanta", "phoenix", "denver", "seattle", "los_angeles", "new_york", "miami",
})
PREFERENCE_WEIGHTS = frozenset({"not_considered", "useful", "important", "priority"})
OPTIONAL_INVESTIGATIONS = frozenset(
    {
        "flood_rewind",
        "route_reality",
        "scene_context",
        "farm_history",
        "observed_heat",
        "environmental_record",
        "land_change",
        "labor_access",
        "climate_trajectory",
        "source_scout",
    }
)

INVESTIGATION_SKILLS = {
    "flood_rewind": "flood-rewind",
    "route_reality": "route-reality",
    "farm_history": "farm-history",
    "scene_context": "scene-context",
    "observed_heat": "observed-heat",
    "environmental_record": "environmental-record",
    "land_change": "land-change",
    "labor_access": "labor-access",
    "climate_trajectory": "climate-trajectory",
    "source_scout": "source-scout",
}

WAREHOUSE_FIELDS = [
    "elevation",
    "slope_degrees",
    "fema_flood_zone",
    "within_floodplain_polygon",
    "intersects_wetland",
    "coast_distance_m",
    "nearest_major_road_distance_m",
    "nearest_major_road_class",
    "nearest_long_haul_rail_corridor_distance_m",
    "nearest_substation_distance_m",
    "fiber_broadband_available",
    "within_water_service_area",
    "within_sewer_service_area",
    "nearest_hazardous_facility_distance_m",
]

HOME_FIELDS = [
    "elevation",
    "slope_degrees",
    "fema_flood_zone",
    "within_floodplain_polygon",
    "intersects_wetland",
    "coast_distance_m",
    "primary_building_footprint_sqm",
    "nearest_major_road_distance_m",
    "nearest_hospital_distance_m",
    "wildfire_annual_frequency",
    "design_wind_speed_mph",
]

FARM_FIELDS = [
    "elevation",
    "fema_flood_zone",
    "within_floodplain_polygon",
    "is_cultivated",
    "dominant_crop_5y",
    "prime_farmland_classification",
    "soil_drainage_class",
    "soil_available_water_capacity",
    "drought_category",
]

DC_FIELDS = [
    "elevation",
    "fema_flood_zone",
    "within_floodplain_polygon",
    "nearest_substation_distance_m",
    "nearest_substation_max_voltage_kv",
    "substations_within_radius_count",
    "max_transmission_line_voltage_kv_within_radius",
    "electric_utility_service_territory",
    "fiber_provider_count",
    "days_above_32c_annual_count",
    "design_wet_bulb_temperature_0_4pct_degc",
    "nearest_superfund_distance_m",
]

FIELDS = {
    "warehouse": WAREHOUSE_FIELDS,
    "home": HOME_FIELDS,
    "farm": FARM_FIELDS,
    "data_center": DC_FIELDS,
    "custom": WAREHOUSE_FIELDS,
}

SFHA_ZONES = frozenset({"A", "AE", "VE", "AO", "AH", "AR", "A99"})

WAREHOUSE_ROUTE_ANCHORS = [
    {
        "id": "port_houston",
        "name": "Port of Houston",
        "lat": 29.73,
        "lng": -95.12,
    },
    {
        "id": "san_antonio_customer",
        "name": "San Antonio customer pin",
        "lat": 29.424,
        "lng": -98.494,
    },
]


@dataclass
class MissionPlan:
    mission: str
    scan_budget: str
    site_form: str
    flood_intolerant: bool
    require_cultivated: bool
    fields: list[str]
    skills: list[str]
    hard_constraints: list[str]
    gaps_always: list[str]
    preferences: list[str]
    route_anchors: list[dict] = field(default_factory=list)
    manifest_id: str | None = None
    search_region: str = "texas_triangle"
    geography_band: str = "selected_region"
    size_band: str = "flexible"
    budget_band: str = "flexible"
    preference_weights: dict[str, str] = field(default_factory=dict)
    optional_investigations: list[str] = field(default_factory=list)
    require_water_service: bool = False
    require_sewer_service: bool = False
    require_fiber_service: bool = False
    confirmed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def compile_plan(
    mission: str,
    *,
    scan_budget: str = "standard",
    site_form: str = "either",
    flood_intolerant: bool | None = None,
    require_cultivated: bool | None = None,
    route_anchors: list[dict] | None = None,
    manifest_id: str | None = None,
    search_region: str = "texas_triangle",
    geography_band: str = "selected_region",
    size_band: str = "flexible",
    budget_band: str = "flexible",
    preferences: list[dict] | None = None,
    optional_investigations: list[str] | None = None,
    require_water_service: bool = False,
    require_sewer_service: bool = False,
    require_fiber_service: bool = False,
) -> MissionPlan:
    mission = mission.replace(" ", "_").lower()
    if mission not in MISSIONS:
        raise ValueError(f"unknown mission {mission}")
    if scan_budget not in SCAN_BUDGETS:
        raise ValueError(f"unknown Scan Budget {scan_budget}")
    if site_form not in SITE_FORMS:
        raise ValueError(f"unknown Site Form {site_form}")
    if geography_band not in GEOGRAPHY_BANDS:
        raise ValueError(f"unknown geography band {geography_band}")
    if search_region not in SEARCH_REGIONS:
        raise ValueError(f"unknown Search Region {search_region}")
    if not isinstance(size_band, str) or not size_band.strip():
        raise ValueError("size band is required")
    if not isinstance(budget_band, str) or not budget_band.strip():
        raise ValueError("budget band is required")
    preference_weights = _validate_preferences(preferences or [])
    investigations_were_specified = optional_investigations is not None
    investigations = list(dict.fromkeys(optional_investigations or []))
    unknown_investigations = sorted(set(investigations) - OPTIONAL_INVESTIGATIONS)
    if unknown_investigations:
        raise ValueError(f"unreviewed investigations: {', '.join(unknown_investigations)}")
    route_anchors = _validate_route_anchors(route_anchors)
    if flood_intolerant is None:
        flood_intolerant = mission in {"warehouse", "home", "data_center"}
    if require_cultivated is None:
        require_cultivated = mission == "farm"
    if not route_anchors and mission == "warehouse":
        # These are declared logistics questions on the Warehouse Mission Plan,
        # not destinations inferred from a Candidate Site or model output.
        route_anchors = [dict(anchor) for anchor in WAREHOUSE_ROUTE_ANCHORS]

    skills = ["resolve-site", "screen-site-core", "skeptic-review"]
    if flood_intolerant:
        skills.insert(2, "flood-rewind")
    if mission == "farm":
        skills.insert(2, "farm-history")
    if mission in {"warehouse", "data_center"}:
        skills.append("grid-readiness")
    if mission == "warehouse":
        skills.append("environmental-record")
    if route_anchors:
        skills.append("route-reality")
    if mission in {"warehouse", "farm", "data_center"}:
        skills.append("land-change")
    if mission in {"warehouse", "data_center"}:
        skills.append("labor-access")
    if mission in {"warehouse", "farm", "data_center", "home"}:
        skills.append("climate-trajectory")
    if mission != "custom":
        skills.append("source-scout")
    if mission == "home":
        # Housing ranking must never include demographic / labor facts.
        skills = [s for s in skills if s not in {"labor-access"}]

    hard = []
    if flood_intolerant:
        hard.append("not_mapped_sfha")
    if require_cultivated:
        hard.append("must_be_cultivated")
    if require_water_service:
        hard.append("must_have_water_service")
    if require_sewer_service:
        hard.append("must_have_sewer_service")
    if require_fiber_service:
        hard.append("must_have_fiber_service")
    if site_form != "either":
        hard.append(f"site_form:{site_form}")
    if size_band != "flexible":
        hard.append(f"size_band:{size_band}")
    if budget_band != "flexible":
        hard.append(f"budget_band:{budget_band}")
    hard.extend(
        f"route_under_{anchor['max_minutes']:g}m:{anchor['id']}"
        for anchor in route_anchors
        if anchor.get("max_minutes") is not None
    )

    gaps = ["market_availability"]
    if mission in {"warehouse", "data_center"}:
        gaps += ["electrical_capacity", "truck_ingress", "zoning_permission"]
    if mission == "warehouse":
        gaps.append("concept_fit")
    if mission == "farm":
        gaps += ["water_right", "yield"]
    if mission == "data_center":
        gaps += ["enterprise_fiber_redundancy", "water_capacity"]
    if route_anchors:
        gaps.append("route_time")  # filled if Routes succeeds

    plan_fields = list(FIELDS[mission])
    plan_preferences = (
        ["nearest_major_road_class", "route_duration_s"]
        if mission == "warehouse"
        else []
    )
    if mission == "custom":
        from expedition.manifests import load_reviewed_manifest

        manifest = load_reviewed_manifest(manifest_id or "logistics-resilience")
        manifest_id = manifest.manifest_id
        overrides = manifest.plan_overrides()
        skills = overrides["skills"]
        plan_fields = overrides["fields"]
        hard = overrides["hard_constraints"]
        plan_preferences = overrides["preferences"]
        gaps = overrides["gaps_always"]
        flood_intolerant = "not_mapped_sfha" in hard
        require_cultivated = "must_be_cultivated" in hard
        if "route-reality" in skills and not route_anchors:
            route_anchors = [dict(anchor) for anchor in WAREHOUSE_ROUTE_ANCHORS]
    elif investigations_were_specified:
        controllable = set(INVESTIGATION_SKILLS.values())
        skills = [
            skill for skill in skills
            if skill not in controllable
            or next(key for key, value in INVESTIGATION_SKILLS.items() if value == skill) in investigations
        ]
        for investigation, skill in INVESTIGATION_SKILLS.items():
            if investigation not in investigations or skill in skills:
                continue
            if skill == "labor-access" and mission == "home":
                continue
            skills.append(skill)
    if mission == "home":
        skills = [s for s in skills if s not in {"labor-access"}]

    return MissionPlan(
        mission=mission,
        scan_budget=scan_budget,
        site_form=site_form,
        flood_intolerant=flood_intolerant,
        require_cultivated=require_cultivated,
        fields=plan_fields,
        skills=skills,
        hard_constraints=hard,
        gaps_always=gaps,
        preferences=plan_preferences,
        route_anchors=list(route_anchors or []),
        manifest_id=manifest_id,
        search_region=search_region,
        geography_band=geography_band,
        size_band=size_band,
        budget_band=budget_band,
        preference_weights=preference_weights,
        optional_investigations=investigations,
        require_water_service=bool(require_water_service),
        require_sewer_service=bool(require_sewer_service),
        require_fiber_service=bool(require_fiber_service),
        confirmed=True,
    )


def _validate_preferences(rows: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("preferences must be objects")
        preference_id = row.get("id")
        weight = row.get("weight")
        if not isinstance(preference_id, str) or not preference_id.strip():
            raise ValueError("preference id is required")
        if weight not in PREFERENCE_WEIGHTS:
            raise ValueError(f"unknown preference weight {weight}")
        if preference_id in out:
            raise ValueError(f"duplicate preference {preference_id}")
        out[preference_id] = weight
    return out


def _validate_route_anchors(rows: list[dict] | None) -> list[dict]:
    if rows is None:
        return []
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError("route anchors must be a list of at most 8")
    out: list[dict] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("route anchors must be objects")
        anchor_id = str(row.get("id") or f"anchor_{index + 1}")
        name = str(row.get("name") or "").strip()
        try:
            lat, lng = float(row["lat"]), float(row["lng"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("route anchor needs numeric lat/lng") from exc
        if not name or not (18 <= lat <= 72 and -180 <= lng <= -65):
            raise ValueError("route anchor must be named and inside the US envelope")
        if anchor_id in seen:
            raise ValueError(f"duplicate route anchor {anchor_id}")
        seen.add(anchor_id)
        maximum = row.get("max_minutes")
        if maximum is not None:
            maximum = float(maximum)
            if not 1 <= maximum <= 1440:
                raise ValueError("route anchor max_minutes must be 1..1440")
        out.append({"id": anchor_id, "name": name, "lat": lat, "lng": lng, "max_minutes": maximum})
    return out
