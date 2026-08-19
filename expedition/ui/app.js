const TILES = [
  ["warehouse", "Warehouse / light industrial", "Planning board: PAST / PAD / FUTURE concept on the real site. Flood is a hard gate."],
  ["farm", "Farm", "Cultivated land required. Water right is never inferred."],
  ["home", "Home", "Functional constraints only. No demographic ranking."],
  ["data_center", "Data center", "Heat and grid context. Deliverable MW is never claimed."],
  ["custom", "Constrained Custom", "Choose one reviewed manifest. Arbitrary tools and sources are not allowed."],
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

const LOOKS = [
  { id: "A", name: "HUD overlay" },
  { id: "B", name: "Layer rack" },
  { id: "C", name: "Ops table" },
  { id: "D", name: "Cinema" },
  { id: "E", name: "Street inspector" },
];

/* Proven Aerial View orbit from uchicago-aerial-view.html — videoId may be stored; URI is fetched at play time. */
const UCHICAGO_AERIAL = {
  address: "5801 S Ellis Ave, Chicago, IL 60637",
  videoId: "KPvJfAwQnLollCjP2bks-y",
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
let pinEntities = [];
let padEntities = [];
let selectedId = null;
let packets = {};
let missionComparison = null;
let sceneMode = "earth";
let customManifests = [];
let planRequest = 0;
let screenedIds = null;
let heldIds = new Set();
let siteOrigin = {};
let waveIds = null;
let streetCache = {};
let aerialCache = {};
let aerialPlayId = null;
let aerialPlayOpts = null;
let aerialRefreshTimer = null;
let aerialRetry = 0;
let aerialRefreshing = false;
let orbitListener = null;
let streetSpin = null;
let earthSpin = null;
let earthRender = 0;
let activeLook = "A";
let layerOn = { site: true, flood: false, power: false, roads: false };
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
  $("replan").onclick = () => {
    if (tileset) tileset.show = false;
    if (viewer) viewer.useDefaultRenderLoop = false;
    $("app").classList.add("hidden");
    $("app").classList.remove("sim-view");
    $("look-switcher").hidden = true;
    $("onboard").classList.remove("hidden");
  };
  $("run-all").onclick = runExpedition;
  $("run-one").onclick = () => selectedId && runOne(selectedId);
  $("add-pin").onclick = addUserSite;
  $("resolve-address").onclick = addAddressSite;
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
  ].forEach((id) => { $(id).onchange = previewPlan; });
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
  bindLookSwitcher();
  refreshCredits();
  loadCustomManifests();
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
  previewPlan();
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
  if (mission !== "warehouse" && mission !== "custom") return true;
  const region = ($("search-region") && $("search-region").value) || "texas_triangle";
  const geo = ($("geography-band") && $("geography-band").value) || "selected_region";
  const rank = { selected: 0, adjacent: 1, statewide: 2 };
  const stop = { selected_region: 0, adjacent_regions: 1, statewide: 2 }[geo] ?? 0;
  const bands = WAREHOUSE_BANDS[region];
  if (!bands) return true;
  if (!(id in bands)) return false;
  return rank[bands[id]] <= stop;
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
  if (log.textContent.includes("Confirm the plan")) log.innerHTML = "";
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
    const n = (missionSites[mission] || []).length;
    const prefs = payload.preferences.filter((item) => item.weight !== "not_considered");
    $("plan-card").textContent =
      `${plan.mission} · ${plan.scan_budget} · ${plan.site_form}\n` +
      `Region: ${payload.search_region} · ${payload.geography_band} · ${payload.size_band} · ${payload.budget_band}\n` +
      `Hard: ${plan.hard_constraints.join(", ") || "none"}\n` +
      `Preferences: ${prefs.map((item) => `${item.id} (${item.weight})`).join(", ") || "none"}\n` +
      `Optional: ${payload.optional_investigations.join(", ") || "none"}\n` +
      `Route anchors: ${payload.route_anchors.length}${payload.manifest_id ? ` · manifest ${payload.manifest_id}` : ""}\n` +
      `Skills: ${plan.skills.join(", ")}\n` +
      `${n} curated/user Candidate Sites. No LISTED inventory.`;
    $("confirm").disabled = false;
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
  };
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
  $("onboard").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("look-switcher").hidden = false;
  $("mission-kicker").textContent = `${mission.replace("_", " ")} expedition`;
  $("plan-locked").textContent =
    `${plan.mission} · ${plan.scan_budget} · ${plan.hard_constraints.join(", ") || "no hard gates"}`;
  await ensureViewer();
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
  applyMode("earth");
  setTimeout(() => { if (viewer) viewer.resize(); }, 80);
  renderCards();
  renderCompare();
  clearDetail();
  renderExpeditionLog([]);
  const first = activeSites()[0];
  if (first) selectSite(first.id, { fly: true, duration: 0 });
  $("status").textContent = "This is TODAY. Run Expedition to reject, replace, and deepen.";
  refreshCredits();
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
  viewer.imageryLayers.removeAll();

  if (config.has_google_tiles) {
    $("status").textContent = "Loading street-level 3D…";
    $("mode-mesh").disabled = true;
    $("mode-mesh").title = "Checking photorealistic 3D availability…";
    tileset = viewer.scene.primitives.add(
      new Cesium.Cesium3DTileset({
        url: config.tileset,
        showCreditsOnScreen: true,
        show: true,
      })
    );
    tileset.tileVisible.addEventListener(() => {
      revealPhotorealisticMesh();
    });
    tileset.readyPromise
      .then(() => {
        $("mode-mesh").disabled = false;
        $("mode-mesh").title = "Photorealistic 3D — context only";
        if (selectedId && ["street", "mesh"].includes(sceneMode)) {
          flyTo(findSite(selectedId), 0.8);
        }
        if (selectedId && sceneMode === "earth" && $("video-panel").hidden) {
          presentEarthLook(findSite(selectedId), packets[selectedId]);
        }
        if (selectedId && sceneMode === "orbit") {
          presentOrbit(findSite(selectedId), packets[selectedId]);
        }
      })
      .catch(() => {
        $("mode-mesh").disabled = true;
        $("mode-mesh").title = "Photorealistic 3D is unavailable";
        $("status").textContent = "Photorealistic 3D is unavailable. Aerial View and Street View still play.";
      });
  } else {
    $("status").textContent = "No Map Tiles key — Street View if coverage exists.";
    $("mode-mesh").disabled = true;
    $("mode-aerial").disabled = true;
  }
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
  const need = sceneMode === "street" || sceneMode === "orbit" ? 8 : 80;
  return Number(stats.numberOfTilesWithContentReady || 0) >= need;
}

