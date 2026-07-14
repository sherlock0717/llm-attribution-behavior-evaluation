// Static showcase behaviour (SHOWCASE-RELEASE-001 rebuild).
// Native JS only: no third-party libraries, no CDN, no remote API, no ES module
// imports from URLs. Loads the static JSON files under data/ and renders the
// continuous research + engineering narrative. Numbers are never hardcoded in
// HTML; they come from site/data/*.json produced by the build scripts.

"use strict";

// ---------------------------------------------------------------------------
// Small DOM helpers
// ---------------------------------------------------------------------------
function el(tag, opts) {
  opts = opts || {};
  const node = document.createElement(tag);
  if (opts.className) node.className = opts.className;
  if (opts.text != null) node.textContent = opts.text;
  return node;
}

function setSlot(name, value) {
  document.querySelectorAll('[data-slot="' + name + '"]').forEach((n) => {
    n.textContent = value;
  });
}

function slotEl(name) {
  return document.querySelector('[data-slot="' + name + '"]');
}

function requireSlot(name) {
  const node = slotEl(name);
  if (!node) throw new Error('Missing required page slot: data-slot="' + name + '"');
  return node;
}

async function loadJSON(path) {
  const resp = await fetch(path, { cache: "no-store" });
  if (!resp.ok) throw new Error("HTTP " + resp.status + " for " + path);
  return resp.json();
}

function fmtP(p) {
  if (p == null) return "";
  return p < 0.001 ? "p < .001" : "p = " + Number(p).toFixed(3);
}

function svgNS(tag, attrs) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  if (attrs) Object.keys(attrs).forEach((k) => n.setAttribute(k, attrs[k]));
  return n;
}

// Distinct, defined series colours (kept in CSS-var-free JS for the SVG chart).
const SERIES_COLORS = ["#2f6fed", "#e8590c", "#2f9e44", "#7048e8", "#c2255c"];

let CONDITION_LABELS = {};

// ---------------------------------------------------------------------------
// 1. Overview / hero core facts
// ---------------------------------------------------------------------------
function renderHero(story, summary) {
  setSlot("source-commit", summary.source_commit);
  setSlot("data-as-of", summary.data_as_of_date);
  setSlot("generated-at", summary.generated_at);

  const dl = requireSlot("hero-corefacts");
  dl.textContent = "";
  (story.core_facts || []).forEach((f) => {
    const wrap = el("div", { className: "metric" });
    wrap.appendChild(el("dt", { text: f.label }));
    wrap.appendChild(el("dd", { text: String(f.value) }));
    dl.appendChild(wrap);
  });
}

// ---------------------------------------------------------------------------
// 3. Experimental design (stats + 6x2 matrix + gradient) + scenarios
// ---------------------------------------------------------------------------
const LENGTH_CONTROL_KEY = "direct_choice_long";

