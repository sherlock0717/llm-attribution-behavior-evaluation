// Static showcase behaviour (SHOWCASE-FIX-001).
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

function repoPathURL(path, kind) {
  const clean = String(path || "").replace(/^\/+|\/+$/g, "");
  return ["https:", "", "github.com", "sherlock0717", "llm-attribution-behavior-evaluation",
    kind === "tree" ? "tree" : "blob", "main", clean].join("/");
}

// ---------------------------------------------------------------------------
// 1. Overview / hero core facts
// ---------------------------------------------------------------------------
function renderHero(story) {
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
// 2. Six process conditions (uniform cards)
// ---------------------------------------------------------------------------
function renderProcessConditions(summary) {
  const host = requireSlot("process-cards");
  host.textContent = "";
  summary.design.process_conditions.forEach((c, i) => {
    const card = el("div", { className: "pc-card" });
    const head = el("div", { className: "pc-head" });
    head.appendChild(el("span", { className: "pc-idx", text: String(i + 1) }));
    head.appendChild(el("span", { className: "pc-label", text: c.label }));
    card.appendChild(head);
    card.appendChild(el("code", { className: "pc-key", text: c.key }));
    card.appendChild(el("p", { className: "pc-note", text: c.note }));
    host.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// 3. Experimental design: stats + 6x2 matrix
// ---------------------------------------------------------------------------
function renderDesign(summary) {
  const d = summary.design;

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
}

// ---------------------------------------------------------------------------
// 3. Scenario case cards
// ---------------------------------------------------------------------------
function renderScenarios(story) {
  const host = requireSlot("scenario-cards");
  host.textContent = "";
  (story.scenarios || []).forEach((s) => {
    const card = el("article", { className: "sc-card" });
    const head = el("div", { className: "sc-head" });
    head.appendChild(el("span", { className: "sc-name", text: s.label }));
    head.appendChild(el("span", { className: "sc-domain", text: s.domain }));
    card.appendChild(head);
    card.appendChild(el("p", { className: "sc-context", text: s.context }));
    const opts = el("div", { className: "sc-options" });
    [["A", s.option_a], ["B", s.option_b]].forEach(([tag, txt]) => {
      const row = el("div", { className: "sc-opt" });
      row.appendChild(el("span", { className: "sc-opt-tag", text: tag }));
      row.appendChild(el("span", { className: "sc-opt-txt", text: txt }));
      opts.appendChild(row);
    });
    card.appendChild(opts);
    const choice = el("p", { className: "sc-choice" });
    choice.appendChild(el("span", { className: "sc-choice-tag", text: "材料中的选择" }));
    choice.appendChild(document.createTextNode(s.fixed_choice));
    card.appendChild(choice);
    const code = el("code", { className: "sc-id", text: s.id });
    card.appendChild(code);
    host.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// 3b. Research & measurement sources (equal cards + full references)
// ---------------------------------------------------------------------------
function renderResearchSources(story) {
  const rs = story.research_sources || {};
  setSlot("research-sources-intro", rs.intro || "");
  setSlot("research-sources-usage", rs.usage_note || "");

  const host = requireSlot("research-source-cards");
  host.textContent = "";
  (rs.sources || []).forEach((s) => {
    const card = el("article", { className: "src-card" });
    card.appendChild(el("h3", { className: "src-name", text: s.label }));
    card.appendChild(el("p", { className: "src-cite", text: s.citation_short }));
    const chips = el("ul", { className: "src-constructs" });
    (s.constructs || []).forEach((c) => chips.appendChild(el("li", { text: c })));
    card.appendChild(chips);
    card.appendChild(el("p", { className: "src-role", text: s.role }));
    card.appendChild(el("span", { className: "src-usage", text: s.usage }));
    host.appendChild(card);
  });

  const refs = requireSlot("research-references");
  refs.textContent = "";
  (rs.references || []).forEach((r) => {
    const li = el("li", { className: "ref-item" });
    li.appendChild(el("span", { className: "ref-full", text: r.full }));
    if (r.url) {
      const a = el("a", { className: "ref-link", text: r.doi ? "DOI: " + r.doi : "出版社入口" });
      a.href = r.url;
      a.target = "_blank";
      a.rel = "noopener";
      li.appendChild(a);
    }
    refs.appendChild(li);
  });

  const docs = requireSlot("research-source-docs");
  docs.textContent = "";
  (rs.detail_docs || []).forEach((d) => {
    const li = el("li", { className: "ref-doc" });
    li.appendChild(el("span", { className: "ref-doc-note", text: d.note }));
    const a = el("a", { className: "ref-doc-link" });
    a.href = repoPathURL(d.path, "blob");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
    docs.appendChild(li);
  });
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
// 5. Reliability bars
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
// 5. Six-condition core construct profile (SVG multi-series)
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

  for (let v = yMin; v <= yMax; v += 1) {
    svg.appendChild(svgNS("line", { x1: padL, y1: y(v), x2: W - padR, y2: y(v),
      class: "cp-grid" }));
    const t = svgNS("text", { x: padL - 6, y: y(v) + 4, class: "cp-tick", "text-anchor": "end" });
    t.textContent = String(v);
    svg.appendChild(t);
  }
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

  const condLegend = el("ol", { className: "cp-cond-legend" });
  conditions.forEach((c, i) => {
    const li = el("li");
    li.appendChild(el("span", { className: "cp-idx", text: String(i + 1) }));
    li.appendChild(document.createTextNode(cp.condition_labels[c]));
    condLegend.appendChild(li);
  });
  host.appendChild(condLegend);

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
  host.appendChild(el("p", { className: "cp-note", text: cp.scale_note + "（纵轴聚焦 3–6）" }));
}

// ---------------------------------------------------------------------------
// 5. Historical figures (3 PNGs)
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
    const cap = el("figcaption");
    cap.appendChild(el("span", { className: "fig-title", text: fig.title }));
    if (fig.read_note) cap.appendChild(el("span", { className: "fig-read", text: fig.read_note }));
    cap.appendChild(el("span", { className: "fig-src", text: "数据取自 " + fig.source_file }));
    fc.appendChild(cap);
    host.appendChild(fc);
  });
}

function openFigure(fig) {
  if (!figureDialog || typeof figureDialog.showModal !== "function") return;
  figureDialogImg.src = fig.file;
  figureDialogImg.alt = fig.alt;
  figureDialogCap.textContent = fig.title + "（数据取自 " + fig.source_file + "）";
  figureDialog.showModal();
}

// ---------------------------------------------------------------------------
// 5. Identity effect
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
// 5. Planned contrasts (forest-style)
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
      const half = (c.diff / maxAbs) * 48;
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
// 5. Controlled regression
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
// 5. Mediation path diagnostic
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
      + (p.crosses_zero ? "区间跨 0" : "区间未跨 0");
    wrap.appendChild(stat);
    host.appendChild(wrap);
  });
}

// ---------------------------------------------------------------------------
// 5G / 6. Ordered narrative lists
// ---------------------------------------------------------------------------
function renderList(slot, items) {
  const host = requireSlot(slot);
  host.textContent = "";
  (items || []).forEach((t) => host.appendChild(el("li", { text: t })));
}

// ---------------------------------------------------------------------------
// 7. Evaluation core: five steps, command block, artifact table, hash note
// ---------------------------------------------------------------------------
function renderEvalSteps(repro) {
  const host = requireSlot("eval-steps");
  host.textContent = "";
  repro.eval_steps.forEach((s, i) => {
    const li = el("li", { className: "es-node" });
    const head = el("div", { className: "es-head" });
    head.appendChild(el("span", { className: "es-idx", text: String(i + 1) }));
    head.appendChild(el("span", { className: "es-step", text: s.step }));
    li.appendChild(head);
    li.appendChild(el("p", { className: "es-note", text: s.note }));
    host.appendChild(li);
  });
}

function renderEvalCommands(repro) {
  const host = requireSlot("eval-commands");
  host.textContent = "";
  const pre = el("pre", { className: "cmd-block" });
  pre.appendChild(el("code", { text: repro.eval_commands.join("\n") }));
  host.appendChild(pre);
}

function renderArtifactTable(repro) {
  const table = requireSlot("artifact-table");
  const caption = table.querySelector("caption");
  table.textContent = "";
  if (caption) table.appendChild(caption);
  const thead = el("thead");
  const hr = el("tr");
  ["产物", "用途"].forEach((h) => hr.appendChild(el("th", { text: h })));
  thead.appendChild(hr);
  table.appendChild(thead);
  const tbody = el("tbody");
  repro.artifact_table.forEach((a) => {
    const tr = el("tr");
    tr.appendChild(el("td", { className: "af-label", text: a.label }));
    tr.appendChild(el("td", { text: a.purpose }));
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  setSlot("hash-note", repro.hash_note);
}

// ---------------------------------------------------------------------------
// 8. Mock run validation
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
}

// ---------------------------------------------------------------------------
// 9. Real model access (single statement + flow)
// ---------------------------------------------------------------------------
function renderReadiness(repro) {
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
}

// ---------------------------------------------------------------------------
// 11. From a single task to a general benchmark
// ---------------------------------------------------------------------------
function renderBenchmarkRoadmap(repro) {
  const host = requireSlot("benchmark-flow");
  host.textContent = "";
  repro.benchmark_roadmap.flow.forEach((step, i) => {
    const li = el("li", { className: "flow-step" });
    li.appendChild(el("span", { className: "flow-idx", text: String(i + 1) }));
    li.appendChild(el("span", { className: "flow-name", text: step }));
    host.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// 10. Reproducibility: commands, key dirs, docs
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
    const a = el("a", { className: "repo-path-link" });
    a.href = repoPathURL(d.path, "tree");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
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
    const a = el("a", { className: "repo-path-link" });
    a.href = repoPathURL(d.path, "blob");
    a.target = "_blank";
    a.rel = "noopener";
    a.appendChild(el("code", { text: d.path }));
    li.appendChild(a);
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
  const slots = ["process-cards", "scenario-cards", "research-source-cards",
    "condition-profile", "identity-effect", "planned-contrasts",
    "controlled-regression", "mediation-path", "figures", "mock-quality",
    "eval-steps", "readiness-flow", "benchmark-flow"];
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
    const [summary, story, measurement, analysis, results, engineering, repro] =
      await Promise.all([
        loadJSON("data/site_summary.json"),
        loadJSON("data/showcase_story.json"),
        loadJSON("data/measurement_summary.json"),
        loadJSON("data/analysis_results.json"),
        loadJSON("data/historical_results.json"),
        loadJSON("data/engineering_status.json"),
        loadJSON("data/reproducibility_summary.json"),
      ]);

    renderHero(story);
    renderProcessConditions(summary);
    renderDesign(summary);
    renderScenarios(story);
    renderResearchSources(story);
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
    renderEvalSteps(repro);
    renderEvalCommands(repro);
    renderArtifactTable(repro);
    renderMockQuality(engineering);
    renderReadiness(repro);
    renderBenchmarkRoadmap(repro);
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
