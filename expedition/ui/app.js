const TILES = [
  ["warehouse", "Warehouse / light industrial", "Matching places, or a pin you already have."],
  ["farm", "Farm", "Cultivated land. Water right is never inferred."],
  ["home", "Home", "A lot from constraints. No demographic ranking."],
  ["data_center", "Data center", "Grid and heat context. Never a MW claim."],
  ["custom", "Constrained Custom", "One reviewed manifest."],
];

const SIZE_BANDS = {
  warehouse: [
    ["flexible", "Flexible / not supplied"],
    ["under_100k_sqft", "Under 100k sq ft"],
    ["100k_250k_sqft", "100k–250k sq ft"],
    ["250k_500k_sqft", "250k–500k sq ft"],
    ["500k_plus_sqft", "500k+ sq ft"],
  ],
  farm: [
    ["flexible", "Flexible / not supplied"],
    ["under_100_acres", "Under 100 acres"],
    ["100_500_acres", "100–500 acres"],
    ["500_2000_acres", "500–2,000 acres"],
    ["2000_plus_acres", "2,000+ acres"],
  ],
  home: [
    ["flexible", "Flexible / not supplied"],
    ["under_1500_sqft", "Under 1,500 sq ft"],
    ["1500_2500_sqft", "1,500–2,500 sq ft"],
    ["2500_4000_sqft", "2,500–4,000 sq ft"],
    ["4000_plus_sqft", "4,000+ sq ft"],
  ],
  data_center: [
    ["flexible", "Flexible / not supplied"],
    ["under_20_acres", "Under 20 acres"],
    ["20_50_acres", "20–50 acres"],
    ["50_150_acres", "50–150 acres"],
    ["150_plus_acres", "150+ acres"],
  ],
  custom: [["flexible", "Defined by reviewed manifest"]],
};

const PREFERENCE_OPTIONS = {
  warehouse: [
    ["major_road_access", "Major-road access"],
    ["route_time", "Declared-anchor route time"],
    ["rail_access", "Long-haul rail proximity"],
    ["grid_proximity", "Grid proximity (not capacity)"],
  ],
  farm: [
    ["soil_water_capacity", "Soil available-water capacity"],
    ["drought_context", "Lower observed drought burden"],
    ["road_access", "Major-road proximity"],
  ],
  home: [
    ["hospital_access", "Hospital proximity"],
    ["lower_slope", "Lower slope"],
    ["lower_wildfire", "Lower observed wildfire frequency"],
  ],
  data_center: [
    ["grid_proximity", "Grid proximity (not deliverable MW)"],
    ["fiber_context", "Observed fiber-provider context"],
    ["lower_heat", "Lower observed heat burden"],
  ],
  custom: [],
};

const INVESTIGATION_OPTIONS = {
  warehouse: [
    ["flood_rewind", "Flood rewind when material", true],
    ["environmental_record", "EPA ECHO facility record after an environmental hit", true],
    ["route_reality", "Routes to declared anchors", true],
    ["land_change", "Neighborhood built-cover change (INFORM, not scored)", true],
    ["labor_access", "Labor-shed context (never a hiring claim)", true],
    ["source_scout", "Official follow-up sources (not web discovery)", true],
    ["climate_trajectory", "Regional climate scenario range", true],
    ["scene_context", "Aerial / 3D presentation context", true],
  ],
  farm: [
    ["farm_history", "Annual crop and rainfall history", true],
    ["climate_trajectory", "Regional climate scenario range", true],
    ["land_change", "Neighborhood built-cover change (INFORM, not scored)", true],
    ["source_scout", "Official follow-up sources (not web discovery)", true],
    ["flood_rewind", "Flood rewind when material", false],
    ["scene_context", "Aerial / 3D presentation context", true],
  ],
  home: [
    ["flood_rewind", "Flood rewind when material", true],
    ["climate_trajectory", "Regional climate scenario range", true],
    ["source_scout", "Official follow-up sources (not web discovery)", true],
    ["land_change", "Neighborhood built-cover change (INFORM, not scored)", false],
    ["scene_context", "Aerial / 3D presentation context", true],
  ],
  data_center: [
    ["observed_heat", "Observed-heat temporal witness", true],
    ["climate_trajectory", "Regional climate scenario range", true],
    ["land_change", "Neighborhood built-cover change (INFORM, not scored)", true],
    ["labor_access", "Labor-shed context (never a hiring claim)", true],
    ["source_scout", "Official follow-up sources (not web discovery)", true],
    ["flood_rewind", "Flood rewind when material", true],
    ["route_reality", "Routes to declared anchors", false],
    ["scene_context", "Aerial / 3D presentation context", true],
  ],
  custom: [],
};

const DEFAULT_ROUTE_ANCHORS = {
  warehouse: [
    { id: "port_houston", name: "Port of Houston", lat: 29.73, lng: -95.12, max_minutes: null },
    { id: "san_antonio_customer", name: "San Antonio customer pin", lat: 29.424, lng: -98.494, max_minutes: null },
  ],
};

const CAM = {
  warehouse: { heading: 48, pitch: -12, range: 95, height: 6 },
  farm: { heading: 40, pitch: -16, range: 180, height: 8 },
  home: { heading: 205, pitch: -10, range: 48, height: 4 },
  data_center: { heading: 88, pitch: -14, range: 120, height: 8 },
};

const WORKSTREAM_QUESTIONS = {
  identity: "Where is this Candidate Site, exactly?",
  "screen-site-core": "Does present-state evidence veto this site?",
  "environmental-record": "Is there a nearby hazardous-facility record that needs Phase I?",
  "route-reality": "Can this operation reach its declared destinations on real roads?",
  "flood-rewind": "Has flood behavior changed, and do elevation models disagree?",
  "farm-history": "Has this land been cultivated, and what is the crop and rain history?",
  "observed-heat": "How hot has this site actually been in observed summers?",
  "today-scene": "What does the site look like from the air?",
  "land-change": "Has nearby built cover changed in recent years?",
  "labor-access": "What labor-shed context exists without claiming workers are available?",
  "climate-trajectory": "What does a labeled climate scenario say at regional scale?",
  "source-scout": "Which official follow-up sources apply to this evidence?",
  "skeptic-review": "What would disqualify the apparent finalist?",
};

const GAP_QUESTIONS = {
  market_availability: "Is this site actually for sale or lease?",
  electrical_capacity: "Can the utility deliver the power this operation needs?",
  truck_ingress: "Can trucks legally enter and turn on this site?",
  zoning_permission: "Is the intended use allowed here?",
  water_right: "Does a water right exist for this operation?",
  yield: "What yield can this land actually support?",
  enterprise_fiber_redundancy: "Is there carrier-diverse fiber, not just a provider count?",
  water_capacity: "Will a provider serve process water here?",
  route_time: "What is the real road time to the declared anchors?",
  concept_fit: "Does the warehouse concept fit a licensed parcel envelope?",
  "hazards.elevation_disagreement": "Which elevation model is true at this pin?",
  environmental_phase_i: "What does a Phase I ESA say about the nearby facility?",
};

const WAREHOUSE_BANDS = {
  texas_triangle: {
    san_leon: "selected", san_marcos_tx: "selected",
    alliance_tx: "selected", port_houston: "selected",
  },
  houston_metro: {
    san_leon: "selected", port_houston: "selected",
    san_marcos_tx: "adjacent", alliance_tx: "statewide",
  },
  austin_san_antonio: {
    san_marcos_tx: "selected", san_leon: "adjacent",
    port_houston: "adjacent", alliance_tx: "statewide",
  },
  dallas_fort_worth: {
    alliance_tx: "selected", san_marcos_tx: "adjacent",
    san_leon: "statewide", port_houston: "statewide",
  },
};

const SITE_FORM_LABELS = {
  either: "Existing asset or land",
  existing_asset: "Existing built asset",
  developable_land: "Developable land",
};

// Mirrors REGION_HUBS in expedition/adapters/discover.py.
const REGION_HUBS = {
  texas_triangle: [[29.7589, -95.3677], [30.2711, -97.7437], [32.7767, -96.797]],
  houston_metro: [[29.7589, -95.3677]],
  austin_san_antonio: [[30.2711, -97.7437], [29.4241, -98.4936]],
  dallas_fort_worth: [[32.7767, -96.797]],
  chicago: [[41.8756, -87.6244]],
  atlanta: [[33.7488, -84.3883]],
  phoenix: [[33.4484, -112.074]],
  denver: [[39.7392, -104.9903]],
  seattle: [[47.6062, -122.3321]],
  los_angeles: [[34.0522, -118.2437]],
  new_york: [[40.7128, -74.006]],
  miami: [[25.7617, -80.1918]],
};

// 200 km keeps Quincy WA inside a Seattle data-center search; 520 km keeps
// the Iowa corn-belt pin adjacent to Chicago and Elba NY adjacent to New York.
const BAND_RADIUS_KM = { selected_region: 200, adjacent_regions: 520, statewide: 900 };

function hubDistanceKm(lat, lng, region) {
  let best = Infinity;
  for (const [hlat, hlng] of REGION_HUBS[region] || []) {
    const x = ((hlng - lng) * Math.PI / 180) * Math.cos(((hlat + lat) / 2) * Math.PI / 180);
    const y = ((hlat - lat) * Math.PI / 180);
    best = Math.min(best, Math.hypot(x, y) * 6371);
  }
  return best;
}

const REGION_LABELS = {
  texas_triangle: "Texas Triangle",
  houston_metro: "Houston metro",
  austin_san_antonio: "Austin-San Antonio corridor",
  dallas_fort_worth: "Dallas-Fort Worth",
  chicago: "Chicago",
  atlanta: "Atlanta",
  phoenix: "Phoenix",
  denver: "Denver",
  seattle: "Seattle",
  los_angeles: "Los Angeles",
  new_york: "New York",
  miami: "Miami",
};

const MISSION_COPY = {
  warehouse: {
    kicker: "Cited facts · not a listing · not a permit",
    findTitle: "Find warehouse places",
    checkTitle: "Check this warehouse site",
    findLede: "Pick a region. Matching starter places, not listings. Mapped floodplain can veto.",
    checkLede: "Bring an address or pin. We say if it is a good idea. If not, you get other cards.",
    placing: "You're placing a warehouse",
  },
  farm: {
    kicker: "Cited crop facts · water right is never inferred",
    findTitle: "Find farm places",
    checkTitle: "Check this farm site",
    findLede: "Cultivated land is required. We show starter fields that match. A water right stays a gap.",
    checkLede: "Bring a field pin. We say if it is cultivated and what still has to be verified. Bad idea? Other cards.",
    placing: "You're placing a farm",
  },
  home: {
    kicker: "Functional constraints only · no demographic ranking",
    findTitle: "Find home places",
    checkTitle: "Check this home site",
    findLede: "Flood and slope can veto. Labor ranking stays out. Starter lots, not listings.",
    checkLede: "Bring an address. We say if the lot works on the supported gates. If not, other cards.",
    placing: "You're placing a house",
  },
  data_center: {
    kicker: "Grid and heat context · deliverable MW is never claimed",
    findTitle: "Find data-hall places",
    checkTitle: "Check this data-hall site",
    findLede: "Nearby substations are not a capacity letter. Starter pads, not listings.",
    checkLede: "Bring a pad pin. We screen heat and grid context. If it is a bad idea, other cards.",
    placing: "You're placing a data hall",
  },
  custom: {
    kicker: "Reviewed manifest only · no arbitrary tools",
    findTitle: "Find places from a reviewed recipe",
    checkTitle: "Check this site against a reviewed recipe",
    findLede: "Custom Missions pick one reviewed manifest. They cannot install code or discover arbitrary sources.",
    checkLede: "Bring a pin. The reviewed recipe screens it. If it fails, other cards from that recipe.",
    placing: "You're placing from a reviewed manifest",
  },
};

const BEAT_ORDER = ["locate", "scout", "screen", "compare", "sketch"];
const BEAT_TITLES = {
  locate: "Locate",
  scout: "Scout",
  screen: "Screening",
  compare: "Compare",
  sketch: "Sketch",
};

const LOOK_TO_REGION = {
  chicago: "chicago",
  "chicago, il": "chicago",
  "chicago, illinois": "chicago",
  dallas: "dallas_fort_worth",
  "fort worth": "dallas_fort_worth",
  dfw: "dallas_fort_worth",
  houston: "houston_metro",
  austin: "austin_san_antonio",
  "san antonio": "austin_san_antonio",
  atlanta: "atlanta",
  phoenix: "phoenix",
  denver: "denver",
  seattle: "seattle",
  "los angeles": "los_angeles",
  "new york": "new_york",
  nyc: "new_york",
  miami: "miami",
};

let mission = null;
let plan = null;
let catalog = [];
let extras = [];
let missionSites = {};
let config = { has_google_tiles: false };
let viewer = null;
let tileset = null;
let meshContentReady = false;
let meshLoadTimer = null;
let quickMapRender = 0;
let conceptModel = null;
let conceptPlaceToken = 0;
let pinEntities = [];
let padEntities = [];
let selectedId = null;
let packets = {};
let missionComparison = null;
let sceneMode = "aerial";
let customManifests = [];
let planRequest = 0;
let screenedIds = null;
let heldIds = new Set();
let siteOrigin = {};
let waveIds = null;
let keptIds = new Set();
let passedIds = new Set();
let swipeUndo = [];
let swipePhotoId = null;
let swipeFaceToken = 0;
let selectionImageToken = 0;
let swipeDrag = null;
let streetCache = {};
let streetRequests = {};
let aerialCache = {};
let aerialUriCache = {};
let aerialPlayId = null;
let aerialPlayOpts = null;
let aerialRefreshTimer = null;
let aerialRetry = 0;
let aerialRefreshing = false;
let earthLookSeq = 0;
let earthPollTimer = null;
let orbitListener = null;
let streetSpin = null;
let earthSpin = null;
let earthRender = 0;
let layerOn = { site: true, flood: false, power: false, roads: false };
let boardBeat = "place";
let entryPath = "find";
let recommendMode = false;
let clickHandler = null;
let activeChip = null;
let regionAllowlist = [];
let intentOpenGeography = false;
let locatePacket = null;

const REGION_FLY = {
  texas_triangle: [-97.4, 30.9, 520000],
  houston_metro: [-95.37, 29.76, 180000],
  austin_san_antonio: [-97.9, 29.9, 220000],
  dallas_fort_worth: [-96.9, 32.78, 180000],
  chicago: [-87.63, 41.88, 160000],
  atlanta: [-84.39, 33.75, 160000],
  phoenix: [-112.07, 33.45, 160000],
  denver: [-104.99, 39.74, 160000],
  seattle: [-122.33, 47.61, 160000],
  los_angeles: [-118.24, 34.05, 180000],
  new_york: [-74.01, 40.71, 140000],
  miami: [-80.19, 25.76, 140000],
};

const HOMEWORK_GAPS = [
  "market_availability",
  "electrical_capacity",
  "truck_ingress",
  "zoning_permission",
  "concept_fit",
];
let layerEntities = [];

class AuthenticationRequired extends Error {}

function $(id) {
  return document.getElementById(id);
}

function showAuthGate() {
  $("auth-gate").classList.remove("hidden");
  $("auth-token").focus();
}

async function apiFetch(input, init) {
  const response = await fetch(input, init);
  if (response.status === 401) {
    showAuthGate();
    throw new AuthenticationRequired("deployment authentication required");
  }
  return response;
}

async function unlock(event) {
  event.preventDefault();
  const button = $("auth-submit");
  const status = $("auth-status");
  button.disabled = true;
  status.textContent = "Checking token…";
  try {
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: $("auth-token").value }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      status.textContent = result.message || "Access token rejected.";
      return;
    }
    status.textContent = "Unlocked. Loading…";
    window.location.reload();
  } finally {
    button.disabled = false;
  }
}

async function boot() {
  const session = await fetch("/api/session").then((response) => response.json());
  if (!session.authenticated) {
    showAuthGate();
    return;
  }
  const [cands, sites, cfg] = await Promise.all([
    apiFetch("/api/candidates").then((r) => r.json()),
    apiFetch("/api/mission-sites").then((r) => r.json()),
    apiFetch("/api/config").then((r) => r.json()).catch((error) => {
      if (error instanceof AuthenticationRequired) throw error;
      return config;
    }),
  ]);
  catalog = cands.candidates;
  missionSites = sites;
  config = cfg;
  const tiles = $("tiles");
  TILES.forEach(([id, title, blurb]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tile";
    b.innerHTML = `<strong>${title}</strong><small>${blurb}</small>`;
    b.onclick = () => pickMission(id);
    b.dataset.id = id;
    tiles.appendChild(b);
  });
  $("confirm").onclick = confirmPlan;
  if ($("intent-go")) $("intent-go").onclick = readIntent;
  if ($("intent-text")) {
    $("intent-text").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        readIntent();
      }
    });
  }
  $("replan").onclick = () => {
    if (tileset) tileset.show = false;
    if (viewer) viewer.useDefaultRenderLoop = false;
    $("app").classList.add("hidden");
    $("app").classList.remove("sim-view");
    $("app").removeAttribute("data-beat");
    boardBeat = "place";
    if ($("look-switcher")) $("look-switcher").hidden = true;
    if ($("story")) $("story").textContent = "";
    $("onboard").classList.remove("hidden");
    $("confirm").disabled = !plan;
    $("confirm").textContent = entryPath === "check" ? "Is this a good idea?" : "Find geographies";
  };
  $("run-all").onclick = runExpedition;
  $("run-one").onclick = () => selectedId && runOne(selectedId);
  $("add-pin").onclick = addUserSite;
  $("resolve-address").onclick = addAddressSite;
  if ($("keep-site")) $("keep-site").onclick = () => keepSite(selectedId);
  if ($("pass-site")) $("pass-site").onclick = () => passSite(selectedId);
  if ($("undo-swipe")) $("undo-swipe").onclick = undoSwipe;
  if ($("examine-location")) $("examine-location").onclick = examineSelectedLocation;
  bindSwipePointer();
  if ($("entry-find")) $("entry-find").onclick = () => setEntryPath("find");
  if ($("entry-check")) $("entry-check").onclick = () => setEntryPath("check");
  bindHud();
  ["entry-address", "entry-lat", "entry-lng", "look-query"].forEach((id) => {
    if ($(id)) $(id).addEventListener("input", () => {
      if (id === "look-query") syncLookRegion();
      previewPlan();
    });
  });
  document.querySelectorAll("#beat-strip .beat").forEach((btn) => {
    btn.onclick = () => jumpToBeat(btn.dataset.beat);
  });
  $("close-video").onclick = closeAerial;
  $("aerial-video").addEventListener("error", onAerialError);
  $("toggle-rail").onclick = () => $("app").classList.toggle("rail-off");
  $("toggle-deck").onclick = () => $("app").classList.toggle("deck-off");
  $("add-anchor").onclick = () => {
    appendRouteAnchor({ name: "", lat: "", lng: "", max_minutes: null });
  };
  [
    "flood", "cultivated", "water-service", "sewer-service", "fiber-service",
    "scan", "site-form", "search-region", "geography-band", "size-band",
    "budget-band", "manifest-id",
  ].forEach((id) => {
    $(id).onchange = () => {
      if (id === "search-region") {
        regionAllowlist = [$("search-region").value].filter(Boolean);
        intentOpenGeography = false;
      }
      previewPlan();
    };
  });
  const conceptOk = config.concept && config.concept.claim && config.concept.claim.FUTURE === "visual_concept";
  if (conceptOk || (config.presets || []).length) {
    const fb = $("mode-future");
    fb.onclick = () => applyMode("future");
  }
  renderConceptPresets();
  updateConceptNote();
  if ($("heading")) {
    $("heading").oninput = () => {
      if (!selectedId) return;
      refreshPlacement(findSite(selectedId), packets[selectedId]);
    };
  }
  if ($("concept-preset")) {
    $("concept-preset").onchange = () => {
      updateConceptNote();
      if (!selectedId) return;
      refreshPlacement(findSite(selectedId), packets[selectedId]);
    };
  }
  if ($("show-interior")) {
    $("show-interior").onchange = () => {
      updateConceptNote();
      if (!selectedId) return;
      refreshPlacement(findSite(selectedId), packets[selectedId]);
    };
  }
  $("past-year").oninput = () => applyPastYear(packets[selectedId]);
  document.querySelectorAll(".mode").forEach((btn) => {
    btn.onclick = () => applyMode(btn.dataset.mode);
  });
  document.querySelectorAll("#layer-rack .layer").forEach((btn) => {
    btn.onclick = () => toggleLayer(btn.dataset.layer);
  });
  if ($("sv-heading")) {
    $("sv-heading").oninput = () => {
      stopStreetSpin();
      const site = selectedId ? findSite(selectedId) : null;
      if (site) paintStreetImage(site);
    };
  }
  refreshCredits();
  loadCustomManifests();
  pickMission("warehouse");
  setTimeout(() => { loadCesium().catch(() => {}); }, 400);
}

function missionConceptKey() {
  return mission === "custom" ? "warehouse" : mission;
}

function missionPresets() {
  const key = missionConceptKey();
  return (config.presets || []).filter((row) => row.mission === key);
}

function missionHasConcept() {
  if (!missionPresets().length) return false;
  if (mission === "warehouse" || mission === "custom") {
    return Boolean(config.concept && config.concept.claim && config.concept.claim.FUTURE === "visual_concept");
  }
  return true;
}

function renderConceptPresets() {
  const sel = $("concept-preset");
  if (!sel) return;
  const rows = missionPresets();
  const previous = sel.value;
  sel.innerHTML = rows.map((row) => `<option value="${row.id}">${row.title}</option>`).join("");
  if (rows.some((row) => row.id === previous)) sel.value = previous;
  else if (rows[0]) sel.value = rows[0].id;
  updateConceptNote();
}

