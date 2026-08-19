const MISSIONS = [
  ["warehouse", "Warehouse"],
  ["farm", "Farm"],
  ["home", "Home"],
  ["data_center", "Data Center"],
];

const MISSION_SITES = {
  warehouse: ["san_leon", "san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"],
  farm: ["manhattan_midtown", "elba_ny", "iowa_corn", "lubbock_cotton"],
  home: ["austin_winfield", "san_leon"],
  data_center: ["ashburn_va", "quincy_wa"],
};

let mission = "warehouse";
let candidates = [];
let map, markers = {};

async function boot() {
  const missions = document.getElementById("missions");
  MISSIONS.forEach(([id, label]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.dataset.id = id;
    if (id === mission) b.classList.add("on");
    b.onclick = () => {
      mission = id;
      missions.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.id === id));
      renderPlan();
      renderCards();
    };
    missions.appendChild(b);
  });
  const data = await (await fetch("/api/candidates")).json();
  candidates = data.candidates;
  map = L.map("map").setView([39.5, -98.3], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);
  renderCards();
  renderPlan();
  refreshCredits();
}

function renderCards() {
  const wrap = document.getElementById("cards");
  wrap.innerHTML = "";
  Object.values(markers).forEach((m) => m.remove());
  markers = {};
  const allowed = new Set(MISSION_SITES[mission] || []);
  candidates.filter((c) => allowed.has(c.id)).forEach((c) => {
    const el = document.createElement("article");
    el.className = "card";
    el.innerHTML = `<div class="label">${c.label}</div><strong>${c.name}</strong><div>${c.lat.toFixed(3)}, ${c.lng.toFixed(3)}</div>`;
    el.onclick = () => run(c.id);
    wrap.appendChild(el);
    const mk = L.marker([c.lat, c.lng]).addTo(map).bindPopup(c.name);
    mk.on("click", () => run(c.id));
    markers[c.id] = mk;
  });
}

function renderPlan() {
  document.getElementById("plan-preview").textContent =
    `${mission} · fixture/replay unless Live is checked · gates are held out`;
}

async function refreshCredits() {
  const c = await (await fetch("/api/credits")).json();
  document.getElementById("credits").textContent =
    `Mireye build ${c.used_this_build} / ${c.soft_cap} (hard ${c.hard_cap})`;
}

async function run(candidateId) {
  const rail = document.getElementById("rail");
  rail.innerHTML = "<li>compiling plan…</li>";
  const body = {
    mission,
    candidate_id: candidateId,
    live: document.getElementById("live").checked,
    review: document.getElementById("review").checked,
    controls: { scan_budget: document.getElementById("scan").value },
  };
  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const packet = await res.json();
  if (!res.ok) {
    document.getElementById("verdict").textContent = packet.error || "run failed";
    return;
  }
  rail.innerHTML = (packet.workstreams || [])
    .map((w) => `<li>${w.id} · ${w.status}${w.note ? " · " + w.note : ""}</li>`)
    .join("");
  const v = packet.verdict.verdict;
  const box = document.getElementById("verdict");
  box.className = "verdict " + v;
  box.textContent = `${v.replace("_", " ")} · ${(packet.verdict.reasons || []).join(", ") || "no veto"}`;
  document.getElementById("gaps").innerHTML = (packet.verdict.gaps || [])
    .map((g) => `<li>${g.question_id}: ${g.action}</li>`)
    .join("");
  const brief = packet.brief || {};
  document.getElementById("brief").innerHTML =
    `<p>${brief.title || ""}</p><ol>${(brief.actions || []).map((a) => `<li>${a}</li>`).join("")}</ol>`;
  const card = [...document.querySelectorAll(".card")].find((el) => el.textContent.includes(packet.candidate.name));
  if (card) card.className = "card " + v;
  map.setView([packet.candidate.lat, packet.candidate.lng], 10);
  refreshCredits();
}

boot();
