/** Harness trace replay — cached packets, simulated timings. */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

let trace = null;
let currentSite = "san_leon";
let playing = false;
let playToken = 0;

const TOOL_COLORS = {
  mireye: "#58a6ff",
  ee: "#3fb950",
  intel: "#bc8cff",
  judge: "#d29922",
  act: "#f85149",
};

function fmtTool(name) {
  const [ns, fn] = name.split(".");
  return `<span class="prefix">${ns}.</span>${fn || ""}`;
}

function syntaxHighlight(obj) {
  const raw = JSON.stringify(obj, null, 2);
  return raw
    .replace(/"([^"]+)":/g, '<span style="color:#79c0ff">"$1"</span>:')
    .replace(/: "([^"]*)"/g, ': <span style="color:#a5d6ff">"$1"</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span style="color:#ffa657">$1</span>')
    .replace(/: (true|false|null)/g, ': <span style="color:#ff7b72">$1</span>');
}

function renderPlan(steps) {
  const list = $("#plan-list");
  list.innerHTML = steps
    .map((s, i) => `<li data-idx="${i}">${s.tool}</li>`)
    .join("");
}

function renderPin(meta) {
  $("#pin-meta").innerHTML = `
    <div><strong>${meta.name}</strong></div>
    <div>${meta.lat.toFixed(6)}, ${meta.lng.toFixed(6)}</div>
    <div class="muted" style="margin-top:6px">verdict → <strong>${trace.verdict}</strong></div>
  `;
}

function buildTimeline(steps) {
  const el = $("#timeline");
  el.innerHTML = steps
    .map(
      (s, i) => `
    <article class="step" data-idx="${i}" id="step-${i}">
      <div class="step-dot"></div>
      <div class="step-card">
        <div class="step-head">
          <span class="tool-name">${fmtTool(s.tool)}</span>
          <span class="step-meta">
            <span class="dur">${(s.duration_ms / 1000).toFixed(2)}s</span>
            <span class="stat">${s.status}</span>
          </span>
        </div>
        <div class="step-desc">${s.description || ""}</div>
        <div class="step-body">
          <div class="io-block">
            <div class="io-label in">input</div>
            <pre class="json">${syntaxHighlight(s.input)}</pre>
          </div>
          <div class="io-block">
            <div class="io-label out">output</div>
            <pre class="json">${syntaxHighlight(s.output)}</pre>
          </div>
        </div>
      </div>
    </article>`
    )
    .join("");

  $$(".step-head").forEach((head) => {
    head.addEventListener("click", () => {
      head.closest(".step").classList.toggle("expanded");
    });
  });
}

function showVerdictStamp() {
  const stamp = $("#verdict-stamp");
  const v = trace.verdict;
  const fights = trace.fights || [];
  stamp.className = `verdict-stamp ${v}`;
  stamp.innerHTML = `
    <div class="stamp-label">judge.verdict</div>
    <div class="stamp-verdict">${v}</div>
    <div class="stamp-detail">${
      fights.length
        ? `${fights.length} fight(s): ${fights.map((f) => f.fight).join(" + ")}`
        : "No material contradiction between record and public satellite archive."
    }</div>
  `;
}

function resetReplay() {
  playToken++;
  playing = false;
  $("#btn-play").disabled = false;
  $("#trace-status").textContent = "idle";
  $("#trace-status").className = "status idle";
  $("#trace-clock").textContent = "0.0s";
  $("#verdict-stamp").className = "verdict-stamp hidden";
  $$(".step").forEach((s) => {
    s.classList.remove("visible", "running", "done", "error", "expanded");
  });
  $$(".plan-list li").forEach((li) => li.classList.remove("active", "done"));
}

function markPlan(idx, state) {
  $$(".plan-list li").forEach((li, i) => {
    li.classList.toggle("active", state === "active" && i === idx);
    li.classList.toggle("done", state === "done" && i <= idx);
  });
}

async function playTrace() {
  if (playing || !trace) return;
  playing = true;
  const token = ++playToken;
  $("#btn-play").disabled = true;
  $("#trace-status").textContent = "running";
  $("#trace-status").className = "status running";
  $("#verdict-stamp").className = "verdict-stamp hidden";

  const speed = parseFloat($("#speed").value) || 1;
  const steps = trace.steps;

  for (let i = 0; i < steps.length; i++) {
    if (token !== playToken) return;

    const stepEl = $(`#step-${i}`);
    const s = steps[i];

    markPlan(i, "active");
    stepEl.classList.add("visible", "running");
    stepEl.scrollIntoView({ behavior: "smooth", block: "nearest" });

    const waitMs = (s.duration_ms + 120) / speed;
    const start = performance.now();

    while (performance.now() - start < waitMs) {
      if (token !== playToken) return;
      const elapsed = ((s.started_ms + (performance.now() - start) * speed) / 1000).toFixed(1);
      $("#trace-clock").textContent = `${elapsed}s`;
      await sleep(50);
    }

    stepEl.classList.remove("running");
    stepEl.classList.add(s.status === "ok" ? "done" : "error");
    stepEl.classList.add("expanded");
    markPlan(i, "done");
    $("#trace-clock").textContent = `${(s.finished_ms / 1000).toFixed(1)}s`;
  }

  if (token !== playToken) return;

  showVerdictStamp();
  $("#trace-status").textContent = "done";
  $("#trace-status").className = "status done";
  playing = false;
  $("#btn-play").disabled = false;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function loadSite(site) {
  currentSite = site;
  resetReplay();
  $$(".site-btn").forEach((b) => b.classList.toggle("active", b.dataset.site === site));

  const resp = await fetch(`/api/trace?site=${encodeURIComponent(site)}`);
  if (!resp.ok) {
    $("#pin-meta").textContent = `error: ${resp.status}`;
    return;
  }
  trace = await resp.json();
  renderPin(trace.site);
  renderPlan(trace.steps);
  buildTimeline(trace.steps);
}

function init() {
  $$(".site-btn").forEach((btn) => {
    btn.addEventListener("click", () => loadSite(btn.dataset.site));
  });
  $("#btn-play").addEventListener("click", playTrace);
  $("#btn-reset").addEventListener("click", () => {
    resetReplay();
    if (trace) buildTimeline(trace.steps);
  });
  $("#speed").addEventListener("input", (e) => {
    $("#speed-label").textContent = `${e.target.value}×`;
  });

  loadSite("san_leon");
}

init();