function updateConceptNote() {
  const note = $("concept-note");
  const preset = activePreset();
  const assumptions = (preset && preset.assumptions) || (config.concept && config.concept.footprint && config.concept.footprint.assumptions) || [];
  if (note) {
    note.textContent = assumptions.length
      ? `${assumptions.join(" · ")} Schematic interiors are not a survey.`
      : "Visual concept. Not a permit. Schematic interiors are not a survey.";
  }
  const cad = $("concept-cad");
  const gltf = $("cad-gltf");
  const dxf = $("cad-dxf");
  const ifc = $("cad-ifc");
  if (cad && dxf && ifc) {
    const files = preset && preset.cad;
    const show = Boolean(files && files.dxf && files.ifc);
    cad.hidden = !show;
    if (show) {
      const studioId = files.studio_id || "concept";
      const interiors = interiorOn();
      if (gltf) {
        gltf.href = interiors && files.gltf_interiors ? files.gltf_interiors : files.gltf;
        gltf.download = `${studioId}${interiors ? "-interiors" : ""}.gltf`;
      }
      dxf.href = files.dxf;
      ifc.href = files.ifc;
      dxf.download = `${studioId}.dxf`;
      ifc.download = `${studioId}.ifc`;
    }
  }
}

function activePreset(packet) {
  const sel = $("concept-preset");
  const rows = missionPresets();
  const fromPacket = packet && packet.scene && packet.scene.future && packet.scene.future.preset_id;
  const id = (sel && sel.value) || fromPacket;
  return rows.find((row) => row.id === id) || rows[0] || null;
}

function activePad(packet) {
  const preset = activePreset(packet);
  const pad = packet && packet.scene && packet.scene.assumed_pad;
  if (!preset && !pad) return null;
  return {
    claim: "assumption",
    fit_status: "deferred",
    preset_id: (preset && preset.id) || (pad && pad.preset_id),
    title: (preset && preset.title) || (pad && pad.title) || "Concept",
    length_m: (preset && preset.length_m) || (pad && pad.length_m),
    width_m: (preset && preset.width_m) || (pad && pad.width_m),
    height_m: (preset && preset.height_m) || (pad && pad.height_m) || 10,
    setback_m: (preset && preset.setback_m) || (pad && pad.setback_m) || 10,
    dock_m: (preset && Object.prototype.hasOwnProperty.call(preset, "dock_m") ? preset.dock_m : pad && pad.dock_m) || null,
    bays: (preset && preset.bays) || 0,
    interior: (preset && preset.interior) || (packet && packet.scene && packet.scene.future && packet.scene.future.interior) || [],
    cad: (preset && preset.cad) || (pad && pad.cad) || null,
    family: (preset && preset.family) || missionConceptKey(),
  };
}

function interiorOn() {
  return Boolean($("show-interior") && $("show-interior").checked);
}

function syncInteriorLegend(packet) {
  const el = $("interior-legend");
  if (!el) return;
  const rooms = (activePad(packet) && activePad(packet).interior) || [];
  const show = interiorOn() && sceneMode === "future" && rooms.length;
  el.hidden = !show;
  el.textContent = show
    ? `Program · ${rooms.map((room) => room.label || room.id).join(" · ")}`
    : "";
}

function pickMission(id) {
  mission = id;
  plan = null;
  $("confirm").disabled = true;
  document.querySelectorAll(".tile").forEach((el) => el.classList.toggle("on", el.dataset.id === id));
  $("cult-wrap").hidden = id !== "farm";
  $("water-wrap").hidden = !["warehouse", "data_center"].includes(id);
  $("sewer-wrap").hidden = id !== "warehouse";
  $("fiber-wrap").hidden = !["warehouse", "data_center"].includes(id);
  $("manifest-section").hidden = id !== "custom";
  $("flood").checked = id !== "farm";
  populateSizeBands(id);
  renderPreferences(id);
  renderInvestigations(id);
  resetRouteAnchors(id);
  renderConceptPresets();
  applyMissionCopy(id);
  previewPlan();
}

function applyMissionCopy(id) {
  const copy = MISSION_COPY[id] || MISSION_COPY.warehouse;
  if ($("onboard-kicker")) $("onboard-kicker").textContent = copy.kicker;
  const title = entryPath === "check" ? copy.checkTitle : copy.findTitle;
  const lede = entryPath === "check" ? copy.checkLede : copy.findLede;
  if ($("onboard-title")) $("onboard-title").textContent = title;
  if ($("onboard-lede")) $("onboard-lede").textContent = lede;
}

function checkEntryReady() {
  if (entryPath !== "check") return true;
  const address = ($("entry-address") && $("entry-address").value.trim()) || "";
  const lat = parseFloat($("entry-lat") && $("entry-lat").value);
  const lng = parseFloat($("entry-lng") && $("entry-lng").value);
  return Boolean(address) || (Number.isFinite(lat) && Number.isFinite(lng));
}

function matchingCount() {
  const missionIds = missionSites[mission] || (mission === "custom" ? missionSites.warehouse : []) || [];
  return catalog.filter((row) => missionIds.includes(row.id) && regionAllows(row.id)).length;
}

function setEntryPath(path) {
  entryPath = path === "check" ? "check" : "find";
  if ($("onboard")) $("onboard").dataset.entry = entryPath;
  if ($("app")) $("app").dataset.entry = entryPath;
  document.querySelectorAll(".entry, .job").forEach((el) => {
    const on = el.dataset.entry === entryPath;
    el.classList.toggle("on", on);
    el.setAttribute("aria-selected", on ? "true" : "false");
  });
  if ($("check-entry")) $("check-entry").hidden = entryPath !== "check";
  if ($("entry-note")) {
    $("entry-note").textContent = entryPath === "check"
      ? "We screen your pin. Click the globe to drop one. If it is a bad idea, other pins light up."
      : "Starter places that match this plan. None of these are listings.";
  }
  if ($("region-label")) {
    $("region-label").textContent = entryPath === "check"
      ? "If this fails, recommend places in"
      : "Or pick a region";
  }
  if ($("confirm")) {
    $("confirm").textContent = entryPath === "check" ? "Is this a good idea?" : "Find geographies";
  }
  if ($("hud-query")) {
    $("hud-query").placeholder = entryPath === "check"
      ? "Address or click the map"
      : "City or metro";
  }
  applyMissionCopy(mission || "warehouse");
  previewPlan();
  if ($("app") && !$("app").classList.contains("hidden")) {
    renderCards();
    paintPinCard(selectedId ? findSite(selectedId) : null, selectedId ? packets[selectedId] : null);
  }
}

async function loadCustomManifests() {
  const status = $("custom-status");
  try {
    const res = await apiFetch("/api/custom-manifests");
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(payload.error || `manifest catalog unavailable (${res.status})`);
    const values = Array.isArray(payload) ? payload : (payload.manifests || []);
    customManifests = values.filter((item) => item && (item.id || item.manifest_id));
    const select = $("manifest-id");
    if (!customManifests.length) {
      select.innerHTML = '<option value="">No reviewed manifests available</option>';
      select.disabled = true;
      status.textContent = "Custom Mission unavailable: the reviewed manifest catalog is empty.";
      return;
    }
    select.disabled = false;
    select.innerHTML = '<option value="">Select a reviewed manifest</option>' + customManifests.map((item) => {
      const id = item.id || item.manifest_id;
      const title = item.title || item.name || id;
      const manifestVersion = item.manifest_version || item.version;
      const version = manifestVersion ? ` · v${manifestVersion}` : "";
      return `<option value="${escapeHtml(id)}">${escapeHtml(title + version)}</option>`;
    }).join("");
    status.textContent = `${customManifests.length} reviewed Custom manifest${customManifests.length === 1 ? "" : "s"} available.`;
  } catch (err) {
    customManifests = [];
    $("manifest-id").disabled = true;
    status.textContent = `Custom Mission unavailable: ${err.message}. Standard Missions still work.`;
  }
  if (mission === "custom") {
    $("confirm").disabled = !$("manifest-id").value;
    previewPlan();
  }
}

function populateSizeBands(id) {
  $("size-band").innerHTML = (SIZE_BANDS[id] || SIZE_BANDS.custom)
    .map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
}

function renderPreferences(id) {
  const values = PREFERENCE_OPTIONS[id] || [];
  $("preferences").innerHTML = values.length ? values.map(([key, label]) => `
    <label>${label}
      <select class="preference" data-preference="${key}">
        <option value="not_considered">Not considered</option>
        <option value="useful" selected>Useful</option>
        <option value="important">Important</option>
        <option value="priority">Priority</option>
      </select>
    </label>`).join("") : '<p class="field-note">Preference fields are fixed by the selected reviewed manifest.</p>';
  document.querySelectorAll(".preference").forEach((el) => { el.onchange = previewPlan; });
}

function renderInvestigations(id) {
  const values = INVESTIGATION_OPTIONS[id] || [];
  $("investigations").innerHTML = values.length ? values.map(([key, label, checked]) => `
    <label class="check"><input class="investigation" type="checkbox" value="${key}"${checked ? " checked" : ""}> ${label}</label>`
  ).join("") : '<p class="field-note">Optional investigations are fixed by the selected reviewed manifest.</p>';
  document.querySelectorAll(".investigation").forEach((el) => { el.onchange = previewPlan; });
}

function resetRouteAnchors(id) {
  $("route-anchors").innerHTML = "";
  (DEFAULT_ROUTE_ANCHORS[id] || []).forEach(appendRouteAnchor);
  $("route-section").classList.toggle("optional", !["warehouse", "data_center"].includes(id));
  $("anchor-status").textContent = "";
}

function appendRouteAnchor(anchor) {
  const row = document.createElement("div");
  row.className = "route-row";
  row.dataset.anchorId = anchor.id || "";
  row.innerHTML = `
    <label>Name<input class="anchor-name" type="text" value="${escapeHtml(anchor.name || "")}" placeholder="Customer or hub"></label>
    <label>Latitude<input class="anchor-lat" type="number" min="18" max="72" step="any" value="${anchor.lat ?? ""}" placeholder="29.730"></label>
    <label>Longitude<input class="anchor-lng" type="number" min="-180" max="-65" step="any" value="${anchor.lng ?? ""}" placeholder="-95.120"></label>
    <label>Hard max, min<input class="anchor-max" type="number" min="1" max="1440" step="1" value="${anchor.max_minutes ?? ""}" placeholder="optional"></label>
    <button class="remove-anchor" type="button" aria-label="Remove route anchor">Remove</button>`;
  row.querySelector(".remove-anchor").onclick = () => {
    row.remove();
    previewPlan();
  };
  row.querySelectorAll("input").forEach((input) => { input.onchange = previewPlan; });
  $("route-anchors").appendChild(row);
}

function collectRouteAnchors() {
  const errors = [];
  const anchors = Array.from(document.querySelectorAll(".route-row")).map((row, index) => {
    const name = row.querySelector(".anchor-name").value.trim();
    const latRaw = row.querySelector(".anchor-lat").value;
    const lngRaw = row.querySelector(".anchor-lng").value;
    const maxRaw = row.querySelector(".anchor-max").value;
    if (!name && !latRaw && !lngRaw && !maxRaw) return null;
    const lat = Number(latRaw);
    const lng = Number(lngRaw);
    const max = maxRaw ? Number(maxRaw) : null;
    if (!name || !Number.isFinite(lat) || !Number.isFinite(lng)) {
      errors.push(`Anchor ${index + 1} needs a name, latitude, and longitude.`);
      return null;
    }
    if (lat < 18 || lat > 72 || lng < -180 || lng > -65) {
      errors.push(`${name} is outside the US Mireye envelope.`);
      return null;
    }
    if (max !== null && (!Number.isFinite(max) || max < 1 || max > 1440)) {
      errors.push(`${name} needs a hard maximum from 1 to 1,440 minutes.`);
      return null;
    }
    return {
      id: row.dataset.anchorId || `user_anchor_${index + 1}`,
      name,
      lat,
      lng,
      max_minutes: max,
    };
  }).filter(Boolean);
  $("anchor-status").textContent = errors.join(" ");
  return { anchors, valid: !errors.length };
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function siteName(id) {
  const site = catalog.find((row) => row.id === id) || extras.find((row) => row.id === id);
  return site ? site.name : id;
}

function regionAllows(id) {
  if (intentOpenGeography) return true;
  const region = ($("search-region") && $("search-region").value) || "texas_triangle";
  const geo = ($("geography-band") && $("geography-band").value) || "selected_region";
  if (mission === "warehouse" || mission === "custom") {
    const bands = WAREHOUSE_BANDS[region];
    if (bands) {
      const rank = { selected: 0, adjacent: 1, statewide: 2 };
      const stop = { selected_region: 0, adjacent_regions: 1, statewide: 2 }[geo] ?? 0;
      if (!(id in bands)) return false;
      return rank[bands[id]] <= stop;
    }
  }
  // No stated geography (no typed intent, region select untouched): the
  // national starter pins stay, so the curated demo flows keep working.
  if (!regionAllowlist.length) return true;
  const row = catalog.find((c) => c.id === id);
  if (!row || !Number.isFinite(row.lat) || !Number.isFinite(row.lng)) return true;
  const radius = BAND_RADIUS_KM[geo] ?? BAND_RADIUS_KM.selected_region;
  return regionAllowlist.some((r) => hubDistanceKm(row.lat, row.lng, r) <= radius);
}

function workstreamLine(row) {
  const id = row.id || row.workstream_id || "";
  const question = row.question || WORKSTREAM_QUESTIONS[id] || id;
  const status = row.status || "";
  const note = row.note ? ` · ${row.note}` : (row.reason ? ` · ${row.reason}` : "");
  return `${question} · ${status}${note} · ${id}`;
}

function renderRailList(rows) {
  $("rail").innerHTML = rows.map((row) => {
    const id = row.id || row.workstream_id || "";
    const candidate = row.candidate_id || row.candidate || "";
    const who = candidate ? `${escapeHtml(siteName(candidate))} · ` : "";
    return `<li data-workstream="${escapeHtml(id)}" data-candidate="${escapeHtml(candidate)}" data-status="${escapeHtml(row.status || "")}" data-phase="${escapeHtml(row.phase || "")}">${who}${escapeHtml(workstreamLine(row))}</li>`;
  }).join("");
}

function renderExpeditionLog(lines) {
  const log = $("expedition-log");
  if (!log) return;
  if (!lines.length) {
    log.innerHTML = "<li>Confirm the plan, then run the Expedition.</li>";
    return;
  }
  log.innerHTML = lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("");
}

function logAction(line) {
  const log = $("expedition-log");
  if (!log) return;
  if (log.textContent.includes("Scout the pins") || log.textContent.includes("Confirm the plan")) log.innerHTML = "";
  const item = document.createElement("li");
  item.textContent = line;
  log.appendChild(item);
}

async function previewPlan() {
  if (!mission) return;
  const payload = controls();
  const request = ++planRequest;
  if (!payload) {
    plan = null;
    $("confirm").disabled = true;
    $("plan-card").textContent = "Fix the highlighted controls before confirming this Mission Plan.";
    return;
  }
  if (mission === "custom" && !payload.manifest_id) {
    plan = null;
    $("confirm").disabled = true;
    $("plan-card").textContent = "Custom Mission requires a reviewed manifest. The standard Mission recipes remain available.";
    return;
  }
  try {
    const res = await apiFetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const nextPlan = await res.json().catch(() => ({}));
    if (request !== planRequest) return;
    if (!res.ok) {
      plan = null;
      $("confirm").disabled = true;
      $("plan-card").textContent = nextPlan.message || nextPlan.error || `Mission Plan could not be compiled (HTTP ${res.status}).`;
      return;
    }
    plan = nextPlan;
    const n = matchingCount();
    const prefs = payload.preferences.filter((item) => item.weight !== "not_considered");
    const copy = MISSION_COPY[mission] || MISSION_COPY.warehouse;
    const region = REGION_LABELS[payload.search_region] || payload.search_region;
    const hardFlood = (plan.hard_constraints || []).includes("not_mapped_sfha");
    const hardCultivated = (plan.hard_constraints || []).some((item) => String(item).includes("cultivated"));
    if (entryPath === "check") {
      $("plan-card").textContent =
        `${copy.placing}. ` +
        (hardFlood ? "Mapped floodplain is a hard no. " : "") +
        (checkEntryReady() ? "We screen your pin." : "Add an address or click the map after you open the globe.");
    } else {
      const look = ($("look-query") && $("look-query").value.trim()) || "";
      $("plan-card").textContent =
        `${copy.placing} in ${look || region}. ` +
        (hardFlood ? "Mapped floodplain is a hard no. " : "") +
        (look
          ? `Map search around ${look}. Not listings.`
          : `${n} starter pin${n === 1 ? "" : "s"} in ${region}. Not listings.`);
    }
    const ready = true;
    $("confirm").disabled = !ready;
    if ($("confirm")) {
      $("confirm").textContent = entryPath === "check" ? "Is this a good idea?" : "Find geographies";
    }
    if (!ready && $("entry-status")) {
      $("entry-status").textContent = "Add an address or pin.";
    } else if ($("entry-status")) {
      $("entry-status").textContent = "";
    }
  } catch (error) {
    if (error instanceof AuthenticationRequired) throw error;
    if (request !== planRequest) return;
    plan = null;
    $("confirm").disabled = true;
    $("plan-card").textContent = `Mission Plan could not be compiled: ${error.message}`;
  }
}

function controls() {
  const route = collectRouteAnchors();
  if (!route.valid) return null;
  return {
    mission,
    manifest_id: mission === "custom" ? ($("manifest-id").value || null) : null,
    search_region: $("search-region").value,
    geography_band: $("geography-band").value,
    size_band: $("size-band").value,
    budget_band: $("budget-band").value,
    scan_budget: $("scan").value,
    site_form: $("site-form").value,
    flood_intolerant: $("flood").checked,
    require_cultivated: mission === "farm" ? $("cultivated").checked : false,
    require_water_service: !$("water-wrap").hidden && $("water-service").checked,
    require_sewer_service: !$("sewer-wrap").hidden && $("sewer-service").checked,
    require_fiber_service: !$("fiber-wrap").hidden && $("fiber-service").checked,
    preferences: Array.from(document.querySelectorAll(".preference")).map((el) => ({
      id: el.dataset.preference,
      weight: el.value,
    })),
    optional_investigations: Array.from(document.querySelectorAll(".investigation:checked")).map((el) => el.value),
    route_anchors: route.anchors,
    region_allowlist: regionAllowlist,
  };
}

function syncLookRegion() {
  const look = (($("look-query") && $("look-query").value) || "").trim().toLowerCase();
  if (!look || !$("search-region")) return;
  const mapped = LOOK_TO_REGION[look] || LOOK_TO_REGION[look.split(",")[0].trim()];
  if (mapped && $("search-region").value !== mapped) {
    $("search-region").value = mapped;
    regionAllowlist = [mapped];
  }
}

async function readIntent() {
  const text = ($("intent-text") && $("intent-text").value.trim()) || "";
  const status = $("intent-status");
  if (!text) {
    if (status) status.textContent = "Say what you are trying to do.";
    return;
  }
  if ($("intent-go")) $("intent-go").disabled = true;
  if (status) status.textContent = "Compiling a Mission Plan…";
  try {
    const res = await apiFetch("/api/intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, live_model: true }),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (status) status.textContent = payload.message || payload.error || "Could not read that.";
      return;
    }
    applyIntentResult(payload);
    const who = payload.source === "model"
      ? `${payload.model || "Luna"} proposed. Compiler still owns the gates.`
      : "";
    if (status) status.textContent = `${who} ${(payload.rationale || []).join(" ")}`.trim();
  } catch (error) {
    if (error instanceof AuthenticationRequired) throw error;
    if (status) status.textContent = error.message || "Could not read that.";
  } finally {
    if ($("intent-go")) $("intent-go").disabled = false;
  }
}

function applyIntentResult(payload) {
  const controlsIn = payload.controls || {};
  regionAllowlist = Array.isArray(payload.region_allowlist) ? payload.region_allowlist.slice() : [];
  intentOpenGeography = !regionAllowlist.length;
  if (controlsIn.mission) pickMission(controlsIn.mission);
  if (controlsIn.search_region && $("search-region")) {
    $("search-region").value = controlsIn.search_region;
  }
  if (typeof controlsIn.flood_intolerant === "boolean" && $("flood")) {
    $("flood").checked = controlsIn.flood_intolerant;
  }
  if (controlsIn.size_band && $("size-band")) $("size-band").value = controlsIn.size_band;
  if (typeof controlsIn.require_cultivated === "boolean" && $("cultivated")) {
    $("cultivated").checked = controlsIn.require_cultivated;
  }
  if (controlsIn.site_form && $("site-form")) $("site-form").value = controlsIn.site_form;
  if (controlsIn.scan_budget && $("scan")) $("scan").value = controlsIn.scan_budget;
  (controlsIn.preferences || []).forEach((row) => {
    const select = document.querySelector(`.preference[data-preference="${row.id}"]`);
    if (select && row.weight) select.value = row.weight;
  });
  renderIntentChips(payload);
  previewPlan();
}

function renderIntentChips(payload) {
  const wrap = $("intent-chips");
  if (!wrap) return;
  const controlsIn = payload.controls || {};
  const chips = [];
  if (controlsIn.mission) chips.push(controlsIn.mission.replace("_", " "));
  (payload.region_allowlist || []).forEach((id) => chips.push(REGION_LABELS[id] || id));
  if (payload.open_inventory) chips.push("all locate metros");
  if (controlsIn.flood_intolerant) chips.push("no mapped floodplain");
  if (controlsIn.size_band && controlsIn.size_band !== "flexible") {
    chips.push(String(controlsIn.size_band).replace(/_/g, " "));
  }
  if (controlsIn.mission === "farm" && controlsIn.require_cultivated === false) {
    chips.push("pasture, not CDL cultivated");
  }
  (controlsIn.preferences || []).forEach((row) => {
    if (row.weight && row.weight !== "not_considered") {
      chips.push(`${String(row.id).replace(/_/g, " ")} · ${row.weight}`);
    }
  });
  wrap.hidden = !chips.length;
  wrap.innerHTML = chips.map((label, index) => (
    `<span class="intent-chip${index ? " soft" : ""}">${escapeHtml(label)}</span>`
  )).join("");
}

function showLocatePanel(show) {
  const panel = $("locate-panel");
  if (panel) panel.hidden = !show;
}

function metricLine(row, field, label, digits) {
  const metric = (row.metrics || {})[field];
  if (!metric || metric.kind === "UNKNOWN" || metric.value == null) return "";
  const value = typeof metric.value === "number"
    ? (digits == null ? String(metric.value) : Number(metric.value).toFixed(digits))
    : String(metric.value);
  const unit = metric.unit && metric.unit !== "1" ? ` ${metric.unit}` : "";
  return `${label} ${value}${unit}`;
}

function renderLocate() {
  const wrap = $("locate-cards");
  const honesty = $("locate-honesty");
  const sensitivity = $("locate-sensitivity");
  if (honesty) honesty.textContent = (locatePacket && locatePacket.honesty) || "";
  const swaps = ((locatePacket && locatePacket.sensitivity) || []).filter((row) => row.order_changed);
  if (sensitivity) {
    sensitivity.textContent = swaps.length
      ? swaps.map((row) => `Drop ${row.dropped} and ${REGION_LABELS[row.top_becomes] || row.top_becomes} overtakes ${REGION_LABELS[row.top_was] || row.top_was}.`).join(" ")
      : "Order is lexicographic on gates then your preference bands. Not a score.";
  }
  if (!wrap) return;
  const rows = (locatePacket && locatePacket.regions) || [];
  wrap.innerHTML = rows.map((row) => {
    const vetoed = row.status === "vetoed";
    const flood = metricLine(row, "mapped_sfha_share", "SFHA share", 2);
    const rail = metricLine(row, "rail_distance_m", "rail", 0);
    const grid = metricLine(row, "grid_distance_m", "grid", 0);
    const labor = row.metrics && row.metrics.civilian_employed
      ? `labor context ${Number(row.metrics.civilian_employed.value).toLocaleString()} employed (not hiring)`
      : "";
    const lines = [flood, rail, grid, labor].filter(Boolean);
    return (
      `<button type="button" class="locate-card${vetoed ? " vetoed" : ""}${row.rank === 1 && !vetoed ? " on" : ""}" data-region="${escapeHtml(row.region_id)}" ${vetoed ? "disabled" : ""}>` +
      `<p class="rank">${vetoed ? "Vetoed" : `Rank ${row.rank}`}</p>` +
      `<strong>${escapeHtml(row.label)}</strong>` +
      lines.map((line) => `<p class="metric">${escapeHtml(line)}</p>`).join("") +
      `<p class="why">${escapeHtml(row.veto_reason || row.counterfactual || "")}</p>` +
      (vetoed ? "" : `<p class="cta">Scout pins in this metro</p>`) +
      `</button>`
    );
  }).join("");
  wrap.querySelectorAll(".locate-card:not([disabled])").forEach((btn) => {
    btn.onclick = () => selectLocateRegion(btn.dataset.region);
  });
}

async function loadLocate() {
  const payload = controls();
  if (!payload) return;
  const allow = (regionAllowlist && regionAllowlist.length)
    ? regionAllowlist
    : (intentOpenGeography ? [] : [payload.search_region]);
  if ($("status")) $("status").textContent = "Ranking metros from replayed probe aggregates. Zero Mireye credits.";
  try {
    const res = await apiFetch("/api/regions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission,
        region_allowlist: allow,
        controls: payload,
      }),
    });
    const packet = await res.json().catch(() => ({}));
    if (!res.ok) {
      if ($("status")) $("status").textContent = packet.message || packet.error || "Region rank failed.";
      return;
    }
    locatePacket = packet;
    renderLocate();
    const top = packet.top_region_ids && packet.top_region_ids[0];
    if (top && REGION_FLY[top] && viewer) flyToRegionId(top);
    if ($("status")) {
      $("status").textContent = top
        ? `${REGION_LABELS[top] || top} leads. Click a survivor to scout pins.`
        : "No surviving metros.";
    }
    logAction("Locate ranked metros. Not listings.");
  } catch (error) {
    if (error instanceof AuthenticationRequired) throw error;
    if ($("status")) $("status").textContent = error.message || "Region rank failed.";
  }
}

