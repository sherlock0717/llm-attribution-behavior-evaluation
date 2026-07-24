// PA—Wu R1 Pilot showcase v1. Reads data/showcase_data.json (synthetic demo)
// and renders all sections + interactions. No model ranking, no ai/human
// comparison, no conclusive brand claims.
"use strict";

const FIG_BASE = "assets/figures/";
const CONDS = ["C0", "C1", "C2", "C3", "C4", "C5"];
const PRIMARY = ["IN", "GO", "MSI", "IC"];
const ALL_CONSTRUCTS = ["IN", "GO", "MSI", "IC", "PA5", "PA8"];

let DATA = null;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

function fmt(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return "–";
  return Number(x).toFixed(digits);
}
function signed(x, digits = 3) {
  if (x === null || x === undefined || Number.isNaN(x)) return "–";
  const v = Number(x);
  return (v >= 0 ? "+" : "") + v.toFixed(digits);
}

async function load() {
  const res = await fetch("data/showcase_data.json");
  DATA = await res.json();
  render();
}

function render() {
  renderQuestion();
  renderConstructs();
  renderConditions();
  renderCoverage();
  renderScenarioBrowser();
  renderJudges();
  renderConditionResults();
  renderContrasts();
  renderJudgeDiff();
  renderScenarioHet();
  renderMaterialExamples();
  renderBoundaries();
  renderReplacement();
  renderGithub();
  renderFigures();
  setupLightbox();
}

function renderQuestion() {
  const s = DATA.project_summary;
  document.getElementById("researchQuestion").textContent = s.research_question;
  document.getElementById("freeWillRole").textContent = s.free_will_role;
  document.getElementById("identityScope").textContent = s.identity_scope;
}

function renderConstructs() {
  const c = DATA.constructs;
  const host = document.getElementById("constructCards");
  const mk = (key) => {
    const isPrimary = c.primary.includes(key);
    return el("div", { class: "card" },
      el("h3", {}, `${key} — ${c.names[key]}`),
      el("p", {},
        el("span", { class: "badge scale" }, `scale ${c.native_scales[key]}`),
        " ",
        el("span", { class: "badge" }, isPrimary ? "primary" : "supplementary")
      ),
      el("p", { class: "small" },
        key === "MSI" ? "Includes wu_ms3 (free will) as an exploratory item only." :
        (isPrimary ? "Machine-specific original Wu & Shen 2026 item." : "Perceived Agency (PA 2024).")
      )
    );
  };
  ALL_CONSTRUCTS.forEach((k) => host.appendChild(mk(k)));
}

function renderConditions() {
  const host = document.getElementById("conditionCards");
  const conds = DATA.conditions;
  CONDS.forEach((k) => {
    host.appendChild(el("div", { class: "card" },
      el("h3", {}, el("span", { class: "cond-pill" }, k)),
      el("p", {}, conds[k])
    ));
  });
}

function renderCoverage() {
  const host = document.getElementById("coverageCards");
  const bal = DATA.material_balance;
  const q = DATA.quality_summary;
  const kv = (label, obj) => el("div", { class: "card" },
    el("h3", {}, label),
    el("p", { class: "small" }, JSON.stringify(obj))
  );
  host.appendChild(el("div", { class: "card" },
    el("h3", {}, "Totals"),
    el("p", {}, `Materials: ${q.n_materials} · Responses: ${q.n_responses} (2 judge models × 96)`),
    el("p", { class: "small" }, `item valid rate ${fmt(q.item_valid_rate, 3)} · construct scored rate ${fmt(q.construct_scored_rate, 3)}`)
  ));
  host.appendChild(kv("Per condition", bal.per_condition));
  host.appendChild(kv("Per scenario", bal.per_scenario));
  host.appendChild(kv("Per direction", bal.per_direction));
}

function renderScenarioBrowser() {
  const scenSel = document.getElementById("scenSelect");
  const condSel = document.getElementById("scenCondSelect");
  const dirSel = document.getElementById("scenDirSelect");
  DATA.scenarios.forEach((s) => scenSel.appendChild(el("option", { value: s }, s)));
  CONDS.forEach((c) => condSel.appendChild(el("option", { value: c }, c)));
  ["A", "B"].forEach((d) => dirSel.appendChild(el("option", { value: d }, d)));

  const update = () => {
    const sid = scenSel.value, cid = condSel.value, dir = dirSel.value;
    const list = (DATA.scenario_materials[sid] || []).filter(
      (m) => m.condition_id === cid && m.direction_version === dir
    );
    const host = document.getElementById("scenStim");
    host.innerHTML = "";
    if (!list.length) { host.appendChild(el("p", { class: "muted" }, "No material for this combination.")); return; }
    list.forEach((m) => host.appendChild(renderStim(m)));
  };
  scenSel.onchange = condSel.onchange = dirSel.onchange = update;
  update();
}