function renderDesign(summary) {
  const d = summary.design;
  CONDITION_LABELS = {};
  d.process_conditions.forEach((c) => { CONDITION_LABELS[c.key] = c.label; });

  const stats = requireSlot("design-stats");
  stats.textContent = "";
  [
    [d.total_records, "历史记录"],
    [d.process_conditions.length + " × " + d.identity_labels.length, "过程 × 身份"],
    [d.n_per_cell, "每格样本"],
    [d.process_conditions.length * d.identity_labels.length, "条件格"],
  ].forEach(([num, lbl]) => {
    const wrap = el("div");
    wrap.appendChild(el("span", { className: "num", text: String(num) }));
    wrap.appendChild(el("span", { className: "lbl", text: lbl }));
    stats.appendChild(wrap);
  });

  const table = requireSlot("design-matrix");
  const caption = table.querySelector("caption");
  table.textContent = "";
  if (caption) table.appendChild(caption);
  const thead = el("thead");
  const hrow = el("tr");
  hrow.appendChild(el("th", { className: "corner", text: "决策过程 ＼ 身份" }));
  d.identity_labels.forEach((idl) => hrow.appendChild(el("th", { text: idl })));
  thead.appendChild(hrow);
  table.appendChild(thead);
  const tbody = el("tbody");
  d.process_conditions.forEach((c) => {
    const tr = el("tr");
    const th = el("th", { className: "rowhead" });
    th.appendChild(el("code", { text: c.key }));
    th.appendChild(document.createTextNode(" " + c.label));
    th.appendChild(el("span", { className: "cond-note", text: c.note }));
    tr.appendChild(th);
    d.identity_labels.forEach(() => {
      tr.appendChild(el("td", { className: "cell", text: "n = " + d.n_per_cell }));
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  renderGradient(d);
}

function renderGradient(d) {
  const host = requireSlot("process-gradient");
  host.textContent = "";
  const scale = el("div", { className: "grad-scale" });
  scale.appendChild(el("span", { className: "grad-end low", text: "低结构" }));
  scale.appendChild(el("span", { className: "grad-end high", text: "高结构" }));
  host.appendChild(scale);
  const track = el("div", { className: "grad-track" });
  d.process_conditions.forEach((c, i) => {
    const isDiag = c.key === LENGTH_CONTROL_KEY;
    const node = el("div", { className: "grad-node" + (isDiag ? " diagnostic" : "") });
    const head = el("div", { className: "grad-head" });
    head.appendChild(el("span", { className: "grad-idx", text: String(i + 1) }));
    head.appendChild(el("code", { text: c.key }));
    node.appendChild(head);
    node.appendChild(el("div", { className: "grad-label", text: c.label }));
    node.appendChild(el("div", { className: "grad-note", text: c.note }));
    if (isDiag) node.appendChild(el("span", { className: "grad-tag", text: "长度对照条件" }));
    track.appendChild(node);
  });
  host.appendChild(track);
}

function renderScenarios(story) {
  const host = requireSlot("scenario-list");
  host.textContent = "";
  (story.scenarios || []).forEach((s) => {
    const li = el("li", { className: "scenario" });
    li.appendChild(el("span", { className: "sc-label", text: s.label }));
    li.appendChild(el("code", { text: s.id }));
    host.appendChild(li);
  });
  if (story.domains && story.domains.length) {
    const li = el("li", { className: "scenario domains" });
    li.appendChild(el("span", { className: "sc-label", text: "决策领域" }));
    li.appendChild(el("span", { className: "sc-domains", text: story.domains.join("、") }));
    host.appendChild(li);
  }
}

// ---------------------------------------------------------------------------
// 3. Construct / measurement table
// ---------------------------------------------------------------------------
function renderConstructTable(measurement) {
  setSlot("construct-count", measurement.total_constructs);
  setSlot("item-count", measurement.total_items);
  const table = requireSlot("construct-table");
  const caption = table.querySelector("caption");
  table.textContent = "";
  if (caption) table.appendChild(caption);
  const thead = el("thead");
  const hr = el("tr");
  ["构念", "角色", "题项数", "评分范围", "内部一致性 α"].forEach((h) =>
    hr.appendChild(el("th", { text: h })));
  thead.appendChild(hr);
  table.appendChild(thead);
  const tbody = el("tbody");
  (measurement.constructs || []).forEach((c) => {
    const tr = el("tr");
    const nameTd = el("td", { className: "cname" });
    nameTd.appendChild(el("span", { text: c.label }));
    nameTd.appendChild(el("code", { text: c.key }));
    tr.appendChild(nameTd);
    tr.appendChild(el("td", { text: c.role }));
    tr.appendChild(el("td", { className: "num-cell", text: String(c.n_items) }));
    tr.appendChild(el("td", { className: "num-cell", text: c.range }));
    tr.appendChild(el("td", { className: "num-cell", text: Number(c.alpha).toFixed(3) }));
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

// ---------------------------------------------------------------------------
// 4. Historical data composition (12 units)
// ---------------------------------------------------------------------------
function renderHistoryComposition(summary) {
  setSlot("record-count", summary.design.total_records);
  const host = requireSlot("history-composition");
  host.textContent = "";
  const d = summary.design;
  d.process_conditions.forEach((c) => {
    const row = el("div", { className: "hc-row" });
    const label = el("div", { className: "hc-rowhead" });
    label.appendChild(el("span", { text: c.label }));
    row.appendChild(label);
    const cells = el("div", { className: "hc-cells" });
    d.identity_labels.forEach((idl, j) => {
      const cell = el("div", { className: "hc-cell k" + j });
      cell.appendChild(el("span", { className: "hc-id", text: idl }));
      cell.appendChild(el("span", { className: "hc-n", text: "n = " + d.n_per_cell }));
      cells.appendChild(cell);
    });
    row.appendChild(cells);
    host.appendChild(row);
  });
  const total = el("p", { className: "hc-total" });
  total.textContent = "12 个实验单元 × 每格 " + d.n_per_cell + " = " + d.total_records + " 条历史记录";
  host.appendChild(total);
}

// ---------------------------------------------------------------------------
// 5A. Reliability bars
// ---------------------------------------------------------------------------
function renderReliability(measurement) {
  const host = requireSlot("reliability-bars");
  host.textContent = "";
  (measurement.constructs || []).forEach((c) => {
    const row = el("div", { className: "rel-row" });
    const label = el("span", { className: "rel-label" });
    label.appendChild(document.createTextNode(c.label));
    label.appendChild(el("code", { text: c.key }));
    row.appendChild(label);
    const track = el("div", { className: "rel-track" });
    const fill = el("div", { className: "rel-fill" });
    fill.style.width = Math.round(Number(c.alpha) * 100) + "%";
    track.appendChild(fill);
    row.appendChild(track);
    row.appendChild(el("span", { className: "rel-val", text: "α = " + Number(c.alpha).toFixed(3) }));
    host.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// 5B. Six-condition core construct profile (SVG multi-series)
// ---------------------------------------------------------------------------
function renderConditionProfile(analysis) {
  const host = requireSlot("condition-profile");
  host.textContent = "";
  const cp = analysis.condition_profile;
  const conditions = cp.conditions;
  const series = cp.series;

  const W = 640, H = 320, padL = 40, padR = 16, padT = 16, padB = 40;
  const yMin = 3, yMax = 6;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const x = (i) => padL + (conditions.length === 1 ? plotW / 2 : (plotW * i) / (conditions.length - 1));
  const y = (v) => padT + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

  const svg = svgNS("svg", { viewBox: "0 0 " + W + " " + H, class: "cp-svg",
    role: "img", "aria-label": "六条件核心构念均值剖面" });

  // gridlines + y ticks
  for (let v = yMin; v <= yMax; v += 1) {
    svg.appendChild(svgNS("line", { x1: padL, y1: y(v), x2: W - padR, y2: y(v),
      class: "cp-grid" }));
    const t = svgNS("text", { x: padL - 6, y: y(v) + 4, class: "cp-tick", "text-anchor": "end" });
    t.textContent = String(v);
    svg.appendChild(t);
  }
  // x index labels (1..6)
  conditions.forEach((c, i) => {
    const t = svgNS("text", { x: x(i), y: H - padB + 20, class: "cp-tick", "text-anchor": "middle" });
    t.textContent = String(i + 1);
    svg.appendChild(t);
  });

  series.forEach((s, si) => {
    const color = SERIES_COLORS[si % SERIES_COLORS.length];
    let d = "";
    s.points.forEach((p, i) => {
      d += (i === 0 ? "M" : "L") + x(i).toFixed(1) + " " + y(p.value).toFixed(1) + " ";
    });
    svg.appendChild(svgNS("path", { d: d.trim(), fill: "none", stroke: color, "stroke-width": "2.5" }));
    s.points.forEach((p, i) => {
      svg.appendChild(svgNS("circle", { cx: x(i), cy: y(p.value), r: "3.5", fill: color }));
    });
  });
  host.appendChild(svg);

  // condition index legend
  const condLegend = el("ol", { className: "cp-cond-legend" });
  conditions.forEach((c, i) => {
    const li = el("li");
    li.appendChild(el("span", { className: "cp-idx", text: String(i + 1) }));
    li.appendChild(document.createTextNode(cp.condition_labels[c]));
    condLegend.appendChild(li);
  });
  host.appendChild(condLegend);

  // series legend
  const legend = el("ul", { className: "cp-legend" });
  series.forEach((s, si) => {
    const li = el("li");
    const dot = el("span", { className: "cp-dot" });
    dot.style.background = SERIES_COLORS[si % SERIES_COLORS.length];
    li.appendChild(dot);
    li.appendChild(document.createTextNode(s.label));
    legend.appendChild(li);
  });
  host.appendChild(legend);
  const note = el("p", { className: "cp-note", text: cp.scale_note + "（纵轴聚焦 3–6）" });
  host.appendChild(note);
}

// ---------------------------------------------------------------------------
// 5B. Historical figures (3 PNGs)
// ---------------------------------------------------------------------------
let figureDialog, figureDialogImg, figureDialogCap;

function renderFigures(figures) {
  const host = requireSlot("figures");
  host.textContent = "";
  figures.forEach((fig, i) => {
    const fc = el("figure", { className: "figure" + (i === 0 ? " wide" : "") });
    const btn = el("button", { className: "fig-btn" });
    btn.type = "button";
    btn.setAttribute("aria-label", "放大：" + fig.title);
    const img = el("img");
    img.src = fig.file;
    img.alt = fig.alt;
    img.loading = "lazy";
    btn.appendChild(img);
    btn.addEventListener("click", () => openFigure(fig));
    fc.appendChild(btn);
    if (fig.read_note) fc.appendChild(el("p", { className: "fig-read", text: "读图：" + fig.read_note }));
    const cap = el("figcaption");
    cap.textContent = fig.title + " — " + fig.boundary_note + "（来源：" + fig.source_file + "）";
    fc.appendChild(cap);
    host.appendChild(fc);
  });
}

function openFigure(fig) {
  if (!figureDialog || typeof figureDialog.showModal !== "function") return;
  figureDialogImg.src = fig.file;
  figureDialogImg.alt = fig.alt;
  figureDialogCap.textContent = fig.title + " — " + fig.boundary_note + "（来源：" + fig.source_file + "）";
  figureDialog.showModal();
}

// ---------------------------------------------------------------------------
// 5C. Identity effect
// ---------------------------------------------------------------------------
function renderIdentityEffect(analysis) {
  const host = requireSlot("identity-effect");
  host.textContent = "";
  const ie = analysis.identity_effect;
  const maxEta = Math.max.apply(null, ie.effects.map((e) => e.partial_eta_sq).concat([0.0001]));
  ie.effects.forEach((e) => {
    const row = el("div", { className: "ie-row" });
    row.appendChild(el("span", { className: "ie-label", text: e.label }));
    const track = el("div", { className: "ie-track" });
    const fill = el("div", { className: "ie-fill" });
    fill.style.width = Math.max(2, Math.round((e.partial_eta_sq / maxEta) * 100)) + "%";
    track.appendChild(fill);
    row.appendChild(track);
    const meta = el("span", { className: "ie-meta" });
    meta.textContent = "η² = " + e.partial_eta_sq.toFixed(3) + " · " + fmtP(e.p)
      + " · 较高：" + e.higher_identity;
    row.appendChild(meta);
    host.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// 5D. Planned contrasts (forest-style)
// ---------------------------------------------------------------------------
function renderPlannedContrasts(analysis) {
  const host = requireSlot("planned-contrasts");
  host.textContent = "";
  const pc = analysis.planned_contrasts;
  let maxAbs = 0.0001;
  pc.groups.forEach((g) => g.contrasts.forEach((c) => {
    maxAbs = Math.max(maxAbs, Math.abs(c.diff));
  }));
  pc.groups.forEach((g) => {
    const block = el("div", { className: "pcx-group" });
    block.appendChild(el("h4", { text: g.label }));
    g.contrasts.forEach((c) => {
      const row = el("div", { className: "pcx-row" });
      row.appendChild(el("span", { className: "pcx-label", text: c.label }));
      const axis = el("div", { className: "pcx-axis" });
      const zero = el("div", { className: "pcx-zero" });
      axis.appendChild(zero);
      const point = el("div", { className: "pcx-point" + (c.p < 0.05 ? " sig" : "") });
      const half = (c.diff / maxAbs) * 48; // % from centre
      point.style.left = (50 + half) + "%";
      point.title = "Δ = " + c.diff.toFixed(3);
      axis.appendChild(point);
      row.appendChild(axis);
      row.appendChild(el("span", { className: "pcx-stat",
        text: "Δ = " + c.diff.toFixed(3) + " · t = " + c.t.toFixed(2) + " · " + fmtP(c.p) }));
      block.appendChild(row);
    });
    host.appendChild(block);
  });
}

// ---------------------------------------------------------------------------
// 5E. Controlled regression
// ---------------------------------------------------------------------------
function renderControlledRegression(analysis) {
  const host = requireSlot("controlled-regression");
  host.textContent = "";
  const cr = analysis.controlled_regression;
  cr.rows.forEach((r) => {
    const row = el("div", { className: "cr-row" });
    row.appendChild(el("span", { className: "cr-dv", text: r.label }));
    const specs = el("div", { className: "cr-specs" });
    r.specs.forEach((s) => {
      const chip = el("div", { className: "cr-chip " + (s.survives ? "keeps" : "drops") });
      chip.appendChild(el("span", { className: "cr-spec", text: cr.spec_labels[s.spec] }));
      chip.appendChild(el("span", { className: "cr-fig",
        text: "F = " + s.process_F.toFixed(2) + " · " + fmtP(s.process_p) }));
      chip.appendChild(el("span", { className: "cr-tag",
        text: s.survives ? "显著保留" : "不再显著" }));
      specs.appendChild(chip);
    });
    row.appendChild(specs);
    host.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// 5F. Mediation path diagnostic
// ---------------------------------------------------------------------------
function renderMediation(analysis) {
  const host = requireSlot("mediation-path");
  host.textContent = "";
  const med = analysis.mediation;
  med.paths.forEach((p) => {
    const wrap = el("div", { className: "path-row" });
    wrap.appendChild(el("h4", { text: p.label }));
    const chain = el("div", { className: "path-chain" });
    [med.predictor, p.mid, med.outcome].forEach((label, i, arr) => {
      chain.appendChild(el("span", { className: "path-node", text: label }));
      if (i < arr.length - 1) chain.appendChild(el("span", { className: "path-arrow", text: "→" }));
    });
    wrap.appendChild(chain);
    const stat = el("p", { className: "path-stat " + (p.crosses_zero ? "crosses" : "clear") });
    stat.textContent = "间接效应 = " + p.indirect.toFixed(4) + "，95% 自助区间 ["
      + p.ci_low.toFixed(4) + ", " + p.ci_high.toFixed(4) + "]，"
      + (p.crosses_zero ? "区间跨 0" : "区间未跨 0")
      + "（a = " + p.a.toFixed(3) + "，b = " + p.b.toFixed(3) + "）";
    wrap.appendChild(stat);
    wrap.appendChild(el("p", { className: "path-tag", text: "关联性间接路径诊断 · 非因果中介、非机制证明" }));
    host.appendChild(wrap);
  });
}

// ---------------------------------------------------------------------------
// 5G. Stability list + 6. results takeaways
// ---------------------------------------------------------------------------
function renderList(slot, items) {
  const host = requireSlot(slot);
  host.textContent = "";
  (items || []).forEach((t) => host.appendChild(el("li", { text: t })));
}

// ---------------------------------------------------------------------------
// 7. Evaluation core: pipeline, artifacts, hashes
// ---------------------------------------------------------------------------
function renderPipeline(repro) {
  const host = requireSlot("pipeline-stages");
  host.textContent = "";
  repro.pipeline_stages.forEach((s, i) => {
    const li = el("li", { className: "pl-node" });
    const head = el("div", { className: "pl-head" });
    head.appendChild(el("span", { className: "pl-idx", text: String(i + 1) }));
    head.appendChild(el("span", { className: "pl-stage", text: s.stage }));
    head.appendChild(el("code", { text: s.code_object }));
    li.appendChild(head);
    li.appendChild(el("p", { className: "pl-role", text: s.role }));
    host.appendChild(li);
  });
}

function renderArtifactLifecycle(repro) {
  const host = requireSlot("artifact-lifecycle");
  host.textContent = "";
  repro.artifact_lifecycle.forEach((a) => {
    const li = el("li", { className: "artifact-node" });
    li.appendChild(el("span", { className: "af-label", text: a.label }));
    li.appendChild(el("code", { text: a.role }));
    host.appendChild(li);
  });
}

function renderHashFields(repro) {
  const host = requireSlot("hash-fields");
  host.textContent = "";
  repro.hash_fields.forEach((h) => {
    const chip = el("div", { className: "hash-chip" });
    chip.appendChild(el("span", { className: "hash-label", text: h.label }));
    chip.appendChild(el("code", { text: h.field }));
    host.appendChild(chip);
  });
  const note = el("p", { className: "hash-note", text: repro.hash_note });
  host.appendChild(note);
}

// ---------------------------------------------------------------------------
// 8. Mock engineering validation
// ---------------------------------------------------------------------------
function pct(v) { return v == null ? "—" : Math.round(Number(v) * 100) + "%"; }

function renderMockQuality(engineering) {
  const host = requireSlot("mock-quality");
  host.textContent = "";
  const eq = engineering.mock_execution_quality || {};
  const oq = engineering.mock_output_quality || {};
  const head = el("p", { className: "mq-head" });
  head.textContent = "确定性 mock 验收：计划 " + (eq.planned_record_count != null ? eq.planned_record_count : "—")
    + " 条 · 完成 " + (eq.completed_record_count != null ? eq.completed_record_count : "—")
    + " 条 · 失败 " + (eq.failed_record_count != null ? eq.failed_record_count : "—") + " 条";
  host.appendChild(head);
  [
    ["完成率", eq.completion_rate],
    ["首答解析成功率", oq.first_attempt_parse_success_rate],
    ["最终解析成功率", oq.final_parse_success_rate],
    ["最终 schema 合规率", oq.final_schema_compliance_rate],
    ["范围有效率", oq.range_validity_rate],
    ["缺失题项率", oq.missing_item_rate],
    ["repair 触发率", oq.repair_trigger_rate],
  ].forEach(([label, value]) => {
    const row = el("div", { className: "mq-row" });
    row.appendChild(el("span", { className: "mq-label", text: label }));
    const track = el("div", { className: "mq-track" });
    const fill = el("div", { className: "mq-fill" });
    fill.style.width = (value == null ? 0 : Math.round(Number(value) * 100)) + "%";
    track.appendChild(fill);
    row.appendChild(track);
    row.appendChild(el("span", { className: "mq-val", text: pct(value) }));
    host.appendChild(row);
  });
  host.appendChild(el("p", { className: "mq-tag",
    text: "确定性 mock 工程验证；非真实模型结果，不进入研究结论。" }));
}

// ---------------------------------------------------------------------------
// 9. Real provider readiness (single section)
// ---------------------------------------------------------------------------
const READINESS_STATE_CLASS = {
  offline_validated: "ok", available: "ok",
  not_configured: "pending", not_run: "pending",
  requires_runtime_verification: "pending", not_applicable: "muted",
};
const READINESS_ROW_LABELS = [
  ["Provider adapter", "adapter_status"],
  ["Credentials", "credential_status"],
  ["Model", "model_id_status"],
  ["Pricing", "pricing_status"],
  ["Dry-run", "dry_run_planning"],
  ["Live API", "live_api_status"],
  ["Live smoke", "smoke_status"],
  ["Live pilot", "pilot_status"],
  ["Result analysis", "result_analysis_status"],
];

function renderReadiness(engineering, repro) {
  const rp = repro.real_provider;
  setSlot("readiness-statement", rp.statement);

  const flow = requireSlot("readiness-flow");
  flow.textContent = "";
  rp.flow.forEach((step, i) => {
    const li = el("li", { className: "flow-step" });
    li.appendChild(el("span", { className: "flow-idx", text: String(i + 1) }));
    li.appendChild(el("span", { className: "flow-name", text: step }));
    flow.appendChild(li);
  });

  const status = requireSlot("readiness-status");
  status.textContent = "";
  const rr = engineering.real_provider_readiness || {};
  READINESS_ROW_LABELS.forEach(([label, key]) => {
    const v = rr[key] == null ? "null" : String(rr[key]);
    const cls = READINESS_STATE_CLASS[v] || "pending";
    const cell = el("div", { className: "readiness-cell is-" + cls });
    cell.appendChild(el("span", { className: "readiness-label", text: label }));
    cell.appendChild(el("span", { className: "readiness-value", text: v }));
    status.appendChild(cell);
  });

  const checklist = requireSlot("readiness-checklist");
  checklist.textContent = "";
  rp.checklist.forEach((c) => {
    const li = el("li", { className: "readiness-req" });
    li.appendChild(el("span", { className: "req-label", text: c.label }));
    li.appendChild(el("code", { text: c.step }));
    checklist.appendChild(li);
  });

  const plan = requireSlot("readiness-plan");
  plan.textContent = "";
  rp.dry_run_plan.forEach((p) => {
    const card = el("div", { className: "plan-card" });
    card.appendChild(el("span", { className: "plan-name", text: p.name }));
    card.appendChild(el("span", { className: "plan-records", text: p.records + " 条计划" }));
    card.appendChild(el("span", { className: "plan-note", text: "6 × 2 单元格 · 每格 " + p.n_per_cell }));
    card.appendChild(el("span", { className: "plan-desc", text: p.note }));
    plan.appendChild(card);
  });

  setSlot("readiness-future", "未来真实运行将记录：" + rp.future_record_fields.join("、")
    + "；详见运行手册 " + rp.runbook + "。");
}

// ---------------------------------------------------------------------------
// 10. Provenance four-state matrix
// ---------------------------------------------------------------------------
const PROV_STATUS_LABEL = {
  repository_verified: "仓库可核查",
  author_attested: "作者记录",
  reconstructed: "现有材料重建",
  unknown: "当前未知",
};

function renderProvenance(evidence) {
  const pc = evidence.provenance_completeness || { dimensions: [] };

  const counts = requireSlot("provenance-counts");
  counts.textContent = "";
  [
    ["repository_verified", pc.repository_verified_count],
    ["author_attested", pc.author_attested_count],
    ["reconstructed", pc.reconstructed_count],
    ["unknown", pc.unknown_count],
  ].forEach(([state, n]) => {
    const chip = el("div", { className: "pv-count prov-" + state });
    chip.appendChild(el("span", { className: "pv-count-n", text: String(n) }));
    chip.appendChild(el("span", { className: "pv-count-l", text: PROV_STATUS_LABEL[state] }));
    counts.appendChild(chip);
  });

  const host = requireSlot("provenance-matrix");
  host.textContent = "";
  const groups = {};
  const order = [];
  pc.dimensions.forEach((d) => {
    const g = d.group || "其他";
    if (!groups[g]) { groups[g] = []; order.push(g); }
    groups[g].push(d);
  });
  order.forEach((g) => {
    const block = el("div", { className: "pv-group" });
    block.appendChild(el("h4", { text: g }));
    const grid = el("div", { className: "pv-grid" });
    groups[g].forEach((d) => {
      const status = d.verification_status || "unknown";
      const cls = PROV_STATUS_LABEL[status] ? status : "unknown";
      const cell = el("div", { className: "prov-cell prov-" + cls });
      cell.appendChild(el("span", { className: "prov-dim", text: d.label || d.dimension }));
      cell.appendChild(el("span", { className: "prov-type", text: PROV_STATUS_LABEL[status] || status }));
      grid.appendChild(cell);
    });
    block.appendChild(grid);
    host.appendChild(block);
  });
}

// ---------------------------------------------------------------------------
// 11. Reproducibility: commands, key dirs, docs
// ---------------------------------------------------------------------------
function renderReproCommands(repro) {
  const host = requireSlot("repro-commands");
  host.textContent = "";
  repro.repro_commands.forEach((c) => {
    const row = el("div", { className: "cmd-row" });
    row.appendChild(el("span", { className: "cmd-label", text: c.label }));
    row.appendChild(el("code", { className: "cmd-code", text: c.cmd }));
    host.appendChild(row);
  });
}

function renderKeyDirectories(repro) {
  const host = requireSlot("key-directories");
  host.textContent = "";
  repro.key_directories.forEach((d) => {
    const li = el("li", { className: "kd-row" });
    li.appendChild(el("code", { text: d.path }));
    li.appendChild(el("span", { className: "kd-note", text: d.note }));
    host.appendChild(li);
  });
}

function renderDocEntries(repro) {
  const host = requireSlot("doc-entries");
  host.textContent = "";
  repro.doc_entries.forEach((d) => {
    const li = el("li", { className: "doc-row" });
    li.appendChild(el("span", { className: "doc-label", text: d.label }));
    li.appendChild(el("code", { text: d.path }));
    host.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Navigation + dialog + diagnostics
// ---------------------------------------------------------------------------
function setupNav() {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
  const links = Array.from(document.querySelectorAll('.site-nav a[href^="#"]'));
  const map = new Map();
  links.forEach((a) => {
    const sec = document.getElementById(a.getAttribute("href").slice(1));
    if (sec) map.set(sec, a);
  });
  if ("IntersectionObserver" in window && map.size) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          links.forEach((l) => l.classList.remove("active"));
          const active = map.get(entry.target);
          if (active) active.classList.add("active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
    map.forEach((_a, sec) => obs.observe(sec));
  }
}

function setupDialog() {
  figureDialog = document.getElementById("figure-dialog");
  figureDialogImg = document.getElementById("figure-dialog-img");
  figureDialogCap = document.getElementById("figure-dialog-cap");
  if (figureDialog) {
    figureDialog.addEventListener("click", (e) => {
      if (e.target === figureDialog) figureDialog.close();
    });
  }
}

function diagnosticsEnabled() {
  return window.location.search.indexOf("diagnostics=1") !== -1;
}

function writeLayoutDiagnostics() {
  if (!diagnosticsEnabled()) return;
  const root = document.documentElement;
  root.dataset.docClientWidth = String(root.clientWidth);
  root.dataset.docScrollWidth = String(root.scrollWidth);
  const slots = ["condition-profile", "provenance-matrix", "mock-quality",
    "identity-effect", "planned-contrasts", "controlled-regression", "figures"];
  const empties = slots.filter((s) => {
    const n = slotEl(s);
    return !n || n.childElementCount === 0;
  });
  root.dataset.emptyCharts = empties.join(",");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  setupNav();
  setupDialog();
  try {
    const [summary, story, measurement, analysis, results, engineering, evidence, repro] =
      await Promise.all([
        loadJSON("data/site_summary.json"),
        loadJSON("data/showcase_story.json"),
        loadJSON("data/measurement_summary.json"),
        loadJSON("data/analysis_results.json"),
        loadJSON("data/historical_results.json"),
        loadJSON("data/engineering_status.json"),
        loadJSON("data/evidence_matrix.json"),
        loadJSON("data/reproducibility_summary.json"),
      ]);

    renderHero(story, summary);
    renderDesign(summary);
    renderScenarios(story);
    renderConstructTable(measurement);
    renderHistoryComposition(summary);
    renderReliability(measurement);
    renderConditionProfile(analysis);
    renderFigures(results.figures);
    renderIdentityEffect(analysis);
    renderPlannedContrasts(analysis);
    renderControlledRegression(analysis);
    renderMediation(analysis);
    renderList("stability-list", analysis.stability.points);
    renderList("results-takeaways", story.result_takeaways);
    renderPipeline(repro);
    renderArtifactLifecycle(repro);
    renderHashFields(repro);
    renderMockQuality(engineering);
    renderReadiness(engineering, repro);
    renderProvenance(evidence);
    renderReproCommands(repro);
    renderKeyDirectories(repro);
    renderDocEntries(repro);

    document.documentElement.dataset.renderComplete = "true";
    requestAnimationFrame(() => requestAnimationFrame(writeLayoutDiagnostics));
  } catch (err) {
    document.documentElement.dataset.renderComplete = "false";
    const banner = document.getElementById("load-error");
    if (banner) {
      banner.hidden = false;
      const directFile = window.location.protocol === "file:";
      banner.textContent = directFile
        ? "页面初始化失败：" + err.message + "。请通过本地静态服务器访问，例如 python -m http.server 8000 --directory site"
        : "页面初始化失败：" + err.message + "。请检查页面结构、data-slot 与 site/data 文件是否一致。";
    }
  }
}

document.addEventListener("DOMContentLoaded", main);
