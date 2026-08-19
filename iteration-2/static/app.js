/**
 * Property Vetting Agent — courtroom exhibit (iteration 2)
 */

const RECORD_ROWS = [
  { key: "elevation_m", label: "Ground elevation", format: (v) => `${v.value.toFixed(2)} m` },
  { key: "fema_flood_zone", label: "FEMA flood zone", format: (v) => v.value },
  {
    key: "intersects_wetland",
    label: "Intersects wetland",
    format: (v) => (v.value ? "True" : "False"),
  },
  {
    key: "surface_water_permanence_pct",
    label: "Surface-water permanence",
    format: (v) => `${v.value.toFixed(2)}%`,
  },
  {
    key: "coast_distance_m",
    label: "Coast distance",
    format: (v) => `${Math.round(v.value).toLocaleString()} m`,
  },
  { key: "soil_drainage_class", label: "Soil drainage", format: (v) => v.value },
];

let activeSite = "san_leon";

async function fetchSites() {
  const res = await fetch("/api/sites");
  if (!res.ok) throw new Error("Failed to load sites");
  return res.json();
}

async function fetchVet(siteId) {
  const res = await fetch(`/api/vet?site=${encodeURIComponent(siteId)}`);
  if (!res.ok) throw new Error("Failed to load vet packet");
  return res.json();
}

function renderPinSwitcher(sites) {
  const nav = document.getElementById("pin-switcher");
  nav.innerHTML = sites
    .map(
      (s) =>
        `<button class="pin-btn${s.id === activeSite ? " active" : ""}" data-site="${s.id}" type="button">${s.label}</button>`
    )
    .join("");

  nav.querySelectorAll(".pin-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.site !== activeSite) {
        activeSite = btn.dataset.site;
        loadSite(activeSite);
      }
    });
  });
}

function renderRecordTable(record) {
  const tbody = document.querySelector("#record-table tbody");
  tbody.innerHTML = RECORD_ROWS.map(({ key, label, format }) => {
    const field = record[key];
    if (!field) return "";
    const vintage = field.vintage || "—";
    const sourceLink = field.source_url
      ? `<a href="${field.source_url}" target="_blank" rel="noopener">${field.source}</a>`
      : field.source;
    return `<tr>
      <td class="fact-name">${label}</td>
      <td class="fact-value">${format(field)}</td>
      <td>${sourceLink}</td>
      <td class="vintage">${vintage}</td>
    </tr>`;
  }).join("");
}

function renderAggravators(aggravators) {
  const el = document.getElementById("aggravators");
  if (!aggravators || aggravators.length === 0) {
    el.classList.add("hidden");
    el.innerHTML = "";
    return;
  }
  el.classList.remove("hidden");
  el.innerHTML = `
    <h4>Aggravating context</h4>
    <ul>${aggravators.map((a) => `<li>${a}</li>`).join("")}</ul>
  `;
}

function renderWaterWitness(evidence, witnessSummary) {
  const water = evidence.water;
  document.getElementById("water-dataset").textContent = water.dataset;

  const baseline = witnessSummary.water.baseline_freq_1985_1999;
  const latest = witnessSummary.water.latest_freq_2021;
  const bp = witnessSummary.water.breakpoint_year;

  document.getElementById("water-stats").innerHTML = `
    <div><dt>Baseline 1985–1999</dt><dd>${(baseline * 100).toFixed(2)}%</dd></div>
    <div><dt>Latest (2021)</dt><dd>${(latest * 100).toFixed(1)}%</dd></div>
    <div><dt>Breakpoint year</dt><dd>${bp ?? "—"}</dd></div>
  `;
}

async function renderTimeline(url) {
  const wrap = document.getElementById("timeline-wrap");
  wrap.innerHTML = '<p style="font-style:italic;color:var(--parchment-dim)">Loading timeline…</p>';
  try {
    const res = await fetch(url);
    const svg = await res.text();
    wrap.innerHTML = svg;
  } catch {
    wrap.innerHTML = '<p>Timeline unavailable</p>';
  }
}