function flyToRegionId(regionId) {
  const dest = REGION_FLY[regionId];
  if (!dest || !viewer || typeof Cesium === "undefined") return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(dest[0], dest[1], dest[2]),
    duration: 1.2,
  });
}

async function selectLocateRegion(regionId) {
  if (!regionId || !$("search-region")) return;
  $("search-region").value = regionId;
  regionAllowlist = [regionId];
  extras = extras.filter((site) => site.source !== "openstreetmap");
  Object.keys(siteOrigin).forEach((id) => {
    if (siteOrigin[id] === "discovered") delete siteOrigin[id];
  });
  showLocatePanel(false);
  setBoardBeat("scout");
  renderCards();
  flyToRegion();
  logAction(`Scout inside ${REGION_LABELS[regionId] || regionId}. Pins stay POTENTIAL.`);
  await previewPlan();
  if ($("plan-locked") && plan) {
    $("plan-locked").textContent =
      `${plan.mission} · ${REGION_LABELS[regionId] || regionId} · ${plan.hard_constraints.join(", ") || "no hard gates"}`;
  }
  await fillDiscoverInBackground();
  renderCards();
  const first = activeSites()[0];
  if (first) selectSite(first.id, { fly: true });
}

async function discoverPlaces() {
  const look = ($("look-query") && $("look-query").value.trim()) || "";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 18000);
  try {
    const res = await apiFetch("/api/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission,
        search_region: ($("search-region") && $("search-region").value) || "texas_triangle",
        look_query: look,
        network: true,
      }),
      signal: controller.signal,
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { candidates: [], note: payload.message || payload.error || "Map search failed." };
    }
    return payload;
  } catch (error) {
    if (error instanceof AuthenticationRequired) throw error;
    return { candidates: [], note: "Map search timed out. Starter pins still work." };
  } finally {
    clearTimeout(timer);
  }
}

async function confirmPlan() {
  if (!plan || !controls()) return;
  extras = [];
  packets = {};
  missionComparison = null;
  screenedIds = null;
  heldIds = new Set();
  siteOrigin = {};
  waveIds = null;
  selectedId = null;
  recommendMode = false;
  activeChip = null;
  layerOn.flood = false;
  if (entryPath === "check") {
    await applyPendingCheck();
  }
  resetSwipe();
  $("confirm").disabled = true;
  $("confirm").textContent = "Opening globe…";
  try {
    await loadCesium();
  } catch (error) {
    $("plan-card").textContent = "The globe could not load. Check the network and try again.";
    $("confirm").disabled = false;
    $("confirm").textContent = entryPath === "check" ? "Is this a good idea?" : "Find geographies";
    return;
  }
  $("onboard").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("app").dataset.mission = mission;
  $("app").dataset.entry = entryPath;
  if ($("hud-query")) {
    $("hud-query").value = entryPath === "find"
      ? (($("look-query") && $("look-query").value) || "")
      : (($("entry-address") && $("entry-address").value) || "");
    $("hud-query").placeholder = entryPath === "check"
      ? "Address or click the map"
      : "City or metro";
  }
  if ($("look-switcher")) $("look-switcher").hidden = true;
  $("mission-kicker").textContent = `${mission.replace("_", " ")} expedition`;
  $("plan-locked").textContent =
    `${plan.mission} · ${plan.scan_budget} · ${plan.hard_constraints.join(", ") || "no hard gates"}`;
  $("status").textContent = "";
  await ensureViewer();
  bindGlobeClick();
  const futureButton = $("mode-future");
  const futureOk = missionHasConcept();
  futureButton.disabled = !futureOk;
  futureButton.classList.toggle("off", !futureOk);
  futureButton.title = futureOk
    ? "Visual concept after Concept Studio. Schematic interiors. Not a permit."
    : "No concept preset is available for this Mission.";
  $("mode-pad").disabled = !futureOk;
  $("mode-pad").title = futureOk
    ? "Parametric pad. Assumption, not FIT."
    : "No assumed pad for this Mission.";
  $("mode-past").disabled = true;
  $("mode-past").title = "Screen a site to attach a temporal witness.";
  applyMode("aerial");
  setTimeout(() => { if (viewer) viewer.resize(); }, 80);
  renderCards();
  renderCompare();
  clearDetail();
  renderExpeditionLog([]);
  if (entryPath === "check" && extras[0]) {
    const first = activeSites()[0];
    if (first) selectSite(first.id, { fly: false, duration: 0 });
    setBoardBeat("screen");
    showLocatePanel(false);
    await runOne(extras[0].id);
  } else if (entryPath === "find") {
    setBoardBeat("locate");
    showLocatePanel(true);
    flyToRegion();
    paintPinCard(null, null);
    await loadLocate();
  } else {
    setBoardBeat("scout");
    showLocatePanel(false);
    const first = activeSites()[0];
    if (first) {
      selectSite(first.id, { fly: false, duration: 0 });
      flyToSites(activeSites(), 1.4);
    } else {
      flyToRegion();
      paintPinCard(null, null);
    }
  }
  refreshCredits();
}

async function fillDiscoverInBackground() {
  if ($("status")) $("status").textContent = "Searching the map for matching places…";
  const found = await discoverPlaces();
  const incoming = found.candidates || [];
  incoming.forEach((site) => {
    if (extras.some((row) => row.id === site.id)) return;
    extras.push(site);
    siteOrigin[site.id] = "discovered";
    keepNewSite(site.id);
  });
  renderCards();
  renderCompare();
  if (incoming.length && typeof flyToSites === "function") flyToSites(activeSites(), 1.4);
  if ($("status")) {
    $("status").textContent = incoming.length
      ? `${incoming.length} map places. Not listings. ${found.note || ""}`.trim()
      : (found.note || "No map places in this area. Starter pins still work.");
  }
  if ($("next-move") && incoming.length) {
    $("next-move").textContent = `${incoming.length} map places, not listings. Screen counts catalog pins only.`;
  }
}

async function applyPendingCheck() {
  if (entryPath !== "check") return false;
  if ($("check-tools")) $("check-tools").open = true;
  const address = ($("entry-address") && $("entry-address").value.trim()) || "";
  const latRaw = ($("entry-lat") && $("entry-lat").value.trim()) || "";
  const lngRaw = ($("entry-lng") && $("entry-lng").value.trim()) || "";
  if (address) {
    $("site-address").value = address;
    const known = catalogByAddress(address);
    if (known) {
      placeKnownSite(known, address);
      return true;
    }
    return addAddressSite({ silent: true });
  }
  if (latRaw && lngRaw) {
    $("pin-lat").value = latRaw;
    $("pin-lng").value = lngRaw;
    return Boolean(placePin(parseFloat(latRaw), parseFloat(lngRaw)));
  }
  return false;
}

function setBoardBeat(beat) {
  if (!BEAT_ORDER.includes(beat)) return;
  boardBeat = beat;
  if ($("app")) $("app").dataset.beat = beat;
  if ($("selection-stage")) $("selection-stage").hidden = beat !== "scout";
  showLocatePanel(beat === "locate");
  const idx = BEAT_ORDER.indexOf(beat);
  document.querySelectorAll("#beat-strip .beat").forEach((el) => {
    const pos = BEAT_ORDER.indexOf(el.dataset.beat);
    el.classList.toggle("on", el.dataset.beat === beat);
    el.classList.toggle("done", pos >= 0 && pos < idx);
  });
  if ($("board-title")) $("board-title").textContent = BEAT_TITLES[beat] || "Scout";
  syncWorkflow();
}

function jumpToBeat(beat) {
  if (beat === "locate") {
    if (entryPath === "find") {
      setBoardBeat("locate");
      showLocatePanel(true);
    }
    return;
  }
  if (beat === "scout") {
    setBoardBeat("scout");
    if ($("swipe-face")) $("swipe-face").focus();
    return;
  }
  if (beat === "screen") {
    if ($("run-all")) $("run-all").focus();
    return;
  }
  if (beat === "compare") {
    if (Object.keys(packets).length) setBoardBeat("compare");
    else syncWorkflow();
    return;
  }
  if (beat === "sketch") {
    if (missionHasConcept() && $("mode-future") && !$("mode-future").disabled) applyMode("future");
  }
}

function screenedCount() {
  return Object.keys(packets).length;
}

function scoutCounts() {
  const catalogOpen = curatedSites().filter((site) => !passedIds.has(site.id));
  const kept = passedIds.size ? catalogKeptIds() : catalogOpen.map((site) => site.id);
  const discovered = extras.filter((site) => site.source === "openstreetmap" && !passedIds.has(site.id)).length;
  return { kept: kept.length, passed: passedIds.size, open: catalogOpen.length, discovered };
}

function syncWorkflow() {
  const counts = scoutCounts();
  const screened = screenedCount();
  const busy = Boolean($("run-all") && $("run-all").disabled);
  const selected = selectedId ? findSite(selectedId) : null;
  if ($("run-all") && !busy) {
    if (screened) $("run-all").textContent = "Screen again";
    else if (passedIds.size) $("run-all").textContent = `Screen ${counts.kept} kept pin${counts.kept === 1 ? "" : "s"}`;
    else $("run-all").textContent = `Screen ${counts.kept || counts.open} catalog pin${(counts.kept || counts.open) === 1 ? "" : "s"}`;
  } else if ($("run-all") && busy) {
    $("run-all").textContent = "Screening…";
  }
  if ($("compare-wait")) $("compare-wait").hidden = screened > 0 || boardBeat === "compare";
  const next = $("next-move");
  const story = $("story");
  if (busy) {
    if (next) next.textContent = "Workstreams are running. Rejects cancel leftover work.";
    return;
  }
  if (boardBeat === "locate") {
    if (next) next.textContent = "Pick a metro. Pins wait until you do. None of these are listings.";
    if (story) story.textContent = "Locate geographies first.";
    return;
  }
  if (boardBeat === "sketch") {
    if (next) next.textContent = "FUTURE is a labeled sketch. Interior is a program diagram. Not a permit, not FIT.";
    return;
  }
  if (screened) {
    if (next) {
      next.textContent = missionHasConcept()
        ? "Compare survivors. FUTURE sketch is unlocked on a Conditional pin."
        : "Compare survivors. Homework stays visible until a responsible authority answers.";
    }
    return;
  }
  if (entryPath === "check" && selected && isUserSite(selected) && !recommendMode) {
    if (next) next.textContent = packets[selected.id]
      ? "Your pin is screened. Other cards appear if it is not a good idea."
      : "This is your place. Screen it. If it is a bad idea, other cards show up.";
    if (story) story.textContent = `${selected.name} · USER SITE`;
    $("status").textContent = "Your pin, not a listing.";
    return;
  }
  if (entryPath === "check" && recommendMode) {
    if (next) next.textContent = "Your pin stayed. These cards are other places to try. Keep the ones you want.";
    if (story && selected) story.textContent = `${selected.name} · ${selected.label}`;
    $("status").textContent = "Recommendations are starter places, not listings.";
    return;
  }
  if (entryPath === "check") {
    if (next) next.textContent = "Drop an address or pin. That is the place we screen.";
    if (story && selected) story.textContent = `${selected.name} · ${selected.label}`;
    $("status").textContent = "I have a place screens your pin. Find places is the starter list.";
    return;
  }
  if (!counts.open) {
    if (next) next.textContent = "The deck is empty. Undo a Pass, or drop a pin / type an address.";
    if (story) story.textContent = "No pins left to scout.";
    $("status").textContent = "Pass is not a Reject. Undo, or add a USER SITE.";
    return;
  }
  if (next) {
    next.textContent = passedIds.size
      ? `${counts.kept} kept · ${counts.passed} passed. Screen when the shortlist feels right.`
      : counts.discovered
        ? `${counts.discovered} map places sit beside catalog pins. Screen counts catalog only.`
        : "Keep the pins you want. Pass is not a Reject. Screening waits.";
  }
  if (story) {
    story.textContent = selected
      ? `${selected.name} · ${selected.label} · not screened`
      : "Scout the pins. Screening starts when you ask.";
  }
  if ($("status")) {
    $("status").textContent = counts.discovered
      ? `${counts.discovered} map places. Not listings.`
      : "";
  }
}

function flyToRegion() {
  if (!viewer) return;
  const region = ($("search-region") && $("search-region").value) || "texas_triangle";
  const dest = REGION_FLY[region] || REGION_FLY.texas_triangle;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(dest[0], dest[1], dest[2]),
    duration: 1.2,
  });
}

function pickLatLng(position) {
  if (!viewer) return null;
  const picked = viewer.scene.pick(position);
  if (picked && picked.id && picked.id.id) {
    const entityId = String(picked.id.id);
    if (entityId.startsWith("pin-")) return { pinId: entityId.slice(4) };
    if (entityId.startsWith("layer-flood")) return { layer: "flood" };
  }
  let cartesian = null;
  if (viewer.scene.pickPositionSupported) {
    cartesian = viewer.scene.pickPosition(position);
  }
  if (!Cesium.defined(cartesian)) {
    cartesian = viewer.camera.pickEllipsoid(position, viewer.scene.globe.ellipsoid);
  }
  if (!Cesium.defined(cartesian)) return null;
  const carto = Cesium.Cartographic.fromCartesian(cartesian);
  return {
    lat: Cesium.Math.toDegrees(carto.latitude),
    lng: Cesium.Math.toDegrees(carto.longitude),
  };
}