function renderStim(m) {
  // split off the referent bridge visually if present.
  const bridge = 'In the following items, "the machine" refers to the AI system described above.';
  let text = m.complete_stimulus_text;
  let bridgePart = "";
  if (text.includes(bridge)) {
    bridgePart = bridge;
    text = text.replace(bridge, "").trim();
  }
  return el("div", { class: "stim" },
    el("div", { class: "meta" }, `${m.material_id}  ·  ${m.condition_id}  ·  dir ${m.direction_version}  ·  machine`),
    el("div", { class: "text" }, text),
    bridgePart ? el("div", { class: "bridge" }, bridgePart) : null
  );
}

function renderJudges() {
  const host = document.getElementById("judgeCards");
  DATA.judge_models.forEach((j) => {
    host.appendChild(el("div", { class: "card" },
      el("h3", {}, el("span", { class: "badge" }, j.id)),
      el("p", {}, `provider: ${j.provider}`),
      el("p", { class: "small" }, j.role)
    ));
  });
}

function tableFrom(headers, rows, numCols = []) {
  const t = el("table");
  const thead = el("tr");
  headers.forEach((h, i) => thead.appendChild(el("th", numCols.includes(i) ? { class: "num" } : {}, h)));
  t.appendChild(thead);
  rows.forEach((r) => {
    const tr = el("tr");
    r.forEach((c, i) => {
      const isNum = numCols.includes(i);
      const td = el("td", isNum ? { class: "num" } : {});
      if (c && typeof c === "object" && c.node) td.appendChild(c.node);
      else td.textContent = c;
      tr.appendChild(td);
    });
    t.appendChild(tr);
  });
  return t;
}

function renderConditionResults() {
  const sel = document.getElementById("resConstructSelect");
  ALL_CONSTRUCTS.forEach((c) => sel.appendChild(el("option", { value: c }, c)));
  const means = DATA.descriptive_results.condition_means;
  sel.onchange = () => rebuildCondTable(sel.value, means);
  rebuildCondTable(sel.value, means);
}
function rebuildCondTable(c, means) {
  const row = means[c] || {};
  const rows = CONDS.map((cd) => [cd, fmt(row[cd])]);
  const t = tableFrom(["condition", "mean (native scale)"], rows, [1]);
  t.id = "condResultTable";
  document.getElementById("condResultTable").replaceWith(t);
}

function renderContrasts() {
  const sel = document.getElementById("contrastConstructSelect");
  ALL_CONSTRUCTS.forEach((c) => sel.appendChild(el("option", { value: c }, c)));
  let mode = "adjusted";
  const modeGroup = document.getElementById("contrastMode");
  modeGroup.querySelectorAll("button").forEach((b) => {
    b.onclick = () => {
      modeGroup.querySelectorAll("button").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      mode = b.dataset.mode;
      build();
    };
  });
  sel.onchange = build;

  function build() {
    const c = sel.value;
    const adj = DATA.model_adjusted_results.contrasts.filter((r) => r.construct === c);
    const rawList = DATA.raw_planned_contrasts.filter((r) => r.construct === c);
    let rows, headers, numCols;
    if (mode === "adjusted") {
      headers = ["id", "contrast", "estimate", "SE", "z", "p", "p(Holm)", "95% CI", "raw"];
      numCols = [2, 3, 4, 5, 6, 8];
      rows = adj.map((r) => [
        r.contrast_id, r.contrast, cell(signed(r.estimate)), fmt(r.standard_error, 3),
        fmt(r.statistic, 2), fmt(r.p_value, 3), fmt(r.p_value_holm, 3),
        (r.ci95_low == null ? "–" : `[${fmt(r.ci95_low, 2)}, ${fmt(r.ci95_high, 2)}]`),
        cell(signed(r.raw_descriptive_contrast)),
      ]);
    } else {
      headers = ["id", "contrast", "difference", "effect size d", "95% CI", "n(L)", "n(R)"];
      numCols = [2, 3, 5, 6];
      rows = rawList.map((r) => [
        r.contrast_id, r.contrast, cell(signed(r.difference)),
        fmt(r.effect_size_d, 2),
        (r.ci95_low == null ? "–" : `[${fmt(r.ci95_low, 2)}, ${fmt(r.ci95_high, 2)}]`),
        r.n_left, r.n_right,
      ]);
    }
    const t = tableFrom(headers, rows, numCols);
    t.id = "contrastTable";
    document.getElementById("contrastTable").replaceWith(t);
  }
  build();
}

