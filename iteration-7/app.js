/* global Cesium from the 1.105 script tag */
const MODE_NOTES = {
  mesh: "Google photorealistic 3D tiles — the listing-photo of this dirt. Context only. Not in the packet.",
  water: "JRC water occurrence (how often wet, 1984–2021). This is the TIME witness.",
  naip: "USDA NAIP ~1 m aerial. Public exhibit. Texas vintage stops mid-2022.",
  height: "FABDEM bare-earth, stretched 0–10 m. Marsh reads blue. Austin at 205 m saturates — high ground.",
  change: "Google Satellite Embedding 2017→2024 (1 − cosine). The land fingerprint moved.",
};

let config = null;
let packets = {};
let viewer = null;
let tileset = null;
let pinEntity = null;
let activeSite = "san_leon";
let activeMode = "mesh";

function $(id) {
  return document.getElementById(id);
}

function fmtElev(m) {
  return m == null ? "—" : Number(m).toFixed(2) + " m";
}
function fmtDist(m) {
  if (m == null) return "—";
  return m > 1000 ? (m / 1000).toFixed(1) + " km" : Math.round(m) + " m";
}

async function boot() {
  $("status").textContent = "Fetching config…";
  config = await fetch("/api/config").then((r) => r.json());
  const [san, aus] = await Promise.all([
    fetch("/api/vet?site=san_leon").then((r) => r.json()),
    fetch("/api/vet?site=keep_control").then((r) => r.json()),
  ]);
  packets.san_leon = san;
  packets.keep_control = aus;

  viewer = new Cesium.Viewer("cesiumContainer", {
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
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#070605");
  viewer.scene.globe.show = false;
  viewer.imageryLayers.removeAll();

  if (!config.has_google_tiles) {
    $("status").textContent = "No Map Tiles API key on the server.";
    renderDock();
    return;
  }

  tileset = viewer.scene.primitives.add(
    new Cesium.Cesium3DTileset({
      url: config.tileset,
      showCreditsOnScreen: true,
    })
  );

  tileset.readyPromise
    .then(() => {
      $("status").textContent = "";
      $("status").style.display = "none";
      flyTo(activeSite, 0);
      applyMode("mesh");
    })
    .otherwise((err) => {
      $("status").textContent = "3D tiles failed to load: " + err;
    });

  document.querySelectorAll(".pin").forEach((btn) => {
    btn.addEventListener("click", () => setSite(btn.dataset.site));
  });
  document.querySelectorAll(".mode").forEach((btn) => {
    btn.addEventListener("click", () => applyMode(btn.dataset.mode));
  });

  renderDock();
}

function siteMeta(id) {
  return config.sites[id];
}

function flyTo(id, duration) {
  const meta = siteMeta(id);
  const cam = meta.camera;
  const center = Cesium.Cartesian3.fromDegrees(meta.lng, meta.lat, cam.height || 8);
  const sphere = new Cesium.BoundingSphere(center, 40);
  viewer.camera.flyToBoundingSphere(sphere, {
    duration: duration == null ? 2.4 : duration,
    offset: new Cesium.HeadingPitchRange(
      Cesium.Math.toRadians(cam.heading),
      Cesium.Math.toRadians(cam.pitch),
      cam.range
    ),
  });

  if (pinEntity) viewer.entities.remove(pinEntity);
  const kill = meta.verdict === "KILL";
  pinEntity = viewer.entities.add({
    position: center,
    point: {
      pixelSize: 14,
      color: kill ? Cesium.Color.fromCssColorString("#c0392b") : Cesium.Color.fromCssColorString("#7dcea0"),
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 1,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
    label: {
      text: meta.label,
      font: "12px monospace",
      fillColor: Cesium.Color.WHITE,
      pixelOffset: new Cesium.Cartesian2(0, -22),
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
}

function setSite(id) {
  activeSite = id;
  document.querySelectorAll(".pin").forEach((b) => b.classList.toggle("on", b.dataset.site === id));
  const meta = siteMeta(id);
  const stamp = $("stamp");
  stamp.textContent = meta.verdict;
  stamp.className = "stamp " + (meta.verdict === "KILL" ? "kill" : "keep");
  $("liner").textContent = meta.one_liner;
  flyTo(id, 2.2);
  renderDock();
}

function clearImagery() {
  viewer.imageryLayers.removeAll();
}

function addTemplate(url, credit) {
  const provider = new Cesium.UrlTemplateImageryProvider({
    url,
    credit: credit || "",
  });
  return viewer.imageryLayers.addImageryProvider(provider);
}

function applyMode(mode) {
  activeMode = mode;
  document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  $("mode-note").textContent = MODE_NOTES[mode] || "";
  $("context-tag").textContent =
    mode === "mesh"
      ? "Google photorealistic 3D — context, never a cited exhibit"
      : "Earth Engine witness — this layer may be cited";

  if (!viewer) return;

  if (mode === "mesh") {
    if (tileset) tileset.show = true;
    viewer.scene.globe.show = false;
    clearImagery();
    return;
  }

  const layer = config.ee_layers && config.ee_layers[mode];
  if (!layer) {
    $("mode-note").textContent = (config.ee_error || "Earth Engine overlay not ready yet.") + " Stay on 3D mesh.";
    return;
  }

  if (tileset) tileset.show = false;
  viewer.scene.globe.show = true;
  clearImagery();
  const sat = addTemplate(config.satellite, "Google satellite (context)");
  sat.alpha = 0.35;
  const overlay = addTemplate(layer.url, layer.credit);
  overlay.alpha = 0.85;
  $("mode-note").textContent = layer.note || MODE_NOTES[mode];
}

function renderDock() {
  const pack = packets[activeSite];
  if (!pack) return;
  const rec = pack.verdict.record;
  const ruling = pack.verdict.ruling;
  const ex = pack.exhibits || {};
  const files = ex.files || {};

  const captions = [
    ["naip_2005", "NAIP 2005"],
    ["naip_2010", "NAIP 2010"],
    ["naip_2022", "NAIP 2022"],
    ["jrc_occurrence", "JRC water %"],
    ["fabdem", "FABDEM height"],
    ["embed_change", "Embedding Δ"],
  ];
  const film = captions
    .filter(([key]) => files[key])
    .map(
      ([key, cap]) =>
        `<figure><img src="/exhibits/${files[key]}" alt="${cap}"><figcaption>${cap}</figcaption></figure>`
    )
    .join("");
  $("film").innerHTML = film || "<p class='mode-note'>Exhibits still rendering from Earth Engine…</p>";

  const stats = ex.stats || {};
  const zone = rec.fema_flood_zone.value;
  const ch = stats.embed_change_2017_2024;
  $("facts").innerHTML = `
    <div><b>FEMA</b><span class="${zone === "AE" ? "alert" : ""}">${zone}</span></div>
    <div><b>Record elev</b>${fmtElev(rec.elevation_m.value)}</div>
    <div><b>FABDEM</b>${fmtElev((pack.evidence.height || {}).fabdem_m)}</div>
    <div><b>Water rec</b>${rec.surface_water_permanence_pct.value}%</div>
    <div><b>Wetland</b><span class="${rec.intersects_wetland.value ? "alert" : ""}">${rec.intersects_wetland.value ? "yes" : "no"}</span></div>
    <div><b>Coast</b>${fmtDist(rec.coast_distance_m.value)}</div>
    <div><b>Δ 2017–24</b>${ch == null ? "—" : (ch * 100).toFixed(1) + "%"}</div>
  `;

  const fights = ruling.fights || [];
  $("fights").innerHTML = fights.length
    ? fights
        .map(
          (f) =>
            `<div class="fight"><strong>${f.fight}</strong> — ${f.claim}<br><em>${f.witness}</em></div>`
        )
        .join("")
    : `<div class="fight">No fights staged. Inland, zone ${zone}, height gate closed.</div>`;

  const tl = (pack.evidence.water && pack.evidence.water.timeline) || [];
  const max = Math.max(...tl.map((t) => t.water_freq), 0.01);
  $("timeline").innerHTML = tl
    .map((t) => {
      const h = Math.max(2, (t.water_freq / max) * 100);
      const wet = ruling.verdict === "KILL" && t.water_freq > 0.005;
      return `<div class="bar${wet ? " wet" : ""}" style="height:${h}%" title="${t.year}: ${(t.water_freq * 100).toFixed(1)}%"></div>`;
    })
    .join("");
}

boot().catch((err) => {
  $("status").textContent = String(err);
});