function bindGlobeClick() {
  if (!viewer || clickHandler) return;
  clickHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  clickHandler.setInputAction((click) => {
    if (swipeBusy()) return;
    const hit = pickLatLng(click.position);
    if (!hit) return;
    if (hit.pinId) {
      selectSite(hit.pinId, { fly: true });
      return;
    }
    if (hit.layer === "flood") {
      if (!layerOn.flood) toggleLayer("flood");
      showFloodExpand(selectedId ? packets[selectedId] : null);
      return;
    }
    dropExaminePin(hit.lat, hit.lng);
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

function examineSite(id) {
  const site = findSite(id) || catalog.find((row) => row.id === id);
  if (!site) return;
  setEntryPath("check");
  if (!extras.some((row) => row.id === id)) {
    extras.unshift({ ...site });
    keepNewSite(id);
  }
  selectSite(id, { fly: true });
  renderCards();
}

function dropExaminePin(lat, lng) {
  const id = placePin(lat, lng);
  if (!id) return;
  setEntryPath("check");
  renderCards();
  renderCompare();
  selectSite(id, { fly: true });
  const site = findSite(id);
  if (!site) return;
  if (packets[id]) {
    paintPinCard(site, packets[id]);
    return;
  }
  const known = catalog.some((row) => row.id === id) || Boolean(catalogPinNear(lat, lng));
  if (known) {
    runOne(id);
    return;
  }
  paintPinCard(site, null);
  if ($("live") && $("live").checked) {
    runOne(id);
    return;
  }
  if ($("pin-note")) {
    $("pin-note").textContent = "New pin. Turn on Live Mireye to read it, or drop on a known place.";
  }
}

function floodAtom(packet) {
  return ((packet && packet.atoms) || []).find((atom) => atom.field_id === "fema_flood_zone") || null;
}

function showFloodExpand(packet) {
  const panel = $("flood-expand");
  if (panel) panel.hidden = true;
  const reasons = (packet && packet.verdict && packet.verdict.reasons) || [];
  const atom = floodAtom(packet);
  const mapped = reasons.includes("mapped_sfha");
  const zone = atom && atom.value != null ? String(atom.value) : "";
  const source = (atom && atom.source) || "FEMA NFHL";
  const body = $("flood-expand-body");
  let line = "";
  if (layerOn.flood && !mapped) {
    line = "No mapped Special Flood Hazard Area at this pin. Overlay stays off.";
  } else if (layerOn.flood && mapped) {
    line = zone
      ? `Mapped SFHA · zone ${zone} · ${source}. Cited, not a score.`
      : `Mapped Special Flood Hazard Area · ${source}. Cited, not a score.`;
  }
  if (body) body.textContent = line || "Cited to FEMA NFHL. This paint is the mapped zone at the pin, not a score.";
  if (line && $("pin-note")) $("pin-note").textContent = line;
}

function paintPinCard(site, packet) {
  const card = $("pin-card");
  if (!card) return;
  if (!site) {
    card.hidden = entryPath !== "check";
    if ($("pin-kicker")) $("pin-kicker").textContent = "Examine";
    if ($("pin-name")) $("pin-name").textContent = "Click the map";
    if ($("pin-chips")) $("pin-chips").innerHTML = "";
    if ($("pin-cite")) $("pin-cite").textContent = "";
    if ($("pin-note")) $("pin-note").textContent = "Drop a pin. The HUD reads the surface. Credits stay in the corner.";
    if ($("flood-expand")) $("flood-expand").hidden = true;
    return;
  }
  card.hidden = false;
  const prior = packet || packets[site.id];
  if ($("pin-kicker")) $("pin-kicker").textContent = site.label || "POTENTIAL";
  if ($("pin-name")) $("pin-name").textContent = site.name;
  const chips = $("pin-chips");
  if (chips) {
    const rows = (prior && prior.scorecard) || [];
    const floodRow = rows.find((row) => row.id === "flood");
    const items = [];
    items.push({
      id: "flood",
      label: "Flood FEMA",
      status: floodRow ? floodRow.status : "unknown",
      layer: "flood",
    });
    rows.filter((row) => row.id !== "flood" && row.status === "fail").slice(0, 2).forEach((row) => {
      items.push({
        id: row.id,
        label: row.label,
        status: row.status,
        layer: "",
      });
    });
    if (!items.length) {
      items.push({ id: "idle", label: "Not read yet", status: "unknown", layer: "" });
    }
    chips.innerHTML = items.map((item) => {
      const on = item.layer && layerOn[item.layer] ? " on" : "";
      const tone = item.status === "fail" ? " fail" : item.status === "pass" ? " pass" : "";
      return `<button type="button" class="pin-chip${on}${tone}" data-chip="${escapeHtml(item.id)}" data-layer="${escapeHtml(item.layer || "")}">${escapeHtml(item.label)}</button>`;
    }).join("");
    chips.querySelectorAll(".pin-chip").forEach((btn) => {
      btn.onclick = () => activateChip(btn.dataset.chip, btn.dataset.layer, site, prior);
    });
  }
  const cite = [];
  if (prior && prior.verdict && prior.verdict.reasons && prior.verdict.reasons.length) {
    cite.push((prior.verdict.reasons || []).join(", "));
  }
  const atom = floodAtom(prior);
  if (atom && atom.source) cite.push(atom.source);
  if ($("pin-cite")) $("pin-cite").textContent = cite.join(" · ");
  if ($("pin-note") && !prior) {
    $("pin-note").textContent = site.source === "openstreetmap"
      ? "Map place, not a listing. Read it to attach Mireye."
      : "Not read yet.";
  } else if ($("pin-note") && prior) {
    $("pin-note").textContent = "";
  }
  showFloodExpand(prior);
}

function activateChip(chipId, layer, site, packet) {
  activeChip = chipId;
  if (layer === "flood") {
    toggleLayer("flood");
    return;
  }
  if ($("pin-note")) {
    $("pin-note").textContent = "That chip is a cited fact. Flood is the projection you can paint.";
  }
}

async function submitHudQuery() {
  const q = ($("hud-query") && $("hud-query").value.trim()) || "";
  if (entryPath === "find") {
    if ($("look-query")) $("look-query").value = q;
    await previewPlan();
    if ($("app") && !$("app").classList.contains("hidden")) {
      await fillDiscoverInBackground();
      return;
    }
    await confirmPlan();
    return;
  }
  if ($("entry-address")) $("entry-address").value = q;
  if ($("site-address")) $("site-address").value = q;
  if ($("app") && !$("app").classList.contains("hidden")) {
    if (q) await addAddressSite();
    return;
  }
  await previewPlan();
  await confirmPlan();
}

const CESIUM_BASE = "https://ajax.googleapis.com/ajax/libs/cesiumjs/1.105/Build/Cesium/";
let cesiumLoad = null;

function loadCesium() {
  if (window.Cesium) return Promise.resolve();
  if (cesiumLoad) return cesiumLoad;
  cesiumLoad = new Promise((resolve, reject) => {
    window.CESIUM_BASE_URL = CESIUM_BASE;
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = `${CESIUM_BASE}Widgets/widgets.css`;
    document.head.appendChild(css);
    const script = document.createElement("script");
    script.src = `${CESIUM_BASE}Cesium.js`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      cesiumLoad = null;
      reject(new Error("Cesium failed to load"));
    };
    document.head.appendChild(script);
  });
  return cesiumLoad;
}

function bindHud() {
  if ($("job-examine")) $("job-examine").onclick = () => setEntryPath("check");
  if ($("job-discover")) $("job-discover").onclick = () => setEntryPath("find");
  if ($("hud-search")) {
    $("hud-search").onsubmit = (event) => {
      event.preventDefault();
      submitHudQuery();
    };
  }
}

async function ensureViewer() {
  if (viewer) {
    viewer.useDefaultRenderLoop = true;
    viewer.resize();
    return;
  }
  viewer = new Cesium.Viewer("cesium", {
    imageryProvider: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    animation: false,
    timeline: false,
    fullscreenButton: false,
    infoBox: false,
    selectionIndicator: false,
    requestRenderMode: false,
    skyBox: false,
    skyAtmosphere: false,
  });
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#0c0d0e");
  viewer.scene.globe.show = true;
  viewer.scene.globe.depthTestAgainstTerrain = false;
  viewer.scene.globe.maximumScreenSpaceError = 4;
  viewer.scene.globe.preloadSiblings = false;
  viewer.scene.fog.enabled = false;
  if (viewer.scene.globe.tileCacheSize != null) viewer.scene.globe.tileCacheSize = 250;
  viewer.imageryLayers.removeAll();
  ensureGlobeImagery();
  bindGlobeClick();

  if (config.has_google_tiles) {
    $("status").textContent = "";
    $("mode-mesh").disabled = false;
    $("mode-mesh").title = "Photorealistic 3D — context only. Loads when you pick 3D.";
    $("mode-aerial").disabled = false;
  } else {
    $("status").textContent = "No Map Tiles key — Street View if coverage exists.";
    $("mode-mesh").disabled = true;
    $("mode-aerial").disabled = true;
  }
}

function ensureTileset() {
  if (tileset || !viewer || !config.has_google_tiles) return tileset;
  $("mode-mesh").title = "Loading photorealistic 3D…";
  tileset = viewer.scene.primitives.add(
    new Cesium.Cesium3DTileset({
      url: config.tileset,
      showCreditsOnScreen: false,
      show: false,
      maximumScreenSpaceError: 24,
    })
  );
  tileset.tileVisible.addEventListener(() => {
    revealPhotorealisticMesh();
  });
  tileset.readyPromise
    .then(() => {
      $("mode-mesh").disabled = false;
      $("mode-mesh").title = "Photorealistic 3D — context only";
      if (selectedId && ["street", "mesh", "future", "earth", "orbit"].includes(sceneMode)) {
        revealPhotorealisticMesh();
        if (sceneMode === "future") placeConcept(findSite(selectedId), packets[selectedId]);
        if (["earth", "orbit", "street", "mesh"].includes(sceneMode)) {
          flyTo(findSite(selectedId), 0.8);
        }
      }
    })
    .catch(() => {
      $("mode-mesh").disabled = true;
      $("mode-mesh").title = "Photorealistic 3D is unavailable";
      $("status").textContent = "Photorealistic 3D is unavailable. Aerial View and Street View still play.";
    });
  return tileset;
}

function mapZoom() {
  if (sceneMode === "future" && mission === "warehouse") return 19;
  if (sceneMode === "pad" && mission === "warehouse") return 18;
  if (mission === "warehouse") return 18;
  if (mission === "home") return 18;
  return 16;
}

function meshTilesReady() {
  if (!tileset) return false;
  const stats = tileset._statistics || {};
  return Number(stats.numberOfTilesWithContentReady || 0) >= 8;
}

function ensureGlobeImagery() {
  if (!viewer) return;
  $("quick-map").classList.add("hidden");
  viewer.scene.globe.show = true;
  if (viewer.imageryLayers.length > 0) return;
  const url = (config.has_google_tiles && config.satellite)
    ? config.satellite
    : "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  viewer.imageryLayers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({
    url,
    maximumLevel: 19,
  }));
}

function revealPhotorealisticMesh() {
  if (!["street", "mesh", "future", "earth", "orbit"].includes(sceneMode) || !meshTilesReady()) return;
  meshContentReady = true;
  clearTimeout(meshLoadTimer);
  $("quick-map").classList.add("hidden");
  if (tileset) tileset.show = true;
  if (sceneMode === "street" && $("street-stage") && !$("street-stage").hidden) {
    return;
  }
  if (sceneMode === "street") {
    $("status").textContent = $("status").textContent || "No Street View at this pin. Street-height 3D — presentation only.";
  }
  if (sceneMode === "mesh") {
    $("status").textContent = "";
    $("context-tag").textContent = "Google photorealistic 3D — context only. Does not score.";
  }
  if (sceneMode === "future") {
    $("context-tag").textContent = "FUTURE visual concept — not a permit.";
  }
  if (sceneMode === "earth" || sceneMode === "orbit") {
    $("context-tag").textContent = "Photorealistic 3D of this pin. Aerial View plays if Google has one. Does not score.";
  }
}

function el(className, tag) {
  const node = document.createElement(tag || "div");
  node.className = className;
  return node;
}

function buildInteriorPlan(rooms) {
  const plan = el("interior-plan");
  (rooms || []).forEach((room) => {
    const cell = el("interior-room");
    cell.style.left = `${(room.x || 0) * 100}%`;
    cell.style.top = `${(room.y || 0) * 100}%`;
    cell.style.width = `${(room.w || 0) * 100}%`;
    cell.style.height = `${(room.h || 0) * 100}%`;
    const label = document.createElement("span");
    label.textContent = room.label || room.id;
    cell.append(label);
    plan.append(cell);
  });
  return plan;
}

function buildConceptMass(pad, padW, padH, heightPx) {
  const box = el("future-box");
  box.dataset.claim = "visual_concept";
  box.dataset.preset = pad.preset_id || "";
  box.dataset.family = pad.family || "warehouse";
  box.style.width = `${padW}px`;
  box.style.height = `${padH}px`;
  box.style.setProperty("--wh-h", `${heightPx}px`);
  box.style.setProperty("--wh-w", `${padW}px`);
  box.style.setProperty("--wh-l", `${padH}px`);
  const shadow = el("wh-shadow");
  const apron = el("wh-apron");
  const mass = el("wh-mass");
  const roof = el("wh-face wh-roof");
  roof.append(el("wh-seam"), el("wh-hvac"), el("wh-hvac wh-hvac-b"));
  const south = el("wh-face wh-south");
  const doors = el("wh-doors");
  const bays = Number(pad.bays);
  const doorCount = Number.isFinite(bays)
    ? bays
    : Math.max(0, Math.min(8, Math.round((pad.length_m || 80) / 12)));
  for (let i = 0; i < doorCount; i += 1) doors.append(el("wh-door"));
  south.append(doors, el("wh-canopy"));
  const office = el("wh-office");
  office.append(el("wh-face wh-office-roof"), el("wh-face wh-office-south"), el("wh-face wh-office-east"));
  mass.append(roof, south, el("wh-face wh-east"), el("wh-face wh-west"), el("wh-face wh-north"), office);
  box.append(shadow, apron, mass);
  if (interiorOn() && (pad.interior || []).length) {
    box.append(buildInteriorPlan(pad.interior));
  }
  return box;
}

function buildWarehouseMass(pad, padW, padH, heightPx) {
  return buildConceptMass(pad, padW, padH, heightPx);
}

function metersToPixels(lat, meters, zoom) {
  const metersPerPixel = 156543.03392 * Math.cos((Number(lat) * Math.PI) / 180) / (2 ** zoom);
  return meters / metersPerPixel;
}

function headingRad() {
  return ((Number($("heading").value) || 0) * Math.PI) / 180;
}

function paintMapOverlays(map, site, packet) {
  if (!map || !site) return;
  map.querySelectorAll(".past-overlay, .pad-overlay, .dock-overlay, .future-box").forEach((node) => node.remove());
  const pastEl = document.createElement("div");
  pastEl.id = "past-overlay";
  pastEl.className = "past-overlay";
  pastEl.dataset.alpha = "0";
  pastEl.hidden = sceneMode !== "past";
  map.appendChild(pastEl);
  if (sceneMode === "past") applyPastYear(packet, pastEl);
  const pad = activePad(packet);
  const showPad = ["pad", "future"].includes(sceneMode) && pad && pad.claim === "assumption";
  if (!showPad) return;
  const zoom = mapZoom();
  const padW = metersToPixels(site.lat, pad.width_m, zoom);
  const padH = metersToPixels(site.lat, pad.length_m, zoom);
  const setbackPx = metersToPixels(site.lat, Number(pad.setback_m) || 10, zoom);
  const lotW = padW + setbackPx * 2;
  const lotH = padH + setbackPx * 2;
  const yaw = Number($("heading").value) || 0;
  const padEl = document.createElement("div");
  padEl.id = "pad-overlay";
  padEl.className = "pad-overlay";
  padEl.dataset.claim = pad.claim;
  padEl.dataset.lengthM = String(pad.length_m);
  padEl.dataset.widthM = String(pad.width_m);
  padEl.style.width = `${lotW}px`;
  padEl.style.height = `${lotH}px`;
  padEl.style.left = `calc(50% - ${lotW / 2}px)`;
  padEl.style.top = `calc(50% - ${lotH / 2}px)`;
  padEl.style.transform = `rotateZ(${yaw}deg)`;
  map.appendChild(padEl);
  if (sceneMode === "future") {
    const heightPx = Math.max(28, metersToPixels(site.lat, pad.height_m || 10, zoom) * 1.55);
    const box = buildConceptMass(pad, padW, padH, heightPx);
    box.style.left = `calc(50% - ${padW / 2}px)`;
    box.style.top = `calc(50% - ${padH / 2}px)`;
    box.style.transform = `rotateZ(${yaw}deg)`;
    map.appendChild(box);
  }
  const dock = pad.dock_m || {};
  if (sceneMode === "pad" && dock.length && dock.width) {
    const dockEl = document.createElement("div");
    dockEl.className = "dock-overlay";
    const dockW = metersToPixels(site.lat, dock.width, zoom);
    const dockH = metersToPixels(site.lat, dock.length, zoom);
    dockEl.style.width = `${dockW}px`;
    dockEl.style.height = `${dockH}px`;
    dockEl.style.left = `calc(50% - ${dockW / 2}px)`;
    dockEl.style.top = `calc(50% + ${padH / 2}px)`;
    dockEl.style.transform = `rotateZ(${yaw}deg)`;
    dockEl.style.transformOrigin = `50% ${-padH / 2}px`;
    map.appendChild(dockEl);
  }
}

function applyPastYear(packet, overlay) {
  const pastEl = overlay || document.getElementById("past-overlay");
  const past = packet && packet.scene && packet.scene.past;
  const sliderWrap = $("past-slider-wrap");
  const panel = $("era-panel");
  if (!pastEl) return;
  if (!past || past.kind === "none") {
    pastEl.dataset.alpha = "0";
    pastEl.style.opacity = "0";
    pastEl.hidden = true;
    if (panel) panel.hidden = sceneMode !== "past";
    if (sliderWrap) sliderWrap.hidden = true;
    $("past-note").textContent = past && past.note ? past.note : "No temporal witness attached.";
    return;
  }
  if (panel) panel.hidden = sceneMode !== "past";
  const series = Array.isArray(past.series) ? past.series : [];
  const hasSeries = series.length >= 2;
  if (sliderWrap) sliderWrap.hidden = !hasSeries;
  if (past.kind === "farm_history") {
    pastEl.dataset.alpha = "0";
    pastEl.style.opacity = "0";
    pastEl.hidden = true;
    $("past-year-label").textContent = "";
    $("past-note").textContent = [
      `${past.years_observed || "?"} years observed`,
      past.pattern,
      past.annual_mean_mm != null ? `${past.annual_mean_mm} mm CHIRPS` : null,
      "No yearly map is invented.",
      past.note,
    ].filter(Boolean).join(" · ");
    return;
  }
  if (!hasSeries || past.kind !== "flood_rewind") {
    pastEl.dataset.alpha = "0";
    pastEl.style.opacity = "0";
    $("past-note").textContent = past.note || "Temporal witness has no yearly series.";
    return;
  }
  const slider = $("past-year");
  slider.min = String(series[0].year);
  slider.max = String(series[series.length - 1].year);
  const year = Number(slider.value);
  const row = series.find((item) => item.year === year) || series.reduce((best, item) => (
    Math.abs(item.year - year) < Math.abs(best.year - year) ? item : best
  ));
  const alpha = Number(row.water_freq) || 0;
  pastEl.hidden = sceneMode !== "past";
  pastEl.dataset.alpha = String(alpha);
  pastEl.dataset.year = String(row.year);
  pastEl.style.opacity = alpha > 0 ? String(Math.min(0.72, 0.18 + alpha * 4)) : "0";
  $("past-year-label").textContent = String(row.year);
  $("past-note").textContent = `${row.year} · JRC water frequency ${alpha} · does not score. FEMA present-state still decides mapped SFHA.`;
}

function updatePlacementClaim(packet) {
  const el = $("placement-claim");
  const pad = activePad(packet);
  const fit = packet && packet.scene && packet.scene.fit;
  if (!pad) {
    el.hidden = true;
    el.dataset.claim = "";
    el.dataset.fit = "";
    return;
  }
  el.hidden = !["pad", "future"].includes(sceneMode);
  el.dataset.claim = pad.claim || "";
  el.dataset.fit = (fit && fit.claim) || "";
  el.textContent = `${pad.length_m}×${pad.width_m} m sketch · not a permit · not FIT`;
}

function syncEraButtons(packet) {
  const past = packet && packet.scene && packet.scene.past;
  const pastOk = Boolean(past && past.kind && past.kind !== "none");
  $("mode-past").disabled = !pastOk;
  $("mode-past").title = pastOk
    ? (past.kind === "flood_rewind"
      ? "JRC water-frequency rewind. Does not score."
      : "Bounded temporal witness. Does not score.")
    : "No temporal witness attached to this packet.";
  const padOk = Boolean(activePad(packet) && activePad(packet).claim === "assumption");
  if ($("mode-pad")) {
    $("mode-pad").disabled = !padOk;
  }
  if ($("mode-future")) {
    const futureOk = Boolean(
      missionHasConcept()
      && packet
      && packet.verdict
      && packet.verdict.verdict !== "reject"
      && packet.scene
      && packet.scene.future
      && packet.scene.future.claim === "visual_concept"
    );
    $("mode-future").disabled = !futureOk;
    $("mode-future").classList.toggle("off", !futureOk);
    $("mode-future").title = futureOk
      ? "Visual concept. Schematic interiors. Not a permit. FIT is a named gap."
      : "FUTURE is for a surviving candidate with a concept preset.";
  }
}

function pastContext(packet) {
  const past = packet && packet.scene && packet.scene.past;
  if (!past || past.kind === "none") return "PAST — no temporal witness. Does not score.";
  if (past.kind === "flood_rewind") {
    const dem = past.dem_delta_m != null
      ? ` USGS 3DEP ${past.usgs_3dep_m} m vs NASADEM ${past.nasadem_m} m. Does not score.`
      : " Elevation-model disagreement is a gap. Does not score.";
    return `PAST flood rewind — JRC water frequency. FEMA still decides the veto.${dem}`;
  }
  if (past.kind === "farm_history") return "PAST farm history — CDL/CHIRPS summary, no invented yearly map. Does not score.";
  if (past.kind === "observed_heat") return "PAST observed heat — not a climate forecast. Does not score.";
  if (past.kind === "land_change") return "PAST land change — Dynamic World modal built fraction. INFORM only. Does not score.";
  return "PAST temporal witness. Does not score.";
}

function enuPoint(lng, lat, east, north, heading) {
  const origin = Cesium.Cartesian3.fromDegrees(lng, lat, 0);
  const transform = Cesium.Transforms.eastNorthUpToFixedFrame(origin);
  const cos = Math.cos(heading);
  const sin = Math.sin(heading);
  const e = east * cos - north * sin;
  const n = east * sin + north * cos;
  return Cesium.Matrix4.multiplyByPoint(transform, new Cesium.Cartesian3(e, n, 0), new Cesium.Cartesian3());
}

function clearPadEntities() {
  if (!viewer) return;
  padEntities.forEach((entity) => viewer.entities.remove(entity));
  padEntities = [];
}

function placeAssumedPad(site, scene, packet) {
  clearPadEntities();
  const pad = activePad(packet || { scene });
  if (!viewer || !site || !pad || pad.claim !== "assumption") return;
  if (sceneMode !== "pad") return;
  const heading = headingRad();
  const hl = pad.length_m / 2;
  const hw = pad.width_m / 2;
  const setback = Number(pad.setback_m) || 10;
  const corners = [
    enuPoint(site.lng, site.lat, -hw, -hl, heading),
    enuPoint(site.lng, site.lat, hw, -hl, heading),
    enuPoint(site.lng, site.lat, hw, hl, heading),
    enuPoint(site.lng, site.lat, -hw, hl, heading),
  ];
  const lot = [
    enuPoint(site.lng, site.lat, -(hw + setback), -(hl + setback), heading),
    enuPoint(site.lng, site.lat, hw + setback, -(hl + setback), heading),
    enuPoint(site.lng, site.lat, hw + setback, hl + setback, heading),
    enuPoint(site.lng, site.lat, -(hw + setback), hl + setback, heading),
  ];
  const lotPolygon = {
    hierarchy: new Cesium.PolygonHierarchy(lot),
    material: Cesium.Color.fromCssColorString("#ff7a18").withAlpha(0.42),
  };
  if (Cesium.ClassificationType) {
    lotPolygon.classificationType = Cesium.ClassificationType.BOTH;
  }
  padEntities.push(viewer.entities.add({ polygon: lotPolygon }));
  padEntities.push(viewer.entities.add({
    polygon: {
      hierarchy: new Cesium.PolygonHierarchy(corners),
      material: Cesium.Color.fromCssColorString("#ffcc33").withAlpha(0.55),
      outline: true,
      outlineColor: Cesium.Color.fromCssColorString("#ffe27a"),
      height: 0.4,
      extrudedHeight: 1.6,
    },
  }));
  padEntities.push(viewer.entities.add({
    position: Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 18),
    label: {
      text: "ASSUMED PAD · not FIT",
      font: "13px Clash, sans-serif",
      fillColor: Cesium.Color.fromCssColorString("#ece8e0"),
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      pixelOffset: new Cesium.Cartesian2(0, 36),
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  }));
  const dock = pad.dock_m || {};
  if (dock.length && dock.width) {
    const north = -(pad.length_m / 2 + dock.length / 2);
    const position = enuPoint(site.lng, site.lat, 0, north, heading);
    padEntities.push(viewer.entities.add({
      position,
      orientation: Cesium.Transforms.headingPitchRollQuaternion(
        position,
        new Cesium.HeadingPitchRoll(heading, 0, 0)
      ),
      box: {
        dimensions: new Cesium.Cartesian3(dock.width, dock.length, dock.height || 1.4),
        material: Cesium.Color.fromCssColorString("#5d6570").withAlpha(0.92),
      },
    }));
  }
}

