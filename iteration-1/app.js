const memo = document.getElementById("memo");
const buttons = [...document.querySelectorAll("nav button")];

async function load(site) {
  const v = await (await fetch(`data/${site}/verdict.json`)).json();
  const ruling = v.ruling;
  const rec = v.record;
  const stamp = ruling.verdict;
  const tag =
    stamp === "KILL"
      ? "You’re buying 2021 dirt at a 1995 feeling."
      : "No material contradiction between the record and the public satellite archive at this pin.";
  const rows = [
    ["Ground elevation", rec.elevation_m],
    ["FEMA flood zone", rec.fema_flood_zone],
    ["Intersects wetland", rec.intersects_wetland],
    ["Surface-water permanence", rec.surface_water_permanence_pct],
    ["Soil drainage", rec.soil_drainage_class],
  ];
  const fights = (ruling.fights || [])
    .map(
      (f, i) => `<section class="fight">
        <h3>Fight ${i + 1}: ${f.fight}</h3>
        <p><strong>Record claims.</strong> ${f.claim}</p>
        <p><strong>Witness.</strong> ${f.witness}</p>
      </section>`
    )
    .join("");
  memo.innerHTML = `
    <p class="meta">Pin ${v.site.lat.toFixed(5)}, ${v.site.lng.toFixed(5)} · ${v.site.name}</p>
    <p><span class="stamp ${stamp}">${stamp}</span></p>
    <p class="tagline">${tag}</p>
    <h2>The record (as cited)</h2>
    <table>
      <thead><tr><th>Fact</th><th>Value</th><th>Source</th><th>Vintage</th></tr></thead>
      <tbody>
        ${rows
          .map(([label, f]) => {
            let val = f.value;
            if (typeof val === "number" && !Number.isInteger(val)) val = val.toFixed(2);
            if (f.unit) val = `${val} ${f.unit}`;
            return `<tr><td>${label}</td><td>${val}</td><td>${f.source}</td><td>${f.vintage || "—"}</td></tr>`;
          })
          .join("")}
      </tbody>
    </table>
    <h2>Where the record and the Earth disagree</h2>
    ${fights || "<p>None staged. The witnesses do not impeach the record at this pin.</p>"}
    <p>${(ruling.aggravators || []).join("; ")}</p>
    <h2>Exhibit</h2>
    <object data="data/${site}/water_timeline.svg" type="image/svg+xml"></object>
    <p class="rec">${
      stamp === "KILL"
        ? "Advise the client to withdraw. If they proceed, price the contradiction, not the record."
        : "The skeptic has nothing material to add. Proceed on the record."
    }</p>
  `;
}

buttons.forEach((b) =>
  b.addEventListener("click", () => {
    buttons.forEach((x) => x.classList.toggle("on", x === b));
    load(b.dataset.site);
  })
);
load("san_leon");