function cell(text) {
  const cls = text.startsWith("+") ? "pos" : (text.startsWith("-") ? "neg" : "");
  return { node: el("span", { class: cls }, text) };
}

function renderJudgeDiff() {
  const mm = DATA.descriptive_results.model_means;
  const models = DATA.judge_models.map((j) => j.id);
  const rows = ALL_CONSTRUCTS.map((c) => [
    c,
    fmt((mm[c] || {})[models[0]]),
    fmt((mm[c] || {})[models[1]]),
  ]);
  const t = tableFrom(["construct", models[0], models[1]], rows, [1, 2]);
  t.id = "judgeDiffTable";
  document.getElementById("judgeDiffTable").replaceWith(t);
}

function renderScenarioHet() {
  const h = DATA.quality_summary.scenario_heterogeneity;
  const rows = ALL_CONSTRUCTS.filter((c) => h[c]).map((c) => [
    c, fmt(h[c].scenario_mean_min), fmt(h[c].scenario_mean_max), fmt(h[c].scenario_mean_range),
  ]);
  const t = tableFrom(["construct", "min", "max", "range"], rows, [1, 2, 3]);
  t.id = "scenHetTable";
  document.getElementById("scenHetTable").replaceWith(t);
}

function renderMaterialExamples() {
  const host = document.getElementById("materialExamples");
  const sid = DATA.scenarios[0];
  const list = DATA.scenario_materials[sid] || [];
  // one example per condition (direction A).
  CONDS.forEach((cid) => {
    const m = list.find((x) => x.condition_id === cid && x.direction_version === "A");
    if (m) host.appendChild(renderStim(m));
  });
}

function renderBoundaries() {
  const ul = document.getElementById("boundaryList");
  DATA.method_boundaries.forEach((b) => ul.appendChild(el("li", {}, b)));
}

function renderReplacement() {
  const ol = document.getElementById("replacementList");
  DATA.real_data_replacement.forEach((r) => ol.appendChild(el("li", {}, r)));
}

function renderGithub() {
  const g = DATA.github_entry;
  const host = document.getElementById("githubCard");
  host.appendChild(el("p", {}, "Repository path: ", el("span", { class: "badge" }, g.repo_path)));
  host.appendChild(el("p", {}, "Outputs: ", el("span", { class: "badge" }, g.repo_path + "/" + g.outputs)));
  host.appendChild(el("p", {}, "Report: ", el("span", { class: "badge" }, g.repo_path + "/" + g.report)));
  host.appendChild(el("p", { class: "small muted" },
    "Replace demo/demo_responses.jsonl with a real authorized run, then re-run the pipeline to refresh this page."));
}

function renderFigures() {
  document.querySelectorAll("img[data-fig]").forEach((img) => {
    img.src = FIG_BASE + img.getAttribute("data-fig");
  });
}

function setupLightbox() {
  const lb = document.getElementById("lightbox");
  const lbImg = document.getElementById("lbImg");
  const lbCap = document.getElementById("lbCap");
  document.querySelectorAll(".figure img").forEach((img) => {
    img.onclick = () => {
      lbImg.src = img.src;
      const cap = img.parentElement.querySelector(".cap");
      lbCap.textContent = cap ? cap.textContent : "";
      lb.classList.add("open");
    };
  });
  const close = () => lb.classList.remove("open");
  document.getElementById("lbClose").onclick = close;
  lb.onclick = (e) => { if (e.target === lb) close(); };
}

load().catch((err) => {
  document.getElementById("app").prepend(
    el("section", {}, el("h2", {}, "Failed to load showcase data"),
      el("p", { class: "muted" }, String(err)))
  );
});