function refreshPlacement(site, packet) {
  if (!site) return;
  if (sceneMode === "future") placeConcept(site, packet);
  if (sceneMode === "pad") placeAssumedPad(site, packet && packet.scene, packet);
  syncInteriorLegend(packet);
  const map = $("quick-map");
  if (map && !map.classList.contains("hidden")) paintMapOverlays(map, site, packet);
  updatePlacementClaim(packet);
}

async function consumeNdjson(response, onEvent) {
  const ctype = (response.headers.get("content-type") || "").toLowerCase();
  if (!response.body || (!ctype.includes("ndjson") && !response.ok)) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(payload.message || payload.error || `HTTP ${response.status}`);
    error.payload = payload;
    error.status = response.status;
    throw error;
  }
  window.__streamTrace = [];
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let errorEvent = null;
  const pushLine = (line) => {
    if (!line.trim()) return;
    const event = JSON.parse(line);
    window.__streamTrace.push({
      event: event.event,
      workstream_id: event.workstream_id,
      status: event.status,
      candidate_id: event.candidate_id,
    });
    if (event.event === "error") errorEvent = event;
    onEvent(event);
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    lines.forEach(pushLine);
  }
  if (buffer.trim()) pushLine(buffer);
  if (errorEvent) {
    const error = new Error(errorEvent.message || errorEvent.error || "stream failed");
    error.payload = errorEvent;
    error.status = 0;
    throw error;
  }
}

function noteWorkstream(event) {
  if (event.event !== "workstream") return;
  const id = event.workstream_id;
  if (!id) return;
  const items = Array.from($("rail").querySelectorAll("li"));
  const existing = items.find((item) => item.dataset.workstream === id && item.dataset.candidate === (event.candidate_id || ""));
  const row = {
    id,
    workstream_id: id,
    candidate_id: event.candidate_id,
    status: event.status,
    reason: event.reason,
    note: event.reason,
    question: event.question,
    phase: event.phase,
  };
  const who = event.candidate_id ? `${siteName(event.candidate_id)} · ` : "";
  const text = `${who}${workstreamLine(row)}`;
  if (existing) {
    existing.dataset.status = event.status;
    existing.textContent = text;
    return;
  }
  if ($("rail").textContent.includes("running…") || $("rail").textContent.includes("expedition ·") || $("rail").textContent.includes("idle")) {
    $("rail").innerHTML = "";
  }
  const li = document.createElement("li");
  li.dataset.workstream = id;
  li.dataset.status = event.status;
  li.dataset.candidate = event.candidate_id || "";
  li.dataset.phase = event.phase || "";
  li.textContent = text;
  $("rail").appendChild(li);
}

function applyMapBase(mode) {
  if (!viewer) return;
  hideEarthSky();
  viewer.imageryLayers.removeAll();
  viewer.scene.globe.show = false;
  if (mode === "hidden") {
    $("quick-map").classList.add("hidden");
    return;
  }
  if (selectedId) renderQuickMap(findSite(selectedId), mode);
  if (mode === "aerial" && config.has_google_tiles) {
    $("context-tag").textContent = "Google aerial map — overhead fallback. Does not score.";
    return;
  }
  $("context-tag").textContent = "OpenStreetMap — context only. Does not score.";
}

function renderQuickMap(site, mode) {
  if (!site) return;
  const map = $("quick-map");
  const renderId = ++quickMapRender;
  map.classList.remove("hidden", "ready");
  map.replaceChildren();
  const zoom = mapZoom();
  const scale = 2 ** zoom;
  const lat = Math.max(-85.05112878, Math.min(85.05112878, Number(site.lat)));
  const lng = Number(site.lng);
  const worldX = ((lng + 180) / 360) * scale * 256;
  const radians = lat * Math.PI / 180;
  const worldY = (1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2 * scale * 256;
  const width = map.clientWidth || window.innerWidth;
  const height = map.clientHeight || window.innerHeight;
  const minX = Math.floor((worldX - width / 2) / 256);
  const maxX = Math.floor((worldX + width / 2) / 256);
  const minY = Math.max(0, Math.floor((worldY - height / 2) / 256));
  const maxY = Math.min(scale - 1, Math.floor((worldY + height / 2) / 256));
  const centerX = Math.floor(worldX / 256);
  const centerY = Math.floor(worldY / 256);
  const tiles = [];
  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      tiles.push({ x, y, distance: Math.abs(x - centerX) + Math.abs(y - centerY) });
    }
  }
  tiles.sort((a, b) => a.distance - b.distance);
  let errors = 0;
  tiles.forEach(({ x, y }, index) => {
    const wrappedX = ((x % scale) + scale) % scale;
    const tile = document.createElement("img");
    tile.alt = "";
    tile.draggable = false;
    tile.decoding = "async";
    if (index === 0) tile.fetchPriority = "high";
    tile.style.left = `${x * 256 - worldX + width / 2}px`;
    tile.style.top = `${y * 256 - worldY + height / 2}px`;
    tile.src = mode === "aerial" && config.has_google_tiles
      ? config.satellite.replace("{z}", zoom).replace("{x}", wrappedX).replace("{y}", y)
      : `https://tile.openstreetmap.org/${zoom}/${wrappedX}/${y}.png`;
    tile.addEventListener("load", () => {
      if (renderId !== quickMapRender) return;
      tile.dataset.loaded = "true";
      map.classList.add("ready");
    }, { once: true });
    tile.addEventListener("error", () => {
      if (renderId !== quickMapRender || mode !== "aerial") return;
      errors += 1;
      if (errors >= 3 && ["aerial", "past", "pad", "future"].includes(sceneMode)) {
        renderQuickMap(site, "osm");
        $("status").textContent = "Google aerial tiles are unavailable. Showing OpenStreetMap.";
      }
    }, { once: true });
    map.appendChild(tile);
  });
  const label = document.createElement("span");
  label.className = "quick-map-label";
  label.textContent = site.name;
  if (["future", "pad"].includes(sceneMode)) label.hidden = true;
  map.appendChild(label);
  const pin = document.createElement("span");
  pin.className = "quick-map-pin";
  pin.setAttribute("aria-hidden", "true");
  if (sceneMode === "future") pin.hidden = true;
  map.appendChild(pin);
  const credit = document.createElement("span");
  credit.className = "quick-map-credit";
  credit.textContent = mode === "aerial"
    ? "Google satellite · context only"
    : "© OpenStreetMap contributors · context only";
  map.appendChild(credit);
  paintMapOverlays(map, site, packets[site.id]);
}

function markModeChrome(mode) {
  const era = ["past"].includes(mode) ? "past"
    : ["future", "pad"].includes(mode) ? "future"
    : "today";
  document.querySelectorAll(".modes .mode[data-era]").forEach((b) => {
    b.classList.toggle("on", b.dataset.era === era);
  });
  const tools = $("today-tools");
  if (tools) tools.hidden = era !== "today";
  document.querySelectorAll("#today-tools .mode").forEach((b) => {
    b.classList.toggle("on", era === "today" && b.dataset.mode === mode);
  });
  $("app").dataset.era = era;
}

function applyMode(mode) {
  if (mode === "fit") return;
  const futureOk = missionHasConcept();
  if (mode === "future" && !futureOk) return;
  if (mode === "past" && $("mode-past").disabled) return;
  if (mode === "pad" && $("mode-pad") && $("mode-pad").disabled) return;
  sceneMode = mode;
  markModeChrome(mode);
  if (["future", "pad"].includes(mode)) {
    if (boardBeat !== "place") setBoardBeat("sketch");
  } else if (boardBeat === "sketch") {
    setBoardBeat(screenedCount() ? "compare" : "scout");
  }
  $("app").classList.toggle("sim-view", ["pad", "future", "past"].includes(mode));
  $("app").dataset.mode = mode;
  $("concept-controls").hidden = !["future", "pad"].includes(mode);
  $("era-panel").hidden = mode !== "past";
  stopOrbit();
  stopStreetSpin();
  if (mode !== "street") hideStreetStage();
  hideEarthStage();
  closeAerial({ silent: true });
  if (!viewer) {
    if (mode === "street" && selectedId) loadStreetView(findSite(selectedId));
    if (mode === "earth") presentEarthLook(selectedId ? findSite(selectedId) : null, selectedId ? packets[selectedId] : null);
    if (mode === "orbit" && selectedId) presentOrbit(findSite(selectedId), packets[selectedId]);
    return;
  }
  if (["mesh", "future", "earth", "orbit", "street"].includes(mode)) ensureTileset();
  clearTimeout(meshLoadTimer);
  if (mode !== "future") clearConcept();
  if (mode !== "pad") clearPadEntities();
  const packet = selectedId ? packets[selectedId] : null;
  const site = selectedId ? findSite(selectedId) : null;
  if (mode === "past") {
    if (tileset) tileset.show = false;
    hideStreetStage();
    applyMapBase(config.has_google_tiles ? "aerial" : "osm");
    $("context-tag").textContent = pastContext(packet);
    $("status").textContent = "";
    refreshPlacement(site, packet);
    return;
  }
  if (mode === "pad") {
    if (tileset) tileset.show = false;
    hideStreetStage();
    applyMapBase(config.has_google_tiles ? "aerial" : "osm");
    $("context-tag").textContent = "Assumed pad and dock — not FIT, not a permit.";
    $("status").textContent = "";
    refreshPlacement(site, packet);
    if (site) flyTo(site, 0.4);
    return;
  }
  if (mode === "street") {
    ensureGlobeImagery();
    if (tileset) tileset.show = meshTilesReady();
    $("context-tag").textContent = "Street-level view — presentation only. Does not score.";
    $("status").textContent = site ? "Looking up Street View…" : "Pick a pin for Street View.";
    if (site) {
      loadStreetView(site);
      flyTo(site, 0.8);
    }
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "earth") {
    ensureGlobeImagery();
    if (tileset) tileset.show = meshTilesReady();
    presentEarthLook(site, packet);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "orbit") {
    ensureGlobeImagery();
    if (tileset) tileset.show = meshTilesReady();
    presentOrbit(site, packet);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "mesh") {
    hideStreetStage();
    ensureGlobeImagery();
    if (tileset) tileset.show = meshTilesReady();
    $("context-tag").textContent = meshTilesReady()
      ? "Google photorealistic 3D — context only. Does not score."
      : "Satellite globe — context only. 3D loads in the background.";
    $("status").textContent = meshTilesReady() ? "" : "Loading 3D. Satellite stays until it is ready.";
    revealPhotorealisticMesh();
    meshLoadTimer = setTimeout(() => {
      if (sceneMode !== "mesh") return;
      if (!meshTilesReady()) {
        $("context-tag").textContent = "Satellite globe — context only. Does not score.";
        $("status").textContent = "";
        return;
      }
      $("status").textContent = "";
    }, 8000);
    const open = activeSites().filter((row) => !passedIds.has(row.id));
    if (open.length > 1 && !screenedCount()) flyToSites(activeSites(), 1.4);
    else if (site) flyTo(site, 0.8);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "future") {
    hideStreetStage();
    $("context-tag").textContent = "FUTURE visual concept — not a permit.";
    $("status").textContent = "";
    if (config.has_google_tiles) {
      ensureTileset();
      if (tileset) tileset.show = true;
      applyMapBase("hidden");
      revealPhotorealisticMesh();
    } else {
      if (tileset) tileset.show = false;
      applyMapBase("osm");
    }
    refreshPlacement(site, packet);
    if (site) flyTo(site, 0.8);
    return;
  }
  if (mode === "aerial" || mode === "osm") {
    hideStreetStage();
    $("quick-map").classList.add("hidden");
    if (tileset) tileset.show = false;
    if (mode === "osm") {
      viewer.imageryLayers.removeAll();
      viewer.scene.globe.show = true;
      viewer.imageryLayers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({
        url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        maximumLevel: 19,
      }));
      $("context-tag").textContent = "OpenStreetMap — context only. Does not score.";
    } else {
      ensureGlobeImagery();
      $("context-tag").textContent = "Satellite globe — context only. Does not score.";
    }
    $("status").textContent = "";
    const open = activeSites().filter((row) => !passedIds.has(row.id));
    if (open.length > 1 && !screenedCount()) flyToSites(activeSites(), 1.4);
    else if (site) flyTo(site, 0.8);
    updatePlacementClaim(packet);
    return;
  }
  if (tileset) tileset.show = false;
  hideStreetStage();
  applyMapBase(mode === "osm" ? "osm" : "aerial");
  $("status").textContent = "";
  updatePlacementClaim(packet);
}

function clearConcept() {
  if (conceptModel && viewer) {
    viewer.scene.primitives.remove(conceptModel);
    conceptModel = null;
  }
}

function groundHeightM(lng, lat) {
  if (!viewer) return 0;
  const carto = Cesium.Cartographic.fromDegrees(lng, lat);
  try {
    if (viewer.scene.sampleHeight) {
      const sampled = viewer.scene.sampleHeight(carto);
      if (sampled != null && Number.isFinite(sampled)) return sampled;
    }
  } catch (err) { /* tileset may not be ready */ }
  try {
    if (viewer.scene.globe && viewer.scene.globe.show) {
      const globeH = viewer.scene.globe.getHeight(carto);
      if (globeH != null && Number.isFinite(globeH)) return globeH;
    }
  } catch (err) { /* globe height unavailable */ }
  return 0;
}