function revealPhotorealisticMesh() {
  if (!["street", "mesh"].includes(sceneMode) || !meshTilesReady()) return;
  meshContentReady = true;
  clearTimeout(meshLoadTimer);
  viewer.imageryLayers.removeAll();
  viewer.scene.globe.show = false;
  if (sceneMode !== "street") $("quick-map").classList.add("hidden");
  $("status").textContent = "";
  if (sceneMode === "mesh") {
    $("context-tag").textContent = "Google photorealistic 3D — context only. Does not score.";
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
  const interior = interiorOn() ? " · schematic interior" : "";
  el.textContent = `${pad.title || "Concept"} · ${pad.length_m}×${pad.width_m} m${interior} · assumption, not FIT`;
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
  if (!["pad", "future"].includes(sceneMode)) return;
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
  const futureLabel = interiorOn()
    ? `${(pad.title || "CONCEPT").toUpperCase()} · schematic interior · not a permit`
    : `${(pad.title || "CONCEPT").toUpperCase()} · not a permit`;
  padEntities.push(viewer.entities.add({
    position: Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 18),
    label: {
      text: sceneMode === "future" ? futureLabel : "ASSUMED PAD · not FIT",
      font: "14px Clash, sans-serif",
      fillColor: Cesium.Color.fromCssColorString("#ffe0cc"),
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
  if (sceneMode === "future" && interiorOn()) {
    (pad.interior || []).forEach((room) => {
      const west = -hw + (room.x || 0) * pad.width_m;
      const east = west + (room.w || 0) * pad.width_m;
      const north = hl - (room.y || 0) * pad.length_m;
      const south = north - (room.h || 0) * pad.length_m;
      const roomCorners = [
        enuPoint(site.lng, site.lat, west, south, heading),
        enuPoint(site.lng, site.lat, east, south, heading),
        enuPoint(site.lng, site.lat, east, north, heading),
        enuPoint(site.lng, site.lat, west, north, heading),
      ];
      padEntities.push(viewer.entities.add({
        polygon: {
          hierarchy: new Cesium.PolygonHierarchy(roomCorners),
          material: Cesium.Color.fromCssColorString("#7ec8e3").withAlpha(0.35),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString("#d7f3ff"),
          height: (pad.height_m || 10) + 0.4,
          extrudedHeight: (pad.height_m || 10) + 0.6,
        },
        position: enuPoint(
          site.lng,
          site.lat,
          (west + east) / 2,
          (north + south) / 2,
          heading
        ),
        label: {
          text: room.label || room.id,
          font: "11px Clash, sans-serif",
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          pixelOffset: new Cesium.Cartesian2(0, -8),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      }));
    });
  }
}

function refreshPlacement(site, packet) {
  if (!site) return;
  if (sceneMode === "future") placeConcept(site, packet);
  if (["pad", "future"].includes(sceneMode)) placeAssumedPad(site, packet && packet.scene, packet);
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
  $("app").classList.toggle("sim-view", ["pad", "future"].includes(mode));
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
  clearTimeout(meshLoadTimer);
  if (mode !== "future") clearConcept();
  if (!["pad", "future"].includes(mode)) clearPadEntities();
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
    if (tileset) tileset.show = true;
    applyMapBase("hidden");
    $("context-tag").textContent = "Street-level view — presentation only. Does not score.";
    $("status").textContent = "";
    if (site) {
      loadStreetView(site);
      flyTo(site, 0.8);
    }
    revealPhotorealisticMesh();
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "earth") {
    if (tileset) tileset.show = false;
    applyMapBase("hidden");
    presentEarthLook(site, packet);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "orbit") {
    presentOrbit(site, packet);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "mesh" && tileset) {
    tileset.show = true;
    applyMapBase("hidden");
    hideStreetStage();
    $("context-tag").textContent = "Google photorealistic 3D — context only. Does not score.";
    $("status").textContent = meshTilesReady() ? "" : "Loading 3D…";
    if (site) flyTo(site, 0.8);
    revealPhotorealisticMesh();
    meshLoadTimer = setTimeout(() => {
      if (sceneMode !== "mesh") return;
      if (!meshTilesReady()) {
        $("status").textContent = "3D tiles are still loading.";
        return;
      }
      $("status").textContent = "";
    }, 10000);
    updatePlacementClaim(packet);
    return;
  }
  if (mode === "future") {
    if (tileset) tileset.show = false;
    hideStreetStage();
    applyMapBase(config.has_google_tiles ? "aerial" : "osm");
    $("context-tag").textContent = "FUTURE visual concept — not a permit.";
    $("status").textContent = "";
    refreshPlacement(site, packet);
    if (site) flyTo(site, 0.4);
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

function placeConcept(site, packet) {
  if (!viewer || !site) return;
  clearConcept();
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
  const origin = Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 1.4);
  let modelMatrix = Cesium.Transforms.headingPitchRollToFixedFrame(origin, hpr);
  const scale = new Cesium.Cartesian3(
    ((pad && pad.width_m) || nativeW) / nativeW,
    ((pad && pad.height_m) || nativeH) / nativeH,
    ((pad && pad.length_m) || nativeL) / nativeL
  );
  modelMatrix = Cesium.Matrix4.multiply(modelMatrix, Cesium.Matrix4.fromScale(scale), new Cesium.Matrix4());
  conceptModel = viewer.scene.primitives.add(Cesium.Model.fromGltf({
    url,
    modelMatrix,
    scale: 1,
    minimumPixelSize: 160,
    maximumScale: 6,
    color: interiors ? Cesium.Color.WHITE : Cesium.Color.fromCssColorString("#ff6a12").withAlpha(1),
    colorBlendMode: interiors ? Cesium.ColorBlendMode.MIX : (studioUrl ? Cesium.ColorBlendMode.MIX : Cesium.ColorBlendMode.REPLACE),
    colorBlendAmount: interiors ? 0 : (studioUrl ? 0.12 : 1),
    silhouetteColor: Cesium.Color.fromCssColorString("#ffe6c8"),
    silhouetteSize: interiors ? 1.2 : 2.4,
  }));
  if (conceptModel && conceptModel.readyPromise) {
    conceptModel.readyPromise.then(() => {
      if (viewer && sceneMode === "future") viewer.scene.requestRender();
    }).catch(() => {});
  }
}

function pickPlanningSite(results) {
  const list = Array.isArray(results) ? results : [];
  return list.find((packet) => packet.verdict && packet.verdict.verdict !== "reject") || list[0] || null;
}

function activeSites() {
  const missionIds = missionSites[mission] || (mission === "custom" ? missionSites.warehouse : []) || [];
  const allow = new Set(missionIds);
  const extraIds = new Set(extras.map((site) => site.id));
  const candidates = catalog.filter((c) => allow.has(c.id) && !extraIds.has(c.id) && regionAllows(c.id)).concat(extras);
  if (waveIds) {
    return candidates.filter((candidate) => waveIds.has(candidate.id) || heldIds.has(candidate.id) || extraIds.has(candidate.id));
  }
  return screenedIds
    ? candidates.filter((candidate) => screenedIds.has(candidate.id) || extraIds.has(candidate.id))
    : candidates;
}

function findSite(id) {
  return activeSites().find((c) => c.id === id);
}

function addUserSite() {
  const lat = parseFloat($("pin-lat").value);
  const lng = parseFloat($("pin-lng").value);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    $("status").textContent = "Need a numeric lat and lng.";
    return;
  }
  if (lat < 18 || lat > 72 || lng < -180 || lng > -65) {
    $("status").textContent = "Pin is outside the US Mireye envelope.";
    return;
  }
  const id = `user_${lat.toFixed(5)}_${lng.toFixed(5)}`.replace(/[.-]/g, "m");
  if (findSite(id)) {
    selectSite(id, { fly: true });
    return;
  }
  extras.push({
    id,
    name: `User pin ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
    lat,
    lng,
    label: "USER SITE",
    site_form: $("site-form").value,
    source: "user_pin",
  });
  renderCards();
  renderCompare();
  selectSite(id, { fly: true });
}

async function addAddressSite() {
  if ($("resolve-address").disabled) return;
  const address = $("site-address").value.trim();
  if (!address) {
    $("address-status").textContent = "Enter a complete US street address.";
    return;
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
      $("address-status").textContent = resolved.message || resolved.error || "Address resolve failed.";
      return;
    }
    if (resolved.disposition !== "resolved") {
      const choices = (resolved.candidates || [])
        .map((candidate) => candidate.normalized_address || `${candidate.lat}, ${candidate.lng}`)
        .join(" / ");
      $("address-status").textContent = `${resolved.message || "Address needs clarification."}${choices ? ` Candidate: ${choices}` : ""}`;
      return;
    }
    const id = resolved.candidate_id || `address_${resolved.lat.toFixed(5)}_${resolved.lng.toFixed(5)}`.replace(/[.-]/g, "m");
    const existing = findSite(id);
    if (!existing) {
      extras.push({
        id,
        name: resolved.normalized_address || address,
        address,
        lat: resolved.lat,
        lng: resolved.lng,
        label: "USER SITE",
        site_form: $("site-form").value,
        source: "user_address",
        geocode: {
          accuracy_type: resolved.accuracy_type,
          parcel_grade: resolved.parcel_grade,
          provider: resolved.provider,
          source: resolved.source,
        },
      });
    } else if (existing.source !== "user_address") {
      extras.push({
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
    }
    $("address-status").textContent = `Resolved ${resolved.accuracy_type} · USER SITE. Ready to screen by coordinate.`;
    renderCards();
    renderCompare();
    applyMode("street");
    selectSite(id, { fly: true });
    prefetchAerial(findSite(id));
    refreshCredits();
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
    const color = prior
      ? prior.verdict.verdict === "reject"
        ? "#d4654d"
        : prior.verdict.verdict === "strong_fit"
          ? "#6fbf8a"
          : "#d4a04a"
      : "#ece8e0";
    pinEntities.push(viewer.entities.add({
      id: "pin-" + c.id,
      position: Cesium.Cartesian3.fromDegrees(c.lng, c.lat, 8),
      point: {
        pixelSize: c.id === selectedId ? 16 : 11,
        color: Cesium.Color.fromCssColorString(color),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 1,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      label: {
        text: c.name,
        font: "11px Clash, sans-serif",
        fillColor: Cesium.Color.WHITE,
        pixelOffset: new Cesium.Cartesian2(0, -20),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    }));
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
  const mesh = sceneMode === "mesh";
  const close = ["future", "pad"].includes(sceneMode);
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
  $("run-one").hidden = false;
  renderCards();
  if (opts && opts.fly !== false && !["earth", "orbit"].includes(sceneMode)) flyTo(site, opts.duration);
  if (["aerial", "osm", "past", "pad", "future"].includes(sceneMode)) {
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
    $("verdict").className = "verdict empty";
    $("verdict").textContent = `${site.label} · not screened`;
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
  }
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
        : "";
    el.className = "card"
      + (prior ? " " + prior.verdict.verdict : "")
      + (c.id === selectedId ? " on" : "")
      + (origin ? " " + origin : "");
    el.dataset.id = c.id;
    el.innerHTML = `<div class="label">${escapeHtml(c.label)}</div><strong>${escapeHtml(c.name)}</strong><div>${c.lat.toFixed(3)}, ${c.lng.toFixed(3)}</div>${originLabel ? `<div class="origin">${escapeHtml(originLabel)}</div>` : ""}`;
    el.setAttribute("aria-pressed", c.id === selectedId ? "true" : "false");
    el.onclick = () => selectSite(c.id, { fly: true });
    wrap.appendChild(el);
  });
  renderPins();
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
  $("verdict").textContent = "Select a site, then screen it.";
  $("gaps").innerHTML = "";
  if ($("scout-followups")) $("scout-followups").innerHTML = "";
  $("brief").innerHTML = "";
  $("skeptic-stamp").hidden = true;
  $("aerial-status").textContent = "Screen a site to check Aerial View.";
  $("play-aerial").hidden = true;
  $("scorecard").innerHTML = "";
  $("coverage").innerHTML = "";
  $("run-one").hidden = true;
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
  box.textContent = `${v.replace("_", " ")} · ${(packet.verdict.reasons || []).join(", ") || "no veto"}${extra}`;
  const stamp = $("skeptic-stamp");
  if (packet.skeptic) {
    stamp.hidden = false;
    stamp.textContent = `${packet.skeptic.stamp} · ${packet.skeptic.model || "deterministic prechecks"} · ${(packet.skeptic.flags || []).join(", ")}`;
  } else {
    stamp.hidden = true;
  }
  $("gaps").innerHTML = (packet.verdict.gaps || [])
    .map((g) => {
      const q = GAP_QUESTIONS[g.question_id] || g.question_id;
      return `<li data-gap="${escapeHtml(g.question_id)}">${escapeHtml(q)} — ${escapeHtml(g.action)}</li>`;
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
  const cov = packet.coverage || { ratio: 0, usable: 0, relevant: 0 };
  $("coverage").innerHTML =
    `<div class="cov"><i style="width:${Math.round(cov.ratio * 100)}%"></i></div>` +
    `<p class="hint">${cov.usable}/${cov.relevant} decision atoms · ${cov.note || ""}</p>`;
  $("run-one").hidden = false;
  renderCards();
  renderCompare();
  if (!opts || opts.fly !== false) flyTo(packet.candidate);
  refreshCredits();
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
  $("aerial-status").textContent = scene.note || "no Aerial orbit at this pin · Earth uses the UChicago clip · Street instead";
}

async function playAerial(videoId, opts) {
  aerialPlayId = videoId;
  aerialPlayOpts = opts || null;
  aerialRefreshing = true;
  $("aerial-status").textContent = "Loading signed Aerial playback…";
  try {
    const res = await apiFetch(`/api/aerial-play?video_id=${encodeURIComponent(videoId)}`);
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || !payload.uri) {
      $("aerial-status").textContent = payload.error || "Aerial playback unavailable.";
      return false;
    }
    hideStreetStage();
    hideEarthStage();
    const uri = typeof payload.uri === "string"
      ? payload.uri
      : (payload.uri && (payload.uri.landscapeUri || payload.uri.uri || payload.uri.url || payload.uri.value)) || "";
    if (!uri) {
      $("aerial-status").textContent = "Aerial playback URI unavailable.";
      return false;
    }
    if (!["earth", "orbit"].includes(sceneMode)) return false;
    const video = $("aerial-video");
    const credit = $("aerial-credit");
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.src = uri;
    $("video-panel").hidden = false;
    if (credit) {
      credit.textContent = (opts && opts.look === "uchicago")
        ? "University of Chicago · Aerial View 3D orbit · 2022-06-19 · presentation only · does not score this pin"
        : "Aerial View is presentation only. It does not score.";
    }
    await video.play().catch(() => {});
    aerialRetry = 0;
    scheduleAerialRefresh(uri);
    $("aerial-status").textContent = "Aerial orbit playing · presentation only";
    return true;
  } catch (err) {
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
    playAerial(videoId, opts);
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
  playAerial(aerialPlayId, aerialPlayOpts);
}

function closeAerial(opts) {
  if (aerialRefreshTimer) clearTimeout(aerialRefreshTimer);
  aerialRefreshTimer = null;
  if (!(opts && opts.keepId)) aerialPlayId = null;
  const video = $("aerial-video");
  if (!video) return;
  video.pause();
  video.removeAttribute("src");
  video.load();
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
  const body = {
    mission,
    manifest_id: runControls.manifest_id,
    candidate_id: candidateId,
    live: $("live").checked,
    review: $("review").checked,
    controls: runControls,
  };
  if (site && ["user_pin", "user_address"].includes(site.source)) body.candidate = site;
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
      return;
    }
    $("status").textContent = "";
    if (!packet) {
      $("verdict").className = "verdict reject";
      $("verdict").textContent = "run failed";
      $("rail").innerHTML = "<li>failed · empty stream</li>";
      return;
    }
    showPacket(packet);
  } finally {
    $("run-one").disabled = false;
    $("run-all").disabled = false;
  }
}

async function runExpedition() {
  if ($("run-all").disabled || $("run-one").disabled) return;
  const runControls = controls();
  if (!runControls) return;
  const siteCount = activeSites().length;
  $("rail").innerHTML = `<li>expedition · ${siteCount} Candidate Sites in this Search Region</li>`;
  $("status").textContent = `Running ${mission.replace("_", " ")} Expedition…`;
  renderExpeditionLog([]);
  logAction("Expedition started. Screening first, then deepening survivors.");
  $("run-all").disabled = true;
  $("run-one").disabled = true;
  try {
    const res = await apiFetch("/api/expedition-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission,
        manifest_id: runControls.manifest_id,
        live: $("live").checked,
        review: $("review").checked,
        controls: runControls,
      }),
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
      applyMode("street");
    }
    const changes = (result.candidate_changes || []).filter((item) => item.status !== "initial");
    const summary = changes.map((item) => {
      if (item.status === "excluded") return `${item.candidate_id} excluded · ${item.reason}`;
      if (item.candidate) return `${item.rejected_candidate_id} rejected · ${item.status} with ${item.candidate.name}`;
      return `${item.rejected_candidate_id} rejected · lawful candidate pool exhausted at ${item.active_band_id}`;
    }).join(" · ");
    $("status").textContent = summary || "Expedition complete. TODAY is the site. FUTURE is a concept, not a permit.";
  } finally {
    $("run-all").disabled = false;
    $("run-one").disabled = false;
  }
}

async function refreshCredits() {
  const c = await (await apiFetch("/api/credits")).json();
  $("credits").textContent = `${c.used_this_build} / ${c.soft_cap} credits`;
}

function bindLookSwitcher() {
  const params = new URLSearchParams(window.location.search);
  applyLook((params.get("variant") || "A").toUpperCase());
  $("look-prev").onclick = () => stepLook(-1);
  $("look-next").onclick = () => stepLook(1);
  window.addEventListener("keydown", (event) => {
    const tag = (event.target && event.target.tagName) || "";
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tag) || event.target.isContentEditable) return;
    if (event.key === "ArrowLeft") stepLook(-1);
    if (event.key === "ArrowRight") stepLook(1);
  });
}

function stepLook(delta) {
  const index = LOOKS.findIndex((look) => look.id === activeLook);
  const next = LOOKS[(index + delta + LOOKS.length) % LOOKS.length];
  applyLook(next.id);
}

function applyLook(id) {
  const look = LOOKS.find((item) => item.id === id) || LOOKS[0];
  activeLook = look.id;
  document.body.dataset.look = look.id;
  $("app").dataset.look = look.id;
  $("look-label").textContent = `${look.id} — ${look.name}`;
  const url = new URL(window.location.href);
  url.searchParams.set("variant", look.id);
  window.history.replaceState({}, "", url);
  $("demand").hidden = look.id !== "C";
  if (look.id === "D" || look.id === "E") {
    const site = selectedId ? findSite(selectedId) : null;
    updateAdvisory(site, selectedId ? packets[selectedId] : null);
  } else {
    $("advisory").hidden = true;
  }
  if (viewer) setTimeout(() => viewer.resize(), 80);
}

async function loadStreetView(site) {
  if (!site) return;
  const key = `${Number(site.lat).toFixed(5)},${Number(site.lng).toFixed(5)}`;
  if (!streetCache[key]) {
    try {
      const res = await apiFetch(`/api/street-meta?lat=${site.lat}&lng=${site.lng}`);
      streetCache[key] = await res.json();
    } catch (err) {
      streetCache[key] = { available: false, status: "FAILED" };
    }
  }
  const meta = streetCache[key];
  if (sceneMode !== "street") return;
  if (meta && meta.available) {
    $("street-stage").hidden = false;
    $("sv-heading").value = String(meta.heading || 70);
    $("street-credit").textContent = [meta.copyright, meta.date, "Street View · does not score"].filter(Boolean).join(" · ");
    paintStreetImage(site);
    startStreetSpin(site);
    $("context-tag").textContent = "Google Street View — presentation only. Does not score.";
  } else {
    hideStreetStage();
    $("context-tag").textContent = "No Street View at this pin. Street-height 3D — presentation only. Does not score.";
  }
  updateAdvisory(site, packets[site.id]);
}

function paintStreetImage(site) {
  const heading = Number($("sv-heading").value) || 70;
  $("street-image").src = `/sv?lat=${site.lat}&lng=${site.lng}&heading=${heading}`;
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
  if (!site || !site.address) return null;
  if (aerialCache[site.id]) return aerialCache[site.id];
  try {
    const res = await apiFetch(`/api/aerial-meta?query=${encodeURIComponent(site.address)}`);
    const payload = await res.json().catch(() => ({}));
    aerialCache[site.id] = payload && payload.state ? payload : { state: "FAILED", video_id: null };
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

function presentEarthLook(site, packet) {
  hideEarthStage();
  hideStreetStage();
  applyMapBase("hidden");
  if (tileset) tileset.show = false;
  const localId = aerialVideoId(site, packet);
  if (localId) {
    $("context-tag").textContent = "Aerial View 3D orbit — the UChicago look. Does not score.";
    $("status").textContent = "";
    playAerial(localId).then((ok) => {
      if (ok || sceneMode !== "earth") return;
      playUchicagoLook(site);
    });
    return;
  }
  if (site && site.address && !aerialCache[site.id]) {
    $("status").textContent = "Checking Aerial View for this address…";
    prefetchAerial(site).then(() => {
      if (sceneMode !== "earth") return;
      presentEarthLook(site, packets[site.id]);
    });
    return;
  }
  playUchicagoLook(site);
}

function playUchicagoLook(site) {
  const video = $("aerial-video");
  if (
    video
    && !$("video-panel").hidden
    && !video.error
    && video.readyState >= 2
    && !video.paused
    && video.currentSrc
  ) {
    $("context-tag").textContent = "University of Chicago Aerial View — the 40s 3D building orbit from the earlier session. Overlay. Does not score this pin.";
    return;
  }
  $("context-tag").textContent = "University of Chicago Aerial View — the 40s 3D building orbit from the earlier session. Overlay. Does not score this pin.";
  $("status").textContent = "";
  playAerial(UCHICAGO_AERIAL.videoId, { look: "uchicago" }).then((ok) => {
    if (ok || sceneMode !== "earth") return;
    $("context-tag").textContent = "Aerial View unavailable. Photorealistic 3D orbit of this pin. Does not score.";
    startPhotorealisticOrbit(site);
  });
}

function presentOrbit(site, packet) {
  hideEarthStage();
  const videoId = aerialVideoId(site, packet);
  if (videoId) {
    if (tileset) tileset.show = false;
    applyMapBase("hidden");
    hideStreetStage();
    $("context-tag").textContent = "Aerial View 3D orbit — the UChicago look. Does not score.";
    $("status").textContent = "";
    playAerial(videoId).then((ok) => {
      if (ok || sceneMode !== "orbit") return;
      startPhotorealisticOrbit(site);
    });
    return;
  }
  if (site && site.address && !aerialCache[site.id]) {
    $("status").textContent = "Checking Aerial View for this address…";
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
  if (!viewer || !site) {
    $("context-tag").textContent = "No Aerial View at this pin, and 3D is not ready.";
    return;
  }
  if (tileset) tileset.show = true;
  applyMapBase("hidden");
  viewer.scene.globe.show = true;
  $("context-tag").textContent = "Photorealistic 3D orbit of this pin — context only. Does not score.";
  $("status").textContent = "";
  const center = Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 10);
  let heading = Cesium.Math.toRadians(42);
  const pitch = Cesium.Math.toRadians(-26);
  const range = 240;
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
  paintLayers(selectedId ? findSite(selectedId) : null, selectedId ? packets[selectedId] : null);
}

function paintLayers(site, packet) {
  if (!viewer) return;
  layerEntities.forEach((entity) => viewer.entities.remove(entity));
  layerEntities = [];
  if (!site) return;
  const reasons = (packet && packet.verdict && packet.verdict.reasons) || [];
  if (layerOn.flood && reasons.includes("mapped_sfha")) {
    layerEntities.push(viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(site.lng, site.lat, 2),
      ellipse: {
        semiMajorAxis: 220,
        semiMinorAxis: 220,
        material: Cesium.Color.fromCssColorString("#d4654d").withAlpha(0.32),
        height: 1,
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
  if (!["D", "E"].includes(activeLook) || !site) {
    banner.hidden = true;
    return;
  }
  const verdict = packet && packet.verdict ? packet.verdict.verdict.replace("_", " ") : "not screened";
  banner.hidden = false;
  banner.textContent = `${site.name} · ${site.label} · ${verdict}. Pictures do not score.`;
}

$("auth-form").addEventListener("submit", unlock);
window.addEventListener("resize", () => {
  if (["aerial", "osm", "past", "pad", "future"].includes(sceneMode) && selectedId) {
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
