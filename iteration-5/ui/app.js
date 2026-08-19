const select = document.getElementById("site-select");
const app = document.getElementById("app");
const loading = document.getElementById("loading");

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} → ${res.status}`);
  return res.json();
}

function renderVerdict(intel) {
  const { site, ruling } = intel;
  const fights = ruling.fights.length;
  const summary =
    ruling.verdict === "KILL"
      ? `${fights} independent witnesses contradict the cited record.`
      : ruling.verdict === "HUMAN"
        ? `${fights} material contradiction — escalate before proceeding.`
        : "Record and satellite archive agree at this pin.";

  document.getElementById("verdict-strip").innerHTML = `
    <div class="verdict-badge ${ruling.verdict}">${ruling.verdict}</div>
    <div class="verdict-meta">
      <h2>${escapeHtml(site.name)}</h2>
      <p>${escapeHtml(summary)} · ${site.lat.toFixed(6)}, ${site.lng.toFixed(6)}</p>
    </div>`;
}

function renderDocket(intel) {
  const root = document.getElementById("docket");
  root.innerHTML = intel.docket
    .map((item) => {
      const num = item.number != null ? String(item.number).padStart(2, "0") : "—";
      const cls = item.staged ? "status-staged" : "status-skipped";
      const verb = item.staged ? "Staged" : "Skipped";
      const reasons = item.because.map((b) => `<li>${escapeHtml(b)}</li>`).join("");
      return `
        <article class="docket-item">
          <div class="docket-head">
            <span class="docket-num">${num}</span>
            <span class="fight-tag ${cls}">${item.fight}</span>
            <span class="${cls}">${verb}</span>
          </div>
          <ul class="because-list">${reasons}</ul>
        </article>`;
    })
    .join("");
}

function renderVintage(intel) {
  const v = intel.vintage;
  const root = document.getElementById("vintage");
  if (!v.applies) {
    root.innerHTML = `<p class="vintage-muted">Vintage arithmetic does not apply — zone is not AE or no water breakpoint was detected.</p>`;
    return;
  }
  root.innerHTML = `
    <div class="vintage-callout">
      <div class="label">${escapeHtml(v.label)}</div>
      <p>${escapeHtml(v.sentence)}</p>
    </div>`;
}

function renderFights(intel) {
  const { ruling } = intel;
  const root = document.getElementById("fights");
  if (!ruling.fights.length) {
    root.innerHTML = `<p class="vintage-muted">No fights cleared adjudication thresholds.</p>`;
  } else {
    root.innerHTML = ruling.fights
      .map(
        (f, i) => `
      <article class="fight-card">
        <h3>Fight ${i + 1}: ${f.fight}</h3>
        <p class="claim"><strong>Record</strong> ${escapeHtml(f.claim)}</p>
        <p class="witness"><strong>Witness</strong> ${escapeHtml(f.witness)}</p>
        <div class="numbers">${escapeHtml(JSON.stringify(f.numbers))}</div>
      </article>`
      )
      .join("");
  }

  const notFought = ruling.not_fought
    .filter((n) => !ruling.fights.some((f) => f.fight === n.fight))
    .map((n) => `<div class="not-fought"><strong>${n.fight}:</strong> ${escapeHtml(n.reason)}</div>`)
    .join("");
  if (notFought) root.insertAdjacentHTML("beforeend", notFought);

  if (ruling.aggravators?.length) {
    root.insertAdjacentHTML(
      "beforeend",
      `<div class="aggravators"><strong>Aggravating context:</strong> ${escapeHtml(ruling.aggravators.join("; "))}</div>`
    );
  }
}

function renderKeep(intel) {
  const panel = document.getElementById("keep-panel");
  const box = document.getElementById("keep-explanation");
  if (intel.ruling.verdict !== "KEEP" || !intel.ruling.keep_explanation) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  box.innerHTML = `<div class="keep-box">${escapeHtml(intel.ruling.keep_explanation)}</div>`;
}

function renderTimeline(intel) {
  const root = document.getElementById("timeline");
  root.innerHTML = intel.water_timeline_svg || "<p class=\"vintage-muted\">No timeline exhibit.</p>";
}

function render(intel) {
  renderVerdict(intel);
  renderDocket(intel);
  renderVintage(intel);
  renderFights(intel);
  renderKeep(intel);
  renderTimeline(intel);
  app.classList.remove("hidden");
  loading.classList.add("hidden");
}

async function loadSite(slug) {
  loading.classList.remove("hidden");
  app.classList.add("hidden");
  const intel = await fetchJson(`/api/intel?site=${encodeURIComponent(slug)}`);
  render(intel);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function init() {
  const { sites } = await fetchJson("/api/sites");
  select.innerHTML = sites
    .map((s) => `<option value="${s.slug}">${escapeHtml(s.name)} (${s.verdict})</option>`)
    .join("");
  select.addEventListener("change", () => loadSite(select.value));
  await loadSite(sites[0]?.slug || "san_leon");
}

init().catch((err) => {
  loading.textContent = `Failed to load: ${err.message}`;
});