function placeConcept(site, packet) {
  if (!viewer || !site) return;
  const token = ++conceptPlaceToken;
  const pad = activePad(packet);
  const preset = activePreset(packet);
  const cad = preset && preset.cad;
  const interiors = interiorOn();
  const studioUrl = cad && (interiors ? cad.gltf_interiors : cad.gltf);
  const url = studioUrl || config.warehouse_gltf || "/assets/warehouse.gltf";
  const nativeW = (cad && cad.native_width_m) || 40;
  const nativeH = (cad && cad.native_height_m) || 10;
  const nativeL = (cad && cad.native_length_m) || 80;
  const heading = headingRad();
  const hpr = new Cesium.HeadingPitchRoll(heading, 0, 0);
  const scale = new Cesium.Cartesian3(
    ((pad && pad.width_m) || nativeW) / nativeW,
    ((pad && pad.height_m) || nativeH) / nativeH,
    ((pad && pad.length_m) || nativeL) / nativeL
  );

  const mount = (heightM) => {
    if (token !== conceptPlaceToken || sceneMode !== "future" || !viewer) return;
    clearConcept();
    clearPadEntities();
    const origin = Cesium.Cartesian3.fromDegrees(site.lng, site.lat, heightM + 0.35);
    let modelMatrix = Cesium.Transforms.headingPitchRollToFixedFrame(origin, hpr);
    modelMatrix = Cesium.Matrix4.multiply(modelMatrix, Cesium.Matrix4.fromScale(scale), new Cesium.Matrix4());
    conceptModel = viewer.scene.primitives.add(Cesium.Model.fromGltf({
      url,
      modelMatrix,
      scale: 1,
      colorBlendMode: Cesium.ColorBlendMode.HIGHLIGHT,
      colorBlendAmount: 0,
    }));
    if (conceptModel && conceptModel.readyPromise) {
      conceptModel.readyPromise.then(() => {
        if (viewer && sceneMode === "future") viewer.scene.requestRender();
      }).catch(() => {});
    }
    const lengthM = (pad && pad.length_m) || nativeL;
    const widthM = (pad && pad.width_m) || nativeW;
    const eaveM = (pad && pad.height_m) || nativeH;
    const labelFont = "12px Clash, sans-serif";
    padEntities.push(viewer.entities.add({
      position: enuPoint(site.lng, site.lat, 0, lengthM / 2 + 8, heading),
      label: {
        text: `${Math.round(lengthM)} × ${Math.round(widthM)} m`,
        font: labelFont,
        fillColor: Cesium.Color.fromCssColorString("#ece8e0"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 3,
        pixelOffset: new Cesium.Cartesian2(0, 0),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    }));
    padEntities.push(viewer.entities.add({
      position: enuPoint(site.lng, site.lat, widthM / 2 + 8, 0, heading),
      label: {
        text: `${Math.round(eaveM)} m eave`,
        font: labelFont,
        fillColor: Cesium.Color.fromCssColorString("#ece8e0"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 3,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    }));
    padEntities.push(viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(site.lng, site.lat, heightM + eaveM + 6),
      label: {
        text: "CONCEPTUAL · NOT A PERMIT",
        font: "11px Clash, sans-serif",
        fillColor: Cesium.Color.fromCssColorString("#f2d27a"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 3,
        pixelOffset: new Cesium.Cartesian2(0, -28),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    }));
  };

  mount(groundHeightM(site.lng, site.lat));
  if (typeof viewer.scene.sampleHeightMostDetailed === "function") {
    const carto = Cesium.Cartographic.fromDegrees(site.lng, site.lat);
    viewer.scene.sampleHeightMostDetailed([carto]).then((rows) => {
      const height = rows && rows[0] && rows[0].height;
      if (height == null || !Number.isFinite(height)) return;
      mount(height);
    }).catch(() => {});
  }
}

function pickPlanningSite(results) {
  const list = Array.isArray(results) ? results : [];
  const survivors = list.filter((packet) => packet.verdict && packet.verdict.verdict !== "reject");
  if (mission === "warehouse") {
    const sanMarcos = survivors.find((packet) => packet.candidate && packet.candidate.id === "san_marcos_tx");
    if (sanMarcos) return sanMarcos;
  }
  return survivors[0] || list[0] || null;
}

function curatedSites() {
  const missionIds = missionSites[mission] || (mission === "custom" ? missionSites.warehouse : []) || [];
  const allow = new Set(missionIds);
  const extraIds = new Set(extras.map((site) => site.id));
  // Held-out reject-demo pins (Midtown Manhattan farm) only belong to the
  // untouched demo board. A stated geography or typed ask drops them.
  const intentActive = intentOpenGeography || regionAllowlist.length > 0;
  return catalog.filter((c) => allow.has(c.id) && !extraIds.has(c.id)
    && regionAllows(c.id) && !(intentActive && c.held_out));
}

function activeSites() {
  const extraIds = new Set(extras.map((site) => site.id));
  const curated = (entryPath === "check" && !recommendMode) ? [] : curatedSites();
  const candidates = extras.concat(curated);
  if (waveIds) {
    return candidates.filter((candidate) => (
      waveIds.has(candidate.id)
      || heldIds.has(candidate.id)
      || extraIds.has(candidate.id)
      || passedIds.has(candidate.id)
    ));
  }
  return screenedIds
    ? candidates.filter((candidate) => (
      screenedIds.has(candidate.id)
      || extraIds.has(candidate.id)
      || passedIds.has(candidate.id)
    ))
    : candidates;
}

function findSite(id) {
  return activeSites().find((c) => c.id === id) || extras.find((c) => c.id === id) || catalog.find((c) => c.id === id);
}

function catalogPinNear(lat, lng) {
  return catalog.find((row) => Math.abs(row.lat - lat) <= 0.0002 && Math.abs(row.lng - lng) <= 0.0002) || null;
}

function catalogByAddress(address) {
  const stripZip = (value) => String(value || "").trim().toLowerCase().replace(/,?\s*\d{5}(?:-\d{4})?$/, "");
  const needle = stripZip(address);
  if (!needle) return null;
  return catalog.find((row) => stripZip(row.address) === needle) || null;
}

function placeKnownSite(row, address) {
  if (extras.some((item) => item.id === row.id)) {
    keepNewSite(row.id);
    return row.id;
  }
  extras.unshift({
    ...row,
    address: address || row.address,
    label: "USER SITE",
    source: row.address ? "user_address" : "user_pin",
    captured_at: new Date().toISOString(),
  });
  keepNewSite(row.id);
  return row.id;
}

function placePin(lat, lng) {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    if ($("entry-status")) $("entry-status").textContent = "Need a numeric lat and lng.";
    $("status").textContent = "Need a numeric lat and lng.";
    return null;
  }
  if (lat < 18 || lat > 72 || lng < -180 || lng > -65) {
    if ($("entry-status")) $("entry-status").textContent = "Pin is outside the US Mireye envelope.";
    $("status").textContent = "Pin is outside the US Mireye envelope.";
    return null;
  }
  const match = catalogPinNear(lat, lng);
  if (match) return placeKnownSite(match);
  const id = `user_${lat.toFixed(5)}_${lng.toFixed(5)}`.replace(/[.-]/g, "m");
  if (extras.some((row) => row.id === id)) {
    keepNewSite(id);
    return id;
  }
  extras.unshift({
    id,
    name: `User pin ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
    lat,
    lng,
    label: "USER SITE",
    site_form: $("site-form").value,
    source: "user_pin",
    captured_at: new Date().toISOString(),
  });
  keepNewSite(id);
  return id;
}

function addUserSite() {
  const id = placePin(parseFloat($("pin-lat").value), parseFloat($("pin-lng").value));
  if (!id) return;
  renderCards();
  renderCompare();
  selectSite(id, { fly: true });
}

async function addAddressSite(opts) {
  const silent = Boolean(opts && opts.silent);
  if ($("resolve-address").disabled) return false;
  const address = $("site-address").value.trim();
  if (!address) {
    $("address-status").textContent = "Enter a complete US street address.";
    if (silent && $("entry-status")) $("entry-status").textContent = "Enter a complete US street address.";
    return false;
  }
  $("resolve-address").disabled = true;
  $("address-status").textContent = "Resolving address once…";
  try {
    const res = await apiFetch("/api/resolve-address", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, live: $("live").checked }),
    });
    const resolved = await res.json().catch(() => ({}));
    if (!res.ok) {
      const message = resolved.message || resolved.error || "Address resolve failed.";
      $("address-status").textContent = message;
      if (silent && $("entry-status")) $("entry-status").textContent = message;
      return false;
    }
    if (resolved.disposition !== "resolved") {
      const choices = (resolved.candidates || [])
        .map((candidate) => candidate.normalized_address || `${candidate.lat}, ${candidate.lng}`)
        .join(" / ");
      const message = `${resolved.message || "Address needs clarification."}${choices ? ` Candidate: ${choices}` : ""}`;
      $("address-status").textContent = message;
      if (silent && $("entry-status")) $("entry-status").textContent = message;
      return false;
    }
    const id = resolved.candidate_id || `address_${resolved.lat.toFixed(5)}_${resolved.lng.toFixed(5)}`.replace(/[.-]/g, "m");
    const existing = extras.find((row) => row.id === id) || findSite(id);
    if (!existing) {
      extras.unshift({
        id,
        name: resolved.normalized_address || address,
        address,
        lat: resolved.lat,
        lng: resolved.lng,
        label: "USER SITE",
        site_form: $("site-form").value,
        source: "user_address",
        captured_at: new Date().toISOString(),
        geocode: {
          accuracy_type: resolved.accuracy_type,
          parcel_grade: resolved.parcel_grade,
          provider: resolved.provider,
          source: resolved.source,
        },
      });
      keepNewSite(id);
    } else if (existing.source !== "user_address") {
      extras.unshift({
        ...existing,
        name: resolved.normalized_address || address,
        address,
        label: "USER SITE",
        source: "user_address",
        geocode: {
          accuracy_type: resolved.accuracy_type,
          parcel_grade: resolved.parcel_grade,
          provider: resolved.provider,
          source: resolved.source,
        },
      });
      keepNewSite(id);
    }
    $("address-status").textContent = `Resolved ${resolved.accuracy_type} · USER SITE. Ready to screen by coordinate.`;
    if (!silent) {
      renderCards();
      renderCompare();
      applyMode("street");
      selectSite(id, { fly: true });
      prefetchAerial(findSite(id));
      refreshCredits();
    }
    return true;
  } finally {
    $("resolve-address").disabled = false;
  }
}

function renderPins() {
  if (!viewer) return;
  pinEntities.forEach((e) => viewer.entities.remove(e));
  pinEntities = [];
  activeSites().forEach((c) => {
    const prior = packets[c.id];
    const passed = passedIds.has(c.id);
    const color = prior
      ? prior.verdict.verdict === "reject"
        ? "#d4654d"
        : prior.verdict.verdict === "strong_fit"
          ? "#6fbf8a"
          : "#d4a04a"
      : passed ? "#8aa0b4" : "#ece8e0";
    pinEntities.push(viewer.entities.add({
      id: "pin-" + c.id,
      position: Cesium.Cartesian3.fromDegrees(c.lng, c.lat, 8),
      point: {
        pixelSize: c.id === selectedId ? 16 : passed ? 8 : 11,
        color: Cesium.Color.fromCssColorString(color).withAlpha(passed ? 0.4 : 1),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: c.id === selectedId ? 3 : 1,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      label: {
        text: c.name,
        font: "11px Clash, sans-serif",
        fillColor: Cesium.Color.WHITE.withAlpha(passed ? 0.45 : 1),
        pixelOffset: new Cesium.Cartesian2(0, -20),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        show: c.id === selectedId,
      },
    }));
    if (c.id === selectedId) {
      pinEntities.push(viewer.entities.add({
        id: "pin-box-" + c.id,
        position: Cesium.Cartesian3.fromDegrees(c.lng, c.lat, 2),
        ellipse: {
          semiMajorAxis: 28,
          semiMinorAxis: 28,
          material: Cesium.Color.TRANSPARENT,
          outline: true,
          outlineColor: Cesium.Color.WHITE.withAlpha(0.85),
          outlineWidth: 2,
          height: 1,
        },
      }));
    }
  });
}

function flyToSites(sites, duration) {
  if (!viewer || !sites || !sites.length) return;
  if (sceneMode === "earth" || sceneMode === "orbit") return;
  if (sites.length === 1) {
    flyTo(sites[0], duration);
    return;
  }
  const points = sites.map((site) => Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 0));
  const sphere = Cesium.BoundingSphere.fromPoints(points);
  viewer.camera.flyToBoundingSphere(sphere, {
    duration: duration == null ? 1.4 : duration,
    offset: new Cesium.HeadingPitchRange(
      Cesium.Math.toRadians(28),
      Cesium.Math.toRadians(-48),
      Math.max(sphere.radius * 2.4, 120000)
    ),
  });
}

function flyTo(site, duration) {
  if (!viewer || !site) return;
  if (sceneMode === "earth") return;
  if (sceneMode === "orbit") {
    if (aerialVideoId(site, packets[site.id])) return;
    startPhotorealisticOrbit(site);
    return;
  }
  const cam = CAM[mission] || CAM.warehouse;
  const street = sceneMode === "street";
  const mesh = sceneMode === "mesh" || sceneMode === "future";
  const close = sceneMode === "pad";
  const range = street ? 88 : mesh ? 240 : close ? 165 : Math.min(cam.range, 220);
  const pitch = street ? -11 : mesh ? -24 : close ? -36 : -18;
  const heading = street ? 62 : mesh ? 48 : close ? 48 : cam.heading;
  const height = street ? 4 : mesh ? 10 : close ? 6 : (cam.height || 8);
  const center = Cesium.Cartesian3.fromDegrees(site.lng, site.lat, height);
  viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(center, street ? 28 : mesh ? 48 : close ? 48 : 40), {
    duration: duration == null ? 2.1 : duration,
    offset: new Cesium.HeadingPitchRange(
      Cesium.Math.toRadians(heading),
      Cesium.Math.toRadians(pitch),
      range
    ),
  });
}

function selectSite(id, opts) {
  selectedId = id;
  const site = findSite(id);
  if (!site) return;
  if (boardBeat === "scout") paintSelectionStage(site);
  if ($("status")) $("status").textContent = "";
  $("run-one").hidden = Boolean(packets[id]);
  renderCards();
  if (opts && opts.fly !== false && !["earth", "orbit"].includes(sceneMode)) flyTo(site, opts.duration);
  if (["past", "pad"].includes(sceneMode)) {
    renderQuickMap(site, sceneMode === "osm" ? "osm" : "aerial");
  } else {
    $("quick-map").classList.add("hidden");
  }
  if (sceneMode === "street") loadStreetView(site);
  if (sceneMode === "earth") presentEarthLook(site, packets[id]);
  if (sceneMode === "orbit") presentOrbit(site, packets[id]);
  prefetchAerial(site);
  refreshPlacement(site, packets[id]);
  const prior = packets[id];
  if (prior) showPacket(prior, { fly: false });
  else {
    loadSwipeFace(site);
    $("verdict").className = "verdict empty";
    $("verdict").textContent = `${site.label} · not screened yet.`;
    $("rail").innerHTML = "<li>idle</li>";
    $("gaps").innerHTML = "";
    if ($("scout-followups")) $("scout-followups").innerHTML = "";
    $("brief").innerHTML = "";
    $("scorecard").innerHTML = "";
    $("coverage").innerHTML = "";
    $("skeptic-stamp").hidden = true;
    if ($("fit-gap")) $("fit-gap").hidden = true;
    $("aerial-status").textContent = "Screen this site to check Aerial View.";
    $("play-aerial").hidden = true;
    paintPinCard(site, null);
  }
}

function isUserSite(site) {
  return Boolean(site && ["user_pin", "user_address"].includes(site.source));
}

function openRecommendations(reason) {
  if (entryPath !== "check") return;
  recommendMode = true;
  curatedSites().forEach((site) => {
    siteOrigin[site.id] = "recommendation";
    keepNewSite(site.id);
  });
  renderCards();
  renderCompare();
  const next = $("next-move");
  if (next) next.textContent = reason || "Other places to try. Not listings.";
  const hint = $("swipe-hint");
  if (hint) hint.textContent = "Other places to try. Right Keep · Left Pass. Not listings.";
  const deckHint = $("deck-hint");
  if (deckHint) deckHint.textContent = "Your pin stayed. These cards are other places that match the plan.";
  discoverPlaces().then((found) => {
    (found.candidates || []).forEach((site) => {
      if (extras.some((row) => row.id === site.id)) return;
      extras.push(site);
      siteOrigin[site.id] = "recommendation";
      keepNewSite(site.id);
    });
    renderCards();
    renderCompare();
  }).catch(() => {});
}

function verdictLine(packet) {
  const v = packet.verdict.verdict;
  const reasons = (packet.verdict.reasons || []).join(", ") || "no veto";
  if (v === "reject") return `Not a good idea · ${reasons}`;
  if (v === "conditional") return `Possible, with homework · ${reasons}`;
  if (v === "strong_fit") return `This works on the supported gates · ${reasons}`;
  return `${v.replace("_", " ")} · ${reasons}`;
}

function resetSwipe() {
  passedIds = new Set();
  swipeUndo = [];
  swipePhotoId = null;
  keptIds = new Set(activeSites().map((site) => site.id));
  syncSwipeActions();
}

function keepNewSite(id) {
  if (!id) return;
  keptIds.add(id);
  passedIds.delete(id);
}

function catalogKeptIds() {
  return activeSites()
    .filter((site) => !isUserSite(site) && keptIds.has(site.id) && !passedIds.has(site.id))
    .map((site) => site.id);
}

function nextOpenSite(fromId) {
  const sites = activeSites();
  const open = sites.filter((site) => !passedIds.has(site.id));
  if (!open.length) return null;
  const fromIndex = sites.findIndex((site) => site.id === fromId);
  for (let i = 1; i <= sites.length; i += 1) {
    const site = sites[(fromIndex + i) % sites.length];
    if (site && !passedIds.has(site.id) && site.id !== fromId) return site;
  }
  return open[0];
}

function swipeBusy() {
  return Boolean($("run-all") && $("run-all").disabled);
}

function passSite(id) {
  const site = findSite(id);
  if (!site || passedIds.has(id) || swipeBusy()) return;
  swipeUndo.push({
    type: "pass",
    id,
    wasKept: keptIds.has(id),
    selectedId,
  });
  passedIds.add(id);
  keptIds.delete(id);
  finishSwipeMove(nextOpenSite(id));
}

function keepSite(id) {
  const site = findSite(id);
  if (!site || swipeBusy()) return;
  swipeUndo.push({
    type: "keep",
    id,
    wasPassed: passedIds.has(id),
    wasKept: keptIds.has(id),
    selectedId,
  });
  keptIds.add(id);
  passedIds.delete(id);
  finishSwipeMove(nextOpenSite(id), site);
}

function finishSwipeMove(next, faceSite) {
  if (next) selectSite(next.id, { fly: false });
  else {
    renderCards();
    loadSwipeFace(faceSite || null);
  }
  const framed = activeSites();
  if (framed.length > 1 && !screenedCount()) flyToSites(framed, 0.7);
  else if (next) flyTo(next, 0.7);
}

function undoSwipe() {
  const last = swipeUndo.pop();
  if (!last) return;
  if (last.type === "pass") {
    passedIds.delete(last.id);
    if (last.wasKept) keptIds.add(last.id);
  } else if (last.type === "keep") {
    if (last.wasPassed) {
      passedIds.add(last.id);
      keptIds.delete(last.id);
    } else {
      passedIds.delete(last.id);
      if (last.wasKept) keptIds.add(last.id);
      else keptIds.delete(last.id);
    }
  }
  const restore = findSite(last.id) ? last.id : last.selectedId;
  finishSwipeMove(restore && findSite(restore) ? findSite(restore) : null);
}

function syncSwipeActions() {
  const open = activeSites().filter((site) => !passedIds.has(site.id));
  const hasFace = Boolean(selectedId && findSite(selectedId));
  const busy = swipeBusy();
  if ($("keep-site")) $("keep-site").disabled = !hasFace || busy;
  if ($("pass-site")) $("pass-site").disabled = !hasFace || busy || passedIds.has(selectedId);
  if ($("undo-swipe")) $("undo-swipe").disabled = !swipeUndo.length || busy;
  const hint = $("swipe-hint");
  if (!hint) return;
  if (!open.length) hint.textContent = "Pass fewer, or drop a pin / type an address.";
  else if (entryPath === "check" && recommendMode) hint.textContent = "Other places to try. Right Keep · Left Pass. Not listings.";
  else if (entryPath === "check") hint.textContent = "This is your pin. Screen it to see if it is a good idea.";
  else hint.textContent = "Right Keep · Left Pass. Does not screen. Pass is not a Reject.";
}

function searchRegionLabel() {
  const value = ($("search-region") && $("search-region").value) || "";
  return REGION_LABELS[value] || value.replace(/_/g, " ") || "Search region not set";
}

function siteFormLabel(site) {
  const form = (site && site.site_form) || "either";
  return SITE_FORM_LABELS[form] || form.replace(/_/g, " ");
}

function chipZoom() {
  if (mission === "warehouse" || mission === "home" || mission === "custom") return 18;
  return 16;
}

function contextChipUrl(site, mode) {
  const zoom = chipZoom();
  const scale = 2 ** zoom;
  const lat = Math.max(-85.05112878, Math.min(85.05112878, Number(site.lat)));
  const lng = Number(site.lng);
  const tileX = Math.floor(((lng + 180) / 360) * scale);
  const radians = lat * Math.PI / 180;
  const tileY = Math.floor((1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2 * scale);
  const wrappedX = ((tileX % scale) + scale) % scale;
  const y = Math.max(0, Math.min(scale - 1, tileY));
  if (mode === "aerial" && config.has_google_tiles) {
    return config.satellite.replace("{z}", String(zoom)).replace("{x}", String(wrappedX)).replace("{y}", String(y));
  }
  return `https://tile.openstreetmap.org/${zoom}/${wrappedX}/${y}.png`;
}

async function streetMetaFor(site) {
  const key = `${Number(site.lat).toFixed(5)},${Number(site.lng).toFixed(5)}`;
  if (streetCache[key]) return streetCache[key];
  if (!streetRequests[key]) {
    streetRequests[key] = (async () => {
      try {
        const res = await apiFetch(`/api/street-meta?lat=${site.lat}&lng=${site.lng}`);
        streetCache[key] = await res.json();
      } catch (err) {
        streetCache[key] = { available: false, status: "FAILED" };
      } finally {
        delete streetRequests[key];
      }
      return streetCache[key];
    })();
  }
  return streetRequests[key];
}

function streetHeadingFor(site, meta) {
  if (!site || !meta || meta.lat == null || meta.lng == null) return Number((meta && meta.heading) || 70);
  const lat1 = Number(meta.lat) * Math.PI / 180;
  const lat2 = Number(site.lat) * Math.PI / 180;
  const deltaLng = (Number(site.lng) - Number(meta.lng)) * Math.PI / 180;
  const y = Math.sin(deltaLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2)
    - Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLng);
  if (Math.abs(x) + Math.abs(y) < 0.000001) return Number(meta.heading || 70);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

function selectionSummary(site) {
  return `${searchRegionLabel()} · ${siteFormLabel(site)} · not screened`;
}

function setSelectionImage(site) {
  const image = $("selection-image");
  const credit = $("selection-credit");
  if (!image || !site) return;
  const token = ++selectionImageToken;
  image.alt = `${site.name} location context`;
  image.src = contextChipUrl(site, "aerial");
  image.dataset.source = config.has_google_tiles ? "satellite" : "map";
  if (credit) {
    credit.textContent = config.has_google_tiles
      ? "Satellite context · does not score"
      : "Map context · does not score";
  }
  streetMetaFor(site).then((meta) => {
    if (token !== selectionImageToken || !(meta && meta.available)) return;
    const candidate = new Image();
    candidate.alt = image.alt;
    candidate.onload = () => {
      if (token !== selectionImageToken) return;
      image.src = candidate.src;
      image.dataset.source = "street-view";
      if (credit) {
        credit.textContent = ["Google Street View", meta.date, "presentation only · does not score"]
          .filter(Boolean).join(" · ");
      }
    };
    candidate.src = streetImageSrc(site, meta, streetHeadingFor(site, meta));
  }).catch(() => {});
}

function paintSelectionStage(site) {
  if (!site) return;
  if ($("selection-label")) $("selection-label").textContent = site.label || "POTENTIAL";
  if ($("selection-name")) $("selection-name").textContent = site.name;
  if ($("selection-summary")) $("selection-summary").textContent = selectionSummary(site);
  if ($("examine-location")) $("examine-location").disabled = false;
  setSelectionImage(site);
}

function examineSelectedLocation() {
  const site = selectedId ? findSite(selectedId) : null;
  if (!site) return;
  setBoardBeat("screen");
  applyMode("street");
  selectSite(site.id, { fly: true, duration: 1.1 });
  logAction(`Examine ${site.name}. Screening waits until you ask.`);
}

function swipeMetaHtml(site) {
  const prior = packets[site.id];
  const screened = prior
    ? "Screened. See inspector."
    : "Not screened";
  const captured = site.captured_at ? String(site.captured_at).slice(0, 10) : "";
  const source = site.source ? String(site.source).replace(/_/g, " ") : "";
  const facts = [searchRegionLabel(), siteFormLabel(site), screened].filter(Boolean).join(" · ");
  const provenance = [source, captured ? `captured ${captured}` : ""].filter(Boolean).join(" · ");
  return (
    `<div class="label">${escapeHtml(site.label || "POTENTIAL")}</div>` +
    `<strong>${escapeHtml(site.name)}</strong>` +
    `<p>${escapeHtml(facts)}</p>` +
    (provenance ? `<p>${escapeHtml(provenance)}</p>` : "")
  );
}

function paintSwipeEmpty(face) {
  face.innerHTML = `<div class="swipe-empty">Pass fewer, or drop a pin / type an address.</div>`;
}

function loadSwipeFace(site) {
  const face = $("swipe-face");
  if (!face) return;
  const token = ++swipeFaceToken;
  if (!site) {
    swipePhotoId = null;
    paintSwipeEmpty(face);
    syncSwipeActions();
    return;
  }
  const open = activeSites().filter((row) => !passedIds.has(row.id));
  if (!open.length && passedIds.has(site.id)) {
    swipePhotoId = null;
    paintSwipeEmpty(face);
    syncSwipeActions();
    return;
  }
  if (swipePhotoId === site.id && face.querySelector("#swipe-photo img")) {
    const meta = face.querySelector(".swipe-meta");
    if (meta) meta.innerHTML = swipeMetaHtml(site);
    syncSwipeActions();
    return;
  }
  face.innerHTML =
    `<div class="swipe-photo" id="swipe-photo"></div>` +
    `<div class="swipe-meta">${swipeMetaHtml(site)}</div>`;
  syncSwipeActions();
  swipePhotoId = site.id;
  fillSwipePhoto(site, token);
}

function paintSwipeMissing(photo) {
  photo.className = "swipe-photo missing";
  photo.textContent = "No Street View or satellite chip at this pin.";
}

function fillSwipePhoto(site, token) {
  const photo = $("swipe-photo");
  if (!photo) return;
  paintSwipeChip(site, token, "aerial");
  streetMetaFor(site).then((meta) => {
    if (token !== swipeFaceToken || swipePhotoId !== site.id) return;
    if (!(meta && meta.available)) return;
    const img = document.createElement("img");
    img.alt = "";
    img.draggable = false;
    const show = () => {
      if (token !== swipeFaceToken || swipePhotoId !== site.id) return;
      const credit = document.createElement("span");
      credit.className = "swipe-credit";
      credit.textContent = "Street View · does not score";
      photo.className = "swipe-photo";
      photo.replaceChildren(img, credit);
    };
    img.addEventListener("load", show, { once: true });
    img.src = streetImageSrc(site, meta, streetHeadingFor(site, meta));
    if (img.complete && img.naturalWidth) show();
  });
}

function paintSwipeChip(site, token, mode) {
  const photo = $("swipe-photo");
  if (!photo || token !== swipeFaceToken) return;
  const img = document.createElement("img");
  img.alt = "";
  img.draggable = false;
  const show = () => {
    if (token !== swipeFaceToken) return;
    const credit = document.createElement("span");
    credit.className = "swipe-credit";
    credit.textContent = mode === "aerial"
      ? "Satellite · context only · does not score"
      : "OpenStreetMap · context only · does not score";
    photo.className = "swipe-photo";
    photo.replaceChildren(img, credit);
  };
  img.addEventListener("error", () => {
    if (token !== swipeFaceToken) return;
    if (mode === "aerial") paintSwipeChip(site, token, "osm");
    else paintSwipeMissing(photo);
  }, { once: true });
  img.addEventListener("load", show, { once: true });
  img.src = contextChipUrl(site, mode);
  if (img.complete && img.naturalWidth) show();
}

function bindSwipePointer() {
  const face = $("swipe-face");
  if (!face) return;
  face.addEventListener("pointerdown", (event) => {
    if (event.button && event.button !== 0) return;
    if (!selectedId || $("app").classList.contains("hidden")) return;
    swipeDrag = { x: event.clientX, id: selectedId, pointerId: event.pointerId };
    face.classList.add("dragging");
    try { face.setPointerCapture(event.pointerId); } catch (err) {}
  });
  face.addEventListener("pointermove", (event) => {
    if (!swipeDrag || swipeDrag.pointerId !== event.pointerId) return;
    const dx = event.clientX - swipeDrag.x;
    face.style.transform = `translateX(${dx}px) rotate(${dx / 28}deg)`;
  });
  const finish = (event) => {
    if (!swipeDrag || swipeDrag.pointerId !== event.pointerId) return;
    const dx = event.clientX - swipeDrag.x;
    const id = swipeDrag.id;
    swipeDrag = null;
    face.classList.remove("dragging");
    face.style.transform = "";
    try { face.releasePointerCapture(event.pointerId); } catch (err) {}
    if (dx > 72) keepSite(id);
    else if (dx < -72) passSite(id);
  };
  face.addEventListener("pointerup", finish);
  face.addEventListener("pointercancel", finish);
}

function renderCards() {
  const wrap = $("cards");
  wrap.innerHTML = "";
  activeSites().forEach((c) => {
    const prior = packets[c.id];
    const el = document.createElement("button");
    el.type = "button";
    const origin = siteOrigin[c.id] || (heldIds.has(c.id) ? "held" : "");
    const originLabel = origin === "replacement"
      ? "Brought in after a Reject"
      : origin === "held"
        ? "Held for lawful replacement"
        : origin === "recommendation"
          ? "Try this instead"
            : origin === "discovered"
            ? "POTENTIAL map feature"
            : "";
    const stamp = prior
      ? prior.verdict.verdict.replace("_", " ")
      : "not screened";
    const why = prior
      ? (prior.verdict.reasons || []).join(", ")
      : "";
    el.className = "card"
      + (prior ? " " + prior.verdict.verdict : "")
      + (c.id === selectedId ? " on" : "")
      + (origin ? " " + origin : "")
      + (passedIds.has(c.id) ? " passed" : "");
    el.dataset.id = c.id;
    const thumb = contextChipUrl(c, "aerial");
    el.innerHTML =
      `<img class="card-thumb" alt="" src="${escapeHtml(thumb)}">` +
      `<div class="label">${escapeHtml(c.label)}</div>` +
      `<strong>${escapeHtml(c.name)}</strong>` +
      `<div class="stamp">${escapeHtml(stamp)}</div>` +
      (passedIds.has(c.id) ? `<div class="gesture">Passed</div>` : "") +
      (originLabel ? `<div class="origin">${escapeHtml(originLabel)}</div>` : "") +
      (why ? `<div class="why">${escapeHtml(why)}</div>` : "");
    el.setAttribute("aria-pressed", c.id === selectedId ? "true" : "false");
    el.onclick = () => selectSite(c.id, { fly: true });
    wrap.appendChild(el);
    upgradeCardThumbnail(c, el);
  });
  renderPins();
  syncSwipeActions();
  syncWorkflow();
  const selected = selectedId ? findSite(selectedId) : null;
  const face = $("swipe-face");
  if (face && selected && $("swipe-photo")) {
    const meta = face.querySelector(".swipe-meta");
    if (meta) meta.innerHTML = swipeMetaHtml(selected);
  }
}

function upgradeCardThumbnail(site, card) {
  if (!card.querySelector(".card-thumb")) return;
  streetMetaFor(site).then((meta) => {
    if (!card.isConnected || card.dataset.id !== site.id || !(meta && meta.available)) return;
    const image = new Image();
    image.alt = "";
    image.onload = () => {
      if (!card.isConnected || card.dataset.id !== site.id) return;
      image.className = "card-thumb";
      image.dataset.source = "street-view";
      const old = card.querySelector(".card-thumb");
      if (old) old.replaceWith(image);
    };
    image.src = streetImageSrc(site, meta, streetHeadingFor(site, meta));
  }).catch(() => {});
}

function renderCompare() {
  const comparedIds = new Set((missionComparison || []).map((row) => row.candidate_id));
  const rows = missionComparison || activeSites().map((site) => {
    const packet = packets[site.id];
    return packet ? {
      candidate_id: site.id,
      name: site.name,
      label: site.label,
      verdict: packet.verdict.verdict,
      gap_count: (packet.verdict.gaps || []).filter((gap) => gap.blocking).length,
      route_times: [],
      counterfactual: "",
    } : { candidate_id: site.id, name: site.name, label: site.label };
  });
  const extraRows = missionComparison
    ? activeSites().filter((site) => !comparedIds.has(site.id)).map((site) => ({
        candidate_id: site.id, name: site.name, label: site.label,
      }))
    : [];
  $("compare-body").innerHTML = rows.concat(extraRows).map((row) => {
    const c = findSite(row.candidate_id) || row;
    const p = packets[c.id];
    if (!p || !row.verdict) return `<tr><td>${c.name}</td><td>${c.label}</td><td>—</td><td></td><td></td><td></td></tr>`;
    const route = (row.route_times || []).map((item) => `${item.anchor}: ${item.display}`).join(" · ") || "UNKNOWN";
    return `<tr>
      <td>${c.name}</td><td>${c.label}</td>
      <td>${row.verdict.replace("_", " ")}</td>
      <td>${row.gap_count}</td>
      <td>${route}</td>
      <td>${row.counterfactual || ""}</td>
    </tr>`;
  }).join("");
}

function clearDetail() {
  $("rail").innerHTML = "";
  $("verdict").className = "verdict empty";
  $("verdict").textContent = "Keep or Pass this pin. Screening waits until you ask.";
  $("gaps").innerHTML = "";
  if ($("scout-followups")) $("scout-followups").innerHTML = "";
  $("brief").innerHTML = "";
  $("skeptic-stamp").hidden = true;
  $("aerial-status").textContent = "Screen a site to check Aerial View.";
  $("play-aerial").hidden = true;
  $("scorecard").innerHTML = "";
  $("coverage").innerHTML = "";
  $("run-one").hidden = true;
  paintPinCard(null, null);
}

function showPacket(packet, opts) {
  packets[packet.candidate.id] = packet;
  selectedId = packet.candidate.id;
  $("rail").innerHTML = (packet.workstreams || [])
    .map((w) => {
      const id = w.id || "";
      return `<li data-workstream="${escapeHtml(id)}" data-status="${escapeHtml(w.status || "")}" data-phase="${escapeHtml(w.phase || "")}">${escapeHtml(workstreamLine(w))}</li>`;
    }).join("");
  const v = packet.verdict.verdict;
  const box = $("verdict");
  box.className = "verdict " + v;
  const demGap = (packet.verdict.gaps || []).find((g) => g.question_id === "hazards.elevation_disagreement");
  const extra = v === "reject" && demGap
    ? " · ground untrusted: 3DEP and NASADEM disagree"
    : "";
  box.textContent = `${verdictLine(packet)}${extra}`;
  if (entryPath === "check" && (v === "reject" || v === "conditional")) {
    openRecommendations(
      v === "reject"
        ? "Not a good idea for this plan. Other cards are places to try."
        : "Not a clean yes. Other cards are places you could try instead."
    );
  }
  const stamp = $("skeptic-stamp");
  if (packet.skeptic) {
    stamp.hidden = false;
    stamp.textContent = `${packet.skeptic.stamp} · ${packet.skeptic.model || "deterministic prechecks"} · ${(packet.skeptic.flags || []).join(", ")}`;
  } else {
    stamp.hidden = true;
  }
  $("gaps").innerHTML = (packet.verdict.gaps || [])
    .slice()
    .sort((a, b) => Number(HOMEWORK_GAPS.includes(b.question_id)) - Number(HOMEWORK_GAPS.includes(a.question_id)))
    .map((g) => {
      const q = GAP_QUESTIONS[g.question_id] || g.question_id;
      const homework = HOMEWORK_GAPS.includes(g.question_id) ? " homework" : "";
      const short = String(g.question_id || q).replace(/^hazards\./, "").replace(/_/g, " ");
      return `<li data-gap="${escapeHtml(g.question_id)}" class="${homework.trim()}" title="${escapeHtml(q)}">${escapeHtml(short)}</li>`;
    }).join("");
  const scoutAtom = (packet.atoms || []).find((atom) => atom.field_id === "official_followup_sources");
  const followups = (scoutAtom && scoutAtom.value && scoutAtom.value.followups) || [];
  const scoutList = $("scout-followups");
  if (scoutList) {
    scoutList.innerHTML = followups.map((row) => {
      const title = row.title || row.authority || "Official follow-up";
      const reason = row.reason || row.action || "Constrained official source. Not web discovery.";
      const href = row.url || (row.urls && row.urls[0]);
      const label = href
        ? `<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(title)}</a>`
        : escapeHtml(title);
      return `<li data-scout="${escapeHtml(row.id || "")}">${label} — ${escapeHtml(reason)}</li>`;
    }).join("");
  }
  const fitGap = $("fit-gap");
  if (fitGap) {
    const named = (packet.verdict.gaps || []).some((g) => g.question_id === "concept_fit");
    fitGap.hidden = !named;
  }
  const brief = packet.brief || {};
  const citations = (brief.citations || []).filter((citation) => citation && citation.source);
  $("brief").innerHTML =
    `<p>${brief.title || ""}</p>` +
    `<ol>${(brief.actions || []).map((a) => `<li>${a}</li>`).join("")}</ol>` +
    (citations.length
      ? `<h3>Sources</h3><ul>${citations.map((citation) => {
          const fetched = citation.fetched_at ? new Date(citation.fetched_at).toLocaleString() : "time unavailable";
          const role = citation.authority || "authority unknown";
          const mode = citation.live_label || "mode unknown";
          const label = `${citation.source}${citation.dataset_vintage ? ` · ${citation.dataset_vintage}` : ""}`;
          return `<li>${citation.source_url ? `<a href="${citation.source_url}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>` : escapeHtml(label)}<br><small>${escapeHtml(role)} · ${escapeHtml(mode)} · fetched ${escapeHtml(fetched)}</small></li>`;
        }).join("")}</ul>`
      : "");
  $("scorecard").innerHTML = (packet.scorecard || [])
    .map((row) => {
      const meter = Number.isFinite(row.meter) ? row.meter : ({ fail: 100, pass: 100, inform: 55, unknown: 35 }[row.status] || 35);
      const tone = row.tone || row.status;
      return `<div class="meter-row" data-id="${escapeHtml(row.id)}" data-meter="${meter}" data-tone="${escapeHtml(tone)}">${escapeHtml(row.label)}${row.value ? ` · ${escapeHtml(row.value)}` : ""} <span class="status-text">${escapeHtml(row.status)}</span><div class="bar ${escapeHtml(tone)}" role="meter" aria-valuenow="${meter}" aria-valuemin="0" aria-valuemax="100" data-meter="${meter}"><i style="width:${meter}%"></i></div></div>`;
    }).join("");
  renderTodayScene(packet);
  syncEraButtons(packet);
  refreshPlacement(findSite(packet.candidate.id), packet);
  updateDemand(packet);
  updateAdvisory(findSite(packet.candidate.id), packet);
  paintLayers(findSite(packet.candidate.id), packet);
  syncFloodLayer(packet);
  const cov = packet.coverage || { ratio: 0, usable: 0, relevant: 0 };
  $("coverage").innerHTML =
    `<div class="cov"><i style="width:${Math.round(cov.ratio * 100)}%"></i></div>` +
    `<p class="hint">${cov.usable}/${cov.relevant} decision atoms · ${cov.note || ""}</p>`;
  $("run-one").hidden = true;
  renderCards();
  renderCompare();
  const shown = findSite(packet.candidate.id);
  if (shown) loadSwipeFace(shown);
  if (!opts || opts.fly !== false) flyTo(packet.candidate);
  refreshCredits();
  paintPinCard(shown || packet.candidate, packet);
}

function renderTodayScene(packet) {
  const scene = packet.today_scene || { state: "UNAVAILABLE" };
  const button = $("play-aerial");
  button.hidden = true;
  button.onclick = null;
  if (scene.state === "ACTIVE" && scene.video_id) {
    $("aerial-status").textContent = "ACTIVE Aerial View orbit at this pin.";
    button.hidden = false;
    button.onclick = () => {
      applyMode("orbit");
    };
    if (sceneMode === "orbit") playAerial(scene.video_id);
    return;
  }
  $("aerial-status").textContent = scene.note || "no Aerial orbit at this pin · Earth shows satellite until Google has a video";
}

function normalizeAerialUri(raw) {
  if (typeof raw === "string") return raw;
  return (raw && (raw.landscapeUri || raw.uri || raw.url || raw.value)) || "";
}

function aerialUriExpireAt(uri) {
  try {
    const expire = Number(new URL(uri).searchParams.get("expire"));
    if (expire) return expire * 1000;
  } catch (err) {}
  return Date.now() + 20 * 60 * 1000;
}

async function fetchAerialUri(videoId, refresh) {
  const cached = aerialUriCache[videoId];
  if (!refresh && cached && cached.expireAt - Date.now() > 120 * 1000) return { uri: cached.uri, error: null };
  const res = await apiFetch(`/api/aerial-play?video_id=${encodeURIComponent(videoId)}${refresh ? "&refresh=1" : ""}`);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) return { uri: "", error: payload.error || "Aerial playback unavailable." };
  const uri = normalizeAerialUri(payload.uri);
  if (!uri) return { uri: "", error: "Aerial playback URI unavailable." };
  aerialUriCache[videoId] = { uri, expireAt: aerialUriExpireAt(uri) };
  return { uri, error: null };
}

async function warmAerial(videoId) {
  if (!videoId) return;
  let uri = "";
  try {
    uri = (await fetchAerialUri(videoId)).uri;
  } catch (err) {
    return;
  }
  const video = $("aerial-video");
  // Buffer ahead only while the stage is idle so a playing orbit is never interrupted.
  if (!uri || !video || aerialPlayId || !$("video-panel").hidden) return;
  video.muted = true;
  video.preload = "auto";
  if (video.src !== uri) {
    video.src = uri;
    video.load();
  }
}

async function playAerial(videoId, opts, refresh) {
  aerialPlayId = videoId;
  aerialPlayOpts = opts || null;
  aerialRefreshing = true;
  $("aerial-status").textContent = "Loading signed Aerial playback…";
  try {
    const { uri, error } = await fetchAerialUri(videoId, refresh);
    if (!uri) {
      $("aerial-status").textContent = error || "Aerial playback unavailable.";
      return false;
    }
    if (!["earth", "orbit"].includes(sceneMode)) return false;
    const video = $("aerial-video");
    const credit = $("aerial-credit");
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    if (video.src !== uri) video.src = uri;
    try {
      await video.play();
    } catch (err) {
      closeAerial({ silent: true });
      $("aerial-status").textContent = "Aerial playback blocked.";
      return false;
    }
    if (video.paused || video.readyState < 2) {
      closeAerial({ silent: true });
      $("aerial-status").textContent = "Aerial playback did not start.";
      return false;
    }
    hideStreetStage();
    hideEarthStage();
    $("video-panel").hidden = false;
    if (credit) {
      credit.textContent = "Aerial View is presentation only. It does not score.";
    }
    aerialRetry = 0;
    scheduleAerialRefresh(uri);
    $("aerial-status").textContent = "Aerial orbit playing · presentation only";
    return true;
  } catch (err) {
    closeAerial({ silent: true });
    $("aerial-status").textContent = "Aerial playback unavailable.";
    return false;
  } finally {
    aerialRefreshing = false;
  }
}

function aerialExpireWaitMs(uri) {
  try {
    const expire = Number(new URL(uri).searchParams.get("expire"));
    if (!expire) return 20 * 60 * 1000;
    return Math.max(8000, expire * 1000 - Date.now() - 90 * 1000);
  } catch (err) {
    return 20 * 60 * 1000;
  }
}

function scheduleAerialRefresh(uri) {
  if (aerialRefreshTimer) clearTimeout(aerialRefreshTimer);
  const videoId = aerialPlayId;
  const opts = aerialPlayOpts;
  aerialRefreshTimer = setTimeout(() => {
    if (!["earth", "orbit"].includes(sceneMode)) return;
    if (aerialPlayId !== videoId) return;
    playAerial(videoId, opts, true);
  }, aerialExpireWaitMs(uri));
}

function onAerialError() {
  if (aerialRefreshing) return;
  if (!["earth", "orbit"].includes(sceneMode) || !aerialPlayId) return;
  if (aerialRetry >= 2) {
    $("aerial-status").textContent = "Aerial playback expired. Click Earth to retry.";
    $("status").textContent = "Aerial link expired. Click Earth for a fresh orbit.";
    return;
  }
  aerialRetry += 1;
  $("status").textContent = "Aerial link expired — fetching a fresh orbit…";
  playAerial(aerialPlayId, aerialPlayOpts, true);
}

function closeAerial(opts) {
  if (aerialRefreshTimer) clearTimeout(aerialRefreshTimer);
  aerialRefreshTimer = null;
  if (!(opts && opts.keepId)) aerialPlayId = null;
  const video = $("aerial-video");
  if (!video) return;
  video.pause();
  if (!(opts && opts.keepSrc)) {
    video.removeAttribute("src");
    video.load();
  }
  $("video-panel").hidden = true;
}

async function runOne(candidateId) {
  if ($("run-one").disabled || $("run-all").disabled) return;
  const site = findSite(candidateId);
  $("rail").innerHTML = "<li>running…</li>";
  $("status").textContent = `Screening ${site ? site.name : candidateId}…`;
  const runControls = controls();
  if (!runControls) return;
  $("run-one").disabled = true;
  $("run-all").disabled = true;
  setBoardBeat("screen");
  syncSwipeActions();
  const body = {
    mission,
    manifest_id: runControls.manifest_id,
    candidate_id: candidateId,
    live: $("live").checked,
    review: $("review").checked,
    controls: runControls,
  };
  if (site && ["user_pin", "user_address", "openstreetmap"].includes(site.source)) body.candidate = site;
  try {
    const res = await apiFetch("/api/run-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let packet = null;
    try {
      await consumeNdjson(res, (event) => {
        noteWorkstream(event);
        if (event.event === "packet") packet = event.packet;
      });
    } catch (err) {
      $("status").textContent = "";
      $("verdict").className = "verdict reject";
      $("verdict").textContent = err.message || "run failed";
      const code = (err.payload && err.payload.error) || err.message || "failed";
      $("rail").innerHTML = `<li>failed · ${escapeHtml(code)}</li>`;
      openRecommendations("We could not finish this pin. Other cards are places you can try now.");
      return;
    }
    $("status").textContent = "";
    if (!packet) {
      $("verdict").className = "verdict reject";
      $("verdict").textContent = "run failed";
      $("rail").innerHTML = "<li>failed · empty stream</li>";
      openRecommendations("We could not finish this pin. Other cards are places you can try now.");
      return;
    }
    showPacket(packet);
    setBoardBeat("compare");
  } finally {
    $("run-one").disabled = false;
    $("run-all").disabled = false;
    if (!packets[candidateId] && boardBeat === "screen") setBoardBeat("scout");
    syncSwipeActions();
    syncWorkflow();
  }
}

async function runExpedition() {
  if ($("run-all").disabled || $("run-one").disabled) return;
  const runControls = controls();
  if (!runControls) return;
  const keptCatalog = catalogKeptIds();
  const extrasKept = extras.filter((site) => keptIds.has(site.id) && !passedIds.has(site.id));
  const siteCount = passedIds.size ? keptCatalog.length : activeSites().filter((site) => !isUserSite(site)).length;
  $("rail").innerHTML = `<li>expedition · ${siteCount} Candidate Sites in this Search Region</li>`;
  $("status").textContent = `Running ${mission.replace("_", " ")} Expedition…`;
  renderExpeditionLog([]);
  logAction("Expedition started. Screening first, then deepening survivors.");
  if (extrasKept.length) {
    logAction(`${extrasKept.length} USER SITE kept. Run All does not screen those. Use Screen this site.`);
  }
  $("run-all").disabled = true;
  $("run-one").disabled = true;
  setBoardBeat("screen");
  syncSwipeActions();
  try {
    const body = {
      mission,
      manifest_id: runControls.manifest_id,
      live: $("live").checked,
      review: $("review").checked,
      controls: runControls,
    };
    if (passedIds.size) {
      body.candidate_ids = keptCatalog;
    } else if (intentOpenGeography || regionAllowlist.length) {
      // Screen only the pins the dock shows, so no verdict lands on a pin
      // the geography filter hid.
      const visible = curatedSites().map((site) => site.id);
      if (visible.length) body.candidate_ids = visible;
    }
    const res = await apiFetch("/api/expedition-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let result = null;
    try {
      await consumeNdjson(res, (event) => {
        noteWorkstream(event);
        if (event.event === "pool") {
          waveIds = new Set(event.active || []);
          heldIds = new Set(event.held || []);
          (event.active || []).forEach((id) => { siteOrigin[id] = "initial"; });
          (event.held || []).forEach((id) => { siteOrigin[id] = "held"; });
          renderCards();
          const heldNames = (event.held || []).map(siteName).join(", ");
          logAction(
            heldNames
              ? `First wave: ${(event.active || []).map(siteName).join(", ")}. Held for replacement: ${heldNames}.`
              : `First wave: ${(event.active || []).map(siteName).join(", ")}.`
          );
        }
        if (event.event === "candidate_change") {
          if (event.status === "replaced" || event.status === "widened") {
            const incoming = event.candidate || {};
            const id = incoming.id;
            if (id) {
              heldIds.delete(id);
              if (waveIds) waveIds.add(id);
              siteOrigin[id] = "replacement";
              keepNewSite(id);
              if (!catalog.some((row) => row.id === id) && incoming.lat != null) {
                extras.push({
                  id,
                  name: incoming.name,
                  lat: incoming.lat,
                  lng: incoming.lng,
                  label: incoming.label || "POTENTIAL",
                  site_form: incoming.site_form || "either",
                  source: incoming.source || "curated_research_pin",
                });
              }
            }
            renderCards();
            logAction(`Rejected ${siteName(event.rejected_candidate_id)} · brought in ${incoming.name || id}.`);
          } else if (event.rejected_candidate_id) {
            logAction(`Rejected ${siteName(event.rejected_candidate_id)} · ${event.reason || event.status}`);
          }
        }
        if (event.event === "site_packet" && event.packet) {
          packets[event.packet.candidate.id] = event.packet;
          renderCards();
          if (event.packet.candidate.id === selectedId) showPacket(event.packet, { fly: false });
        }
        if (event.event === "packet") result = event.packet;
      });
    } catch (err) {
      $("status").textContent = err.message || "Expedition failed.";
      $("rail").innerHTML = `<li>failed · ${escapeHtml((err.payload && err.payload.error) || err.message)}</li>`;
      return;
    }
    if (!result) {
      $("status").textContent = "Expedition failed.";
      $("rail").innerHTML = "<li>failed · empty stream</li>";
      return;
    }
    missionComparison = result.comparison || [];
    screenedIds = new Set((result.results || []).map((packet) => packet.candidate.id));
    waveIds = null;
    (result.results || []).forEach((packet) => { packets[packet.candidate.id] = packet; });
    renderCards();
    renderCompare();
    const selected = pickPlanningSite(result.results) || packets[selectedId] || (result.results || [])[0];
    if (selected) {
      showPacket(selected, { fly: true });
      const past = selected.scene && selected.scene.past;
      if (mission === "farm" && past && past.kind && past.kind !== "none") applyMode("past");
    }
    writeExpeditionStory(result.results || []);
    const changes = (result.candidate_changes || []).filter((item) => item.status !== "initial");
    const summary = changes.map((item) => {
      if (item.status === "excluded") return `${item.candidate_id} excluded · ${item.reason}`;
      if (item.candidate) return `${item.rejected_candidate_id} rejected · ${item.status} with ${item.candidate.name}`;
      return `${item.rejected_candidate_id} rejected · lawful candidate pool exhausted at ${item.active_band_id}`;
    }).join(" · ");
    $("status").textContent = summary || "Expedition complete. TODAY is the site. FUTURE is a sketch, not a permit.";
    setBoardBeat("compare");
  } finally {
    $("run-all").disabled = false;
    $("run-one").disabled = false;
    if (!screenedCount() && boardBeat === "screen") setBoardBeat("scout");
    else if (screenedCount() && boardBeat === "screen") setBoardBeat("compare");
    syncSwipeActions();
    syncWorkflow();
  }
}

async function refreshCredits() {
  const c = await (await apiFetch("/api/credits")).json();
  $("credits").textContent = `${c.used_this_build} / ${c.soft_cap} credits`;
}

function writeExpeditionStory(results) {
  const story = $("story");
  if (!story) return;
  const list = Array.isArray(results) ? results : [];
  if (mission === "warehouse") {
    const sanLeon = list.find((packet) => packet.candidate && packet.candidate.id === "san_leon");
    const sanMarcos = list.find((packet) => packet.candidate && packet.candidate.id === "san_marcos_tx");
    const bits = [];
    if (sanLeon && sanLeon.verdict && sanLeon.verdict.verdict === "reject") {
      bits.push("San Leon Reject · FEMA mapped floodplain");
    }
    if (sanMarcos && sanMarcos.verdict && sanMarcos.verdict.verdict === "conditional") {
      bits.push("San Marcos Conditional · sale, power, trucking, zoning still homework");
    }
    if (missionHasConcept()) bits.push("FUTURE sketch is unlocked");
    story.textContent = bits.join(". ");
    return;
  }
  const rejects = list.filter((packet) => packet.verdict && packet.verdict.verdict === "reject");
  const conditionals = list.filter((packet) => packet.verdict && packet.verdict.verdict === "conditional");
  story.textContent = [
    rejects.length ? `${rejects.map((packet) => packet.candidate.name).join(", ")} Reject` : "",
    conditionals.length ? `${conditionals.map((packet) => packet.candidate.name).join(", ")} Conditional` : "",
  ].filter(Boolean).join(". ");
}

function bindLookSwitcher() {
  if ($("look-switcher")) $("look-switcher").hidden = true;
}

function stepLook() {}

function applyLook() {
  if ($("look-switcher")) $("look-switcher").hidden = true;
  if ($("demand")) $("demand").hidden = true;
  if ($("advisory")) $("advisory").hidden = true;
}

async function loadStreetView(site) {
  if (!site) return;
  const meta = await streetMetaFor(site);
  if (sceneMode !== "street") return;
  if (meta && meta.available) {
    $("street-stage").hidden = false;
    $("sv-heading").value = String(Math.round(streetHeadingFor(site, meta)));
    $("street-credit").textContent = [meta.copyright, meta.date, "Street View · does not score"].filter(Boolean).join(" · ");
    paintStreetImage(site);
    $("status").textContent = "";
    $("context-tag").textContent = "Google Street View — presentation only. Does not score.";
  } else {
    hideStreetStage();
    ensureTileset();
    if (tileset) tileset.show = meshTilesReady();
    $("status").textContent = "No Street View at this pin. Street-height 3D — presentation only.";
    $("context-tag").textContent = "No Street View at this pin. Street-height 3D — presentation only. Does not score.";
    if (site) flyTo(site, 0.6);
  }
  updateAdvisory(site, packets[site.id]);
}

function streetImageSrc(site, meta, heading) {
  const lat = (meta && meta.lat != null) ? meta.lat : site.lat;
  const lng = (meta && meta.lng != null) ? meta.lng : site.lng;
  const h = heading != null ? heading : ((meta && meta.heading) || 70);
  const pano = meta && meta.pano_id ? `&pano=${encodeURIComponent(meta.pano_id)}` : "";
  return `/sv?lat=${lat}&lng=${lng}&heading=${h}${pano}`;
}

function paintStreetImage(site) {
  const key = `${Number(site.lat).toFixed(5)},${Number(site.lng).toFixed(5)}`;
  const meta = streetCache[key] || {};
  const heading = Number($("sv-heading").value) || meta.heading || 70;
  $("street-image").src = streetImageSrc(site, meta, heading);
}

function hideStreetStage() {
  stopStreetSpin();
  $("street-stage").hidden = true;
}

function startStreetSpin(site) {
  stopStreetSpin();
  streetSpin = setInterval(() => {
    if (sceneMode !== "street" || !site) return;
    const input = $("sv-heading");
    input.value = String((Number(input.value) + 8) % 360);
    paintStreetImage(site);
  }, 900);
}

function stopStreetSpin() {
  if (streetSpin) clearInterval(streetSpin);
  streetSpin = null;
}

function aerialVideoId(site, packet) {
  const scene = packet && packet.today_scene;
  if (scene && scene.state === "ACTIVE" && scene.video_id) return scene.video_id;
  const cached = site && aerialCache[site.id];
  if (cached && cached.state === "ACTIVE" && cached.video_id) return cached.video_id;
  return null;
}

async function prefetchAerial(site) {
  if (!site) return null;
  const known = aerialCache[site.id];
  if (known && known.state === "ACTIVE") {
    warmAerial(known.video_id);
    return known;
  }
  try {
    const meta = await fetchAerialEnsure(site, false);
    aerialCache[site.id] = meta;
    if (meta.query && !site.address) site.address = meta.query;
    if (meta.state === "ACTIVE" && meta.video_id) warmAerial(meta.video_id);
  } catch (err) {
    aerialCache[site.id] = { state: "FAILED", video_id: null };
  }
  return aerialCache[site.id];
}

function hideEarthSky() {
  if (!viewer) return;
  viewer.scene.backgroundColor = Cesium.Color.BLACK;
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#0c0d0e");
  viewer.scene.fog.enabled = false;
  if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = false;
  if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;
}

function hideEarthStage() {
  stopEarthPoll();
  if (earthSpin) clearInterval(earthSpin);
  earthSpin = null;
  const stage = $("earth-stage");
  if (stage) stage.hidden = true;
}

function showEarthGlobe(site) {
  hideStreetStage();
  $("quick-map").classList.add("hidden");
  if (tileset) tileset.show = false;
  if (viewer) {
    hideEarthSky();
    viewer.scene.globe.show = false;
    viewer.imageryLayers.removeAll();
  }
  const stage = $("earth-stage");
  if (!stage) return;
  stage.hidden = false;
  if (site) {
    renderEarthGround(site);
    startEarthOrbit(site);
  }
}

function renderEarthGround(site) {
  const map = $("earth-ground");
  if (!map || !site) return;
  const renderId = ++earthRender;
  map.replaceChildren();
  const zoom = 17;
  const cols = 7;
  const rows = 7;
  const scale = 2 ** zoom;
  const lat = Math.max(-85.05112878, Math.min(85.05112878, Number(site.lat)));
  const lng = Number(site.lng);
  const worldX = ((lng + 180) / 360) * scale * 256;
  const radians = lat * Math.PI / 180;
  const worldY = (1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2 * scale * 256;
  const width = cols * 256;
  const height = rows * 256;
  const minX = Math.floor(worldX / 256) - Math.floor(cols / 2);
  const minY = Math.max(0, Math.floor(worldY / 256) - Math.floor(rows / 2));
  const originX = worldX - width / 2;
  const originY = worldY - height / 2;
  let loaded = 0;
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const x = minX + col;
      const y = minY + row;
      const wrappedX = ((x % scale) + scale) % scale;
      const tile = document.createElement("img");
      tile.alt = "";
      tile.draggable = false;
      tile.decoding = "async";
      tile.style.left = `${x * 256 - originX}px`;
      tile.style.top = `${y * 256 - originY}px`;
      tile.src = config.has_google_tiles && config.satellite
        ? config.satellite.replace("{z}", zoom).replace("{x}", wrappedX).replace("{y}", y)
        : `https://tile.openstreetmap.org/${zoom}/${wrappedX}/${y}.png`;
      tile.addEventListener("load", () => {
        if (renderId !== earthRender) return;
        loaded += 1;
        tile.dataset.loaded = "true";
        if (loaded === 1) map.dataset.ready = "true";
      }, { once: true });
      map.appendChild(tile);
    }
  }
  const pin = document.createElement("span");
  pin.className = "quick-map-pin";
  pin.setAttribute("aria-hidden", "true");
  map.appendChild(pin);
}

function aerialQuery(site) {
  return ((site && site.address) || "").trim();
}

function hasHouseAddress(site) {
  return /^\d+\s+\S+/.test(aerialQuery(site));
}

async function fetchAerialMeta(query, videoId) {
  const params = videoId
    ? `video_id=${encodeURIComponent(videoId)}`
    : `query=${encodeURIComponent(query)}`;
  const res = await apiFetch(`/api/aerial-meta?${params}`);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) return { state: "FAILED", video_id: null, query: query || videoId };
  return payload;
}

async function fetchAerialEnsure(site, render) {
  const res = await apiFetch("/api/aerial-ensure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      address: aerialQuery(site),
      lat: site && site.lat,
      lng: site && site.lng,
      render: Boolean(render),
    }),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) return { state: "FAILED", video_id: null, query: aerialQuery(site) };
  return payload;
}

function stopEarthPoll() {
  if (earthPollTimer) clearTimeout(earthPollTimer);
  earthPollTimer = null;
}

function presentEarthLook(site, packet) {
  const seq = ++earthLookSeq;
  stopEarthPoll();
  hideStreetStage();
  // keepSrc: a prefetch may have buffered this pin's orbit already.
  closeAerial({ silent: true, keepSrc: true });
  if (!site) {
    hideEarthStage();
    $("context-tag").textContent = "Pick a pin. Earth shows that place.";
    $("status").textContent = "";
    return;
  }
  startPhotorealisticOrbit(site);
  $("context-tag").textContent = "Photorealistic 3D of this pin. Aerial View plays if Google has a street address. Does not score.";
  $("status").textContent = "";
  const localId = aerialVideoId(site, packet);
  if (localId) {
    playAerial(localId).then((ok) => {
      if (seq !== earthLookSeq || sceneMode !== "earth") return;
      if (!ok) {
        startPhotorealisticOrbit(site);
        $("context-tag").textContent = "Photorealistic 3D of this pin. Does not score.";
        $("status").textContent = "";
      } else {
        $("context-tag").textContent = "Aerial View orbit of this pin. Does not score.";
        $("status").textContent = "";
      }
    });
    return;
  }
  // No street address is fine: the server reverse-geocodes the pin to one.
  runEarthPipeline(site, seq);
}

async function runEarthPipeline(site, seq) {
  $("status").textContent = "Looking up Aerial View for this pin…";
  try {
    const meta = await fetchAerialEnsure(site, true);
    if (seq !== earthLookSeq || sceneMode !== "earth") return;
    aerialCache[site.id] = meta;
    if (hasHouseAddress({ address: meta.query }) && !site.address) site.address = meta.query;
    if (meta.state === "ACTIVE" && meta.video_id) {
      const ok = await playAerial(meta.video_id);
      if (seq !== earthLookSeq || sceneMode !== "earth") return;
      if (!ok) {
        startPhotorealisticOrbit(site);
        $("context-tag").textContent = "Photorealistic 3D of this pin. Does not score.";
        $("status").textContent = "";
        return;
      }
      $("context-tag").textContent = "Aerial View orbit of this pin. Does not score.";
      $("status").textContent = "";
      return;
    }
    if (meta.state === "PROCESSING" && meta.video_id) {
      $("context-tag").textContent = "Photorealistic 3D while Google renders an Aerial clip for this pin. Does not score.";
      $("status").textContent = "Google is rendering an Aerial View clip — usually a few minutes. It plays here when ready.";
      pollEarthAerial(site, meta.video_id, seq, 0);
      return;
    }
    if (meta.state === "NO_ADDRESS") {
      $("context-tag").textContent = "Photorealistic 3D of this pin. No street address here for Aerial View. Does not score.";
      $("status").textContent = "";
      return;
    }
    $("context-tag").textContent = "Photorealistic 3D of this pin. No Aerial View here. Does not score.";
    $("status").textContent = "";
  } catch (err) {
    if (seq !== earthLookSeq || sceneMode !== "earth") return;
    startPhotorealisticOrbit(site);
    $("context-tag").textContent = "Photorealistic 3D of this pin. Does not score.";
    $("status").textContent = "";
  }
}

function pollEarthAerial(site, videoId, seq, attempt) {
  const waits = [4000, 6000, 8000, 12000, 15000, 20000, 20000,
    30000, 30000, 30000, 30000, 30000, 30000, 30000, 30000, 30000];
  if (attempt >= waits.length) {
    if (seq === earthLookSeq && sceneMode === "earth") {
      $("context-tag").textContent = "Photorealistic 3D of this pin. Aerial View is still rendering. Does not score.";
      $("status").textContent = "Aerial clip still rendering — it plays on the next Earth click once Google finishes.";
    }
    return;
  }
  stopEarthPoll();
  earthPollTimer = setTimeout(async () => {
    if (seq !== earthLookSeq || sceneMode !== "earth") return;
    try {
      const meta = await fetchAerialMeta("", videoId);
      if (seq !== earthLookSeq || sceneMode !== "earth") return;
      const prior = aerialCache[site.id] || {};
      aerialCache[site.id] = {
        ...meta,
        query: prior.query && prior.query.includes(" ") ? prior.query : meta.query,
      };
      if (meta.state === "ACTIVE" && meta.video_id) {
        const ok = await playAerial(meta.video_id);
        if (seq !== earthLookSeq || sceneMode !== "earth") return;
        if (!ok) {
          startPhotorealisticOrbit(site);
          $("context-tag").textContent = "Photorealistic 3D of this pin. Does not score.";
          $("status").textContent = "";
        } else {
          $("context-tag").textContent = "Aerial View orbit of this pin. Does not score.";
          $("status").textContent = "";
        }
        return;
      }
    } catch (err) {
      if (seq !== earthLookSeq || sceneMode !== "earth") return;
    }
    pollEarthAerial(site, videoId, seq, attempt + 1);
  }, waits[attempt]);
}

function presentOrbit(site, packet) {
  hideEarthStage();
  const videoId = aerialVideoId(site, packet);
  if (videoId) {
    if (tileset) tileset.show = false;
    applyMapBase("hidden");
    hideStreetStage();
    $("context-tag").textContent = "Aerial View orbit of this pin. Does not score.";
    $("status").textContent = "";
    playAerial(videoId).then((ok) => {
      if (ok || sceneMode !== "orbit") return;
      startPhotorealisticOrbit(site);
    });
    return;
  }
  if (site && !aerialCache[site.id]) {
    $("status").textContent = "Checking Aerial View for this pin…";
    prefetchAerial(site).then((meta) => {
      if (sceneMode !== "orbit") return;
      if (meta && meta.video_id) {
        presentOrbit(site, packets[site.id]);
        return;
      }
      startPhotorealisticOrbit(site);
    });
    return;
  }
  startPhotorealisticOrbit(site);
}

function startPhotorealisticOrbit(site) {
  hideEarthStage();
  hideStreetStage();
  if (!site) {
    $("context-tag").textContent = "Pick a pin. Earth shows that place.";
    return;
  }
  if (!viewer) {
    showEarthGlobe(site);
    $("context-tag").textContent = "Satellite of this pin. Context only. Does not score.";
    return;
  }
  ensureTileset();
  ensureGlobeImagery();
  if (tileset) tileset.show = meshTilesReady();
  if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = true;
  $("context-tag").textContent = "Photorealistic 3D of this pin. Aerial View plays if Google has one. Does not score.";
  const center = Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 8);
  let heading = Cesium.Math.toRadians(42);
  const pitch = Cesium.Math.toRadians(-28);
  const range = 280;
  const tick = () => {
    if (!["orbit", "earth"].includes(sceneMode)) return;
    heading += 0.0035;
    viewer.camera.lookAt(center, new Cesium.HeadingPitchRange(heading, pitch, range));
  };
  tick();
  if (orbitListener) {
    viewer.scene.preUpdate.removeEventListener(orbitListener);
  }
  orbitListener = tick;
  viewer.scene.preUpdate.addEventListener(orbitListener);
  revealPhotorealisticMesh();
}

function startEarthOrbit(site) {
  if (earthSpin) clearInterval(earthSpin);
  const ground = $("earth-ground");
  if (!ground || !site) return;
  let heading = 8;
  const tick = () => {
    if (!["earth", "orbit"].includes(sceneMode)) return;
    heading = (heading + 0.35) % 360;
    ground.style.setProperty("--earth-rot", `${heading}deg`);
  };
  tick();
  earthSpin = setInterval(tick, 80);
}

function stopOrbit() {
  if (viewer && orbitListener) {
    viewer.scene.preUpdate.removeEventListener(orbitListener);
  }
  orbitListener = null;
  if (earthSpin) clearInterval(earthSpin);
  earthSpin = null;
  if (viewer) viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
}

function toggleLayer(id) {
  layerOn[id] = !layerOn[id];
  document.querySelectorAll("#layer-rack .layer").forEach((btn) => {
    btn.classList.toggle("on", Boolean(layerOn[btn.dataset.layer]));
  });
  const site = selectedId ? findSite(selectedId) : null;
  const packet = selectedId ? packets[selectedId] : null;
  paintLayers(site, packet);
  paintPinCard(site, packet);
  if (id === "flood" && layerOn.flood && site) flyTo(site, 0.7);
}

function paintLayers(site, packet) {
  if (!viewer) return;
  layerEntities.forEach((entity) => viewer.entities.remove(entity));
  layerEntities = [];
  if (!site) return;
  const reasons = (packet && packet.verdict && packet.verdict.reasons) || [];
  if (layerOn.flood && reasons.includes("mapped_sfha")) {
    const flood = Cesium.Color.fromCssColorString("#3d8ec8");
    const ring = [
      site.lng - 0.012, site.lat - 0.008,
      site.lng + 0.014, site.lat - 0.006,
      site.lng + 0.011, site.lat + 0.010,
      site.lng - 0.004, site.lat + 0.012,
      site.lng - 0.014, site.lat + 0.003,
    ];
    layerEntities.push(viewer.entities.add({
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArray(ring),
        material: flood.withAlpha(0.42),
        outline: true,
        outlineColor: flood.withAlpha(0.95),
        height: 0,
        extrudedHeight: 180,
      },
    }));
    layerEntities.push(viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 24),
      ellipse: {
        semiMajorAxis: 520,
        semiMinorAxis: 400,
        material: flood.withAlpha(0.28),
        height: 8,
      },
      label: {
        text: "SFHA",
        font: "bold 14px sans-serif",
        fillColor: Cesium.Color.fromCssColorString("#c5e4f5"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0, -36),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    }));
  }
}