function renderHeightWitness(record, evidence, witnessSummary) {
  const recordM = record.elevation_m.value;
  const fabdem = evidence.height.fabdem_m;
  const nasadem = evidence.height.nasadem_m;
  const maxM = Math.max(recordM, fabdem, nasadem, 1) * 1.15;

  const pct = (m) => `${Math.min(100, (m / maxM) * 100).toFixed(1)}%`;

  document.getElementById("height-bars").innerHTML = `
    <div class="height-row">
      <span class="height-label">Record</span>
      <div class="height-track"><div class="height-fill record" style="width:${pct(recordM)}"></div></div>
      <span class="height-value">${recordM.toFixed(2)} m</span>
    </div>
    <div class="height-row">
      <span class="height-label">FABDEM</span>
      <div class="height-track"><div class="height-fill fabdem" style="width:${pct(fabdem)}"></div></div>
      <span class="height-value">${fabdem.toFixed(2)} m</span>
    </div>
    <div class="height-row">
      <span class="height-label">NASADEM</span>
      <div class="height-track"><div class="height-fill nasadem" style="width:${pct(nasadem)}"></div></div>
      <span class="height-value">${nasadem.toFixed(2)} m</span>
    </div>
  `;

  const datasets = witnessSummary.height.datasets.join(" · ");
  document.getElementById("height-stats").innerHTML = `
    <div><dt>Datasets</dt><dd style="font-size:0.75rem">${datasets}</dd></div>
    <div><dt>Record − FABDEM</dt><dd>${(recordM - fabdem).toFixed(2)} m</dd></div>
    <div><dt>Record − NASADEM</dt><dd>${(recordM - nasadem).toFixed(2)} m</dd></div>
  `;
}

function renderFights(fights) {
  const panel = document.getElementById("fights-panel");
  if (!fights || fights.length === 0) {
    panel.className = "fights-panel empty";
    panel.innerHTML =
      "No material contradiction between the record and the public satellite archive at this pin.";
    return;
  }

  panel.className = "fights-panel";
  panel.innerHTML = fights
    .map(
      (f) => `
    <article class="fight-card">
      <div class="fight-type">Fight: ${f.fight}</div>
      <p class="claim"><strong>Record claims:</strong> ${f.claim}</p>
      <p class="witness"><strong>Witness says:</strong> ${f.witness}</p>
      <div class="numbers">${JSON.stringify(f.numbers)}</div>
    </article>
  `
    )
    .join("");
}

function renderVerdict(ruling, site, fightCount) {
  const stamp = document.getElementById("verdict-stamp");
  const tagline = document.getElementById("verdict-tagline");
  const verdict = ruling.verdict;

  stamp.className = `verdict-stamp visible ${verdict.toLowerCase()}`;
  stamp.querySelector(".stamp-text").textContent = verdict;

  if (verdict === "KILL") {
    tagline.textContent = "You're buying 2021 dirt at a 1995 feeling";
    tagline.classList.remove("hidden");
  } else {
    tagline.textContent = "";
    tagline.classList.add("hidden");
  }

  document.getElementById("fight-count").textContent =
    fightCount === 0
      ? "0 fights — record and witnesses agree"
      : `${fightCount} fight${fightCount > 1 ? "s" : ""} — record contradicted`;

  document.getElementById("verdict-coords").textContent =
    `${site.lat.toFixed(6)}, ${site.lng.toFixed(6)}`;
}

function renderSiteMeta(site) {
  document.getElementById("site-meta").innerHTML = `
    <strong>${site.name}</strong><br>
    Pin: ${site.lat.toFixed(6)}, ${site.lng.toFixed(6)}
  `;
}

async function loadSite(siteId) {
  const courtroom = document.getElementById("courtroom");
  courtroom.classList.add("loading");

  document.querySelectorAll(".pin-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.site === siteId);
  });

  try {
    const packet = await fetchVet(siteId);
    const { verdict: v, evidence, timeline_url } = packet;
    const { site, ruling, record, witness_summary } = v;

    renderSiteMeta(site);
    renderRecordTable(record);
    renderAggravators(ruling.aggravators);
    renderWaterWitness(evidence, witness_summary);
    await renderTimeline(timeline_url);
    renderHeightWitness(record, evidence, witness_summary);
    renderFights(ruling.fights);
    renderVerdict(ruling, site, ruling.fights.length);
  } catch (err) {
    console.error(err);
    document.getElementById("verdict-tagline").textContent = "Failed to load packet.";
  } finally {
    courtroom.classList.remove("loading");
  }
}

async function init() {
  try {
    const { sites } = await fetchSites();
    renderPinSwitcher(sites);
    await loadSite(activeSite);
  } catch (err) {
    console.error(err);
    document.body.innerHTML =
      '<p style="padding:2rem;color:#c0392b">Could not connect to the vetting API. Run: python3 serve.py</p>';
  }
}

init();