function updateDemand(packet) {
  const rows = (packet && packet.scorecard) || [];
  const byId = Object.fromEntries(rows.map((row) => [row.id, row]));
  const set = (id, status) => {
    const node = document.querySelector(`.demand-meter[data-id="${id}"] i`);
    if (!node) return;
    node.style.width = status === "fail" ? "100%" : status === "pass" ? "70%" : "35%";
    node.style.background = status === "fail" ? "#c24a3a" : status === "pass" ? "#3d8f62" : "#c48a2a";
  };
  set("flood", (byId.flood && byId.flood.status) || "unknown");
  set("power", (byId.capacity && byId.capacity.status) || "unknown");
  set("roads", rows.some((row) => String(row.id).startsWith("route") && row.status === "pass") ? "pass" : "unknown");
  set("gaps", packet && packet.verdict && packet.verdict.verdict === "reject" ? "fail" : "unknown");
}

function updateAdvisory(site, packet) {
  const banner = $("advisory");
  if (!banner) return;
  banner.hidden = true;
}

function syncFloodLayer(packet) {
  const reasons = (packet && packet.verdict && packet.verdict.reasons) || [];
  if (!reasons.includes("mapped_sfha")) {
    if ($("flood-expand") && !layerOn.flood) $("flood-expand").hidden = true;
    return;
  }
  document.querySelectorAll("#layer-rack .layer").forEach((btn) => {
    btn.classList.toggle("on", Boolean(layerOn[btn.dataset.layer]));
  });
  paintLayers(selectedId ? findSite(selectedId) : null, packet);
  showFloodExpand(packet);
}

$("auth-form").addEventListener("submit", unlock);
window.addEventListener("keydown", (event) => {
  if (!$("app") || $("app").classList.contains("hidden")) return;
  const tag = (event.target && event.target.tagName) || "";
  if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
  if (event.key === "ArrowRight") {
    event.preventDefault();
    keepSite(selectedId);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    passSite(selectedId);
  } else if (event.key === "u" || event.key === "U") {
    event.preventDefault();
    undoSwipe();
  }
});
window.addEventListener("resize", () => {
  if (viewer) viewer.resize();
  if (["past", "pad"].includes(sceneMode) && selectedId) {
    renderQuickMap(findSite(selectedId), sceneMode === "osm" ? "osm" : "aerial");
  }
});
boot().catch((error) => {
  if (!(error instanceof AuthenticationRequired)) {
    $("auth-status").textContent = "The board could not start. Check the server and retry.";
    showAuthGate();
    console.error(error);
  }
});
