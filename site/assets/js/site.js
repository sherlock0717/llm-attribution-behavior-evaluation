// Static showcase behaviour (SITE-005 redesign).
// Native JS only: no third-party libraries, no CDN, no remote API, no ES module
// imports from URLs. Loads the four static JSON files and populates the page.
// Numbers are never hardcoded in HTML; they come from site/data/*.json produced
// by scripts/build_site_data.py.

"use strict";

const STATUS_LABELS = {
  historical: "历史基线数据",
  completed: "已完成（本地）",
  current: "进行中",
  planned: "规划中",
  pending_verification: "已配置，远程验证待完成",
};

function el(tag, opts = {}) {
  const node = document.createElement(tag);
  if (opts.className) node.className = opts.className;
  if (opts.text != null) node.textContent = opts.text;
  return node;
}

function badge(status) {
  const b = el("span", { className: "badge badge-" + status });
  b.textContent = STATUS_LABELS[status] || status;
  return b;
}

function setSlot(name, value) {
  document.querySelectorAll('[data-slot="' + name + '"]').forEach((n) => {
    n.textContent = value;
  });
}

function slotEl(name) {
  return document.querySelector('[data-slot="' + name + '"]');
}

// Required dynamic containers must exist; throw a clear error instead of a
// generic "Cannot set properties of null" if the HTML slot is missing.
function requireSlot(name) {
  const node = slotEl(name);
  if (!node) {
    throw new Error('Missing required page slot: data-slot="' + name + '"');
  }
  return node;
}

async function loadJSON(path) {
  const resp = await fetch(path, { cache: "no-store" });
  if (!resp.ok) throw new Error("HTTP " + resp.status + " for " + path);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Hero
// ---------------------------------------------------------------------------
function renderHero(summary) {
  setSlot("version", summary.project_version);
  setSlot("source-commit", summary.source_commit);
  setSlot("data-as-of", summary.data_as_of_date);
  setSlot("generated-at", summary.generated_at);

  const metrics = [
    ["历史记录", summary.historical_record_count],
    ["设计", summary.process_condition_count + " × " + summary.identity_condition_count],
    ["每格样本", summary.n_per_cell],
    ["历史基线", summary.historical_provider],
  ];
  const dl = requireSlot("hero-metrics");
  dl.textContent = "";
  metrics.forEach(([label, value]) => {
    const wrap = el("div", { className: "metric" });
    wrap.appendChild(el("dt", { text: label }));
    wrap.appendChild(el("dd", { text: String(value) }));
    dl.appendChild(wrap);
  });
}

// ---------------------------------------------------------------------------
// Experimental design (stats + 6x2 matrix)
// ---------------------------------------------------------------------------
function renderDesign(summary) {
  const d = summary.design;
  if (d && d.process_conditions) {
    CONDITION_LABELS = {};
    d.process_conditions.forEach((c) => { CONDITION_LABELS[c.key] = c.label; });
  }
  const stats = requireSlot("design-stats");
  if (d) {
    stats.textContent = "";
    const items = [
      [d.total_records, "历史记录"],
      [d.process_conditions.length + " × " + d.identity_labels.length, "过程 × 身份"],
      [d.n_per_cell, "每格样本"],
      [d.process_conditions.length * d.identity_labels.length, "条件格"],
    ];
    items.forEach(([num, lbl]) => {
      const wrap = el("div");
      wrap.appendChild(el("span", { className: "num", text: String(num) }));
      wrap.appendChild(el("span", { className: "lbl", text: lbl }));
      stats.appendChild(wrap);
    });
  }

  const table = requireSlot("design-matrix");
  if (!d) return;
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
    const code = el("code", { text: c.key });
    th.appendChild(code);
    th.appendChild(document.createTextNode(" " + c.label));
    th.appendChild(el("span", { className: "cond-note", text: c.note }));
    tr.appendChild(th);
    d.identity_labels.forEach(() => {
      tr.appendChild(el("td", { className: "cell", text: "n = " + d.n_per_cell }));
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  renderProcessGradient(d);
}

// Length-control diagnostic condition: only adds length, not real structure.
const LENGTH_CONTROL_KEY = "direct_choice_long";

function renderProcessGradient(d) {
  const host = requireSlot("process-gradient");
  if (!d || !d.process_conditions) return;
  host.textContent = "";

  const scale = el("div", { className: "grad-scale" });
  scale.appendChild(el("span", { className: "grad-end low", text: "低结构" }));
  scale.appendChild(el("span", { className: "grad-end high", text: "高结构" }));
  host.appendChild(scale);

  const track = el("div", { className: "grad-track" });
  d.process_conditions.forEach((c, i) => {
    const isDiag = c.key === LENGTH_CONTROL_KEY;
    const node = el("div", { className: "grad-node" + (isDiag ? " diagnostic" : "") });
    node.style.setProperty("--lvl", String(i));
    const head = el("div", { className: "grad-head" });
    head.appendChild(el("span", { className: "grad-idx", text: String(i + 1) }));
    head.appendChild(el("code", { text: c.key }));
    node.appendChild(head);
    node.appendChild(el("div", { className: "grad-label", text: c.label }));
    node.appendChild(el("div", { className: "grad-note", text: c.note }));
    if (isDiag) {
      node.appendChild(el("span", { className: "grad-tag", text: "Length-control diagnostic" }));
    }
    track.appendChild(node);
  });
  host.appendChild(track);
}

// ---------------------------------------------------------------------------
// Historical results (claims + bars + figures)
// ---------------------------------------------------------------------------
const EVIDENCE_ZH = {
  descriptive: "描述性",
  derived: "派生汇总",
  planned_contrast: "计划对比",
  exploratory_path_diagnostic: "探索性路径诊断",
};

// Chinese condition labels, populated from summary.design in renderDesign.
let CONDITION_LABELS = {};

const WIDE_CLAIMS = new Set(["agency-condition-means", "factual-check"]);

function renderResults(results) {
  const container = requireSlot("results");
  container.textContent = "";
  results.claims.forEach((claim) => {
    const card = el("article", { className: "claim" + (WIDE_CLAIMS.has(claim.id) ? " wide" : "") });
    card.appendChild(el("h3", { text: claim.title }));
    card.appendChild(el("p", { className: "summary", text: claim.summary }));

    if (claim.metrics && claim.metrics.length) {
      const details = el("details");
      const sm = el("summary", { text: "展开统计" });
      details.appendChild(sm);
      const ul = el("ul", { className: "metrics" });
      claim.metrics.forEach((m) => ul.appendChild(el("li", { text: m.display })));
      details.appendChild(ul);
      card.appendChild(details);
    }

    const meta = el("p", { className: "meta" });
    const line1 = el("span");
    line1.appendChild(badge(mapEvidence(claim.evidence_level)));
    line1.appendChild(document.createTextNode(" 证据等级：" + (EVIDENCE_ZH[claim.evidence_level] || claim.evidence_level)));
    meta.appendChild(line1);
    meta.appendChild(el("span", { text: "来源：" + (claim.source_refs || []).join("、") }));
    meta.appendChild(el("span", { text: claim.boundary_note }));
    card.appendChild(meta);

    container.appendChild(card);
  });

  renderBars(results.claims);
  renderFigures(results.figures);
  renderPathDiagram(results.claims);
}

function pathRow(title, mid, metric) {
  const wrap = el("div", { className: "path-row" });
  wrap.appendChild(el("h4", { text: title }));
  const chain = el("div", { className: "path-chain" });
  ["过程结构", mid, "自由意志归因"].forEach((label, i, arr) => {
    chain.appendChild(el("span", { className: "path-node", text: label }));
    if (i < arr.length - 1) chain.appendChild(el("span", { className: "path-arrow", text: "→" }));
  });
  wrap.appendChild(chain);
  if (metric) {
    const crosses = metric.crosses_zero;
    const stat = el("p", { className: "path-stat" + (crosses ? " crosses" : " clear") });
    const est = Number(metric.estimate).toFixed(4);
    const lo = Number(metric.ci_low).toFixed(4);
    const hi = Number(metric.ci_high).toFixed(4);
    stat.textContent = "间接效应 = " + est + "，95% CI [" + lo + ", " + hi + "]，"
      + (crosses ? "区间跨 0" : "区间未跨 0");
    wrap.appendChild(stat);
  }
  wrap.appendChild(el("p", { className: "path-tag", text: "Exploratory · 非机制证明，不作因果断言" }));
  return wrap;
}

function renderPathDiagram(claims) {
  const host = requireSlot("path-diagram");
  host.textContent = "";
  const med = claims.find((c) => c.id === "parallel-mediation");
  if (!med) return;
  const agency = med.metrics.find((m) => m.name === "agency_indirect");
  const intel = med.metrics.find((m) => m.name === "perceived_intelligence_indirect");
  host.appendChild(pathRow("主路径（primary exploratory path）", "行动者感", agency));
  host.appendChild(pathRow("次路径（secondary exploratory path）", "感知智能", intel));
}

function mapEvidence(level) {
  switch (level) {
    case "exploratory_path_diagnostic":
      return "planned";
    default:
      return "historical";
  }
}

function barGroup(title, metrics, altColor) {
  const wrap = el("div", { className: "bar-group" });
  wrap.appendChild(el("h4", { text: title }));
  const values = metrics.map((m) => Math.abs(Number(m.value)) || 0);
  const max = Math.max(...values, 0.0001);
  metrics.forEach((m) => {
    const row = el("div", { className: "bar-row" });
    const label = el("span", { className: "bar-label" });
    label.appendChild(document.createTextNode(CONDITION_LABELS[m.name] || m.name));
    if (CONDITION_LABELS[m.name]) label.appendChild(el("code", { text: m.name }));
    row.appendChild(label);
    const track = el("div", { className: "bar-track" });
    const fill = el("div", { className: "bar-fill" + (altColor ? " alt" : "") });
    const pct = Math.max(2, Math.round((Math.abs(Number(m.value)) / max) * 100));
    fill.style.width = pct + "%";
    track.appendChild(fill);
    row.appendChild(track);
    row.appendChild(el("span", { className: "bar-val", text: (Number(m.value)).toFixed(2) }));
    wrap.appendChild(row);
  });
  return wrap;
}

function renderBars(claims) {
  const host = requireSlot("result-bars");
  host.textContent = "";
  const agency = claims.find((c) => c.id === "agency-condition-means");
  const factual = claims.find((c) => c.id === "factual-check");
  if (agency && agency.metrics.length) {
    host.appendChild(barGroup("行动者感（agency）按条件均值", agency.metrics, false));
  }
  if (factual && factual.metrics.length) {
    host.appendChild(barGroup("操纵检验：过程完整性事实检查", factual.metrics, true));
  }
}

let figureDialog, figureDialogImg, figureDialogCap;

function renderFigures(figures) {
  const figWrap = requireSlot("figures");
  figWrap.textContent = "";
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
    figWrap.appendChild(fc);
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
// Version history
// ---------------------------------------------------------------------------
function renderVersions(vh) {
  const ol = requireSlot("version-timeline");
  ol.textContent = "";
  vh.versions.forEach((v) => {
    const li = el("li");
    if (v.is_future) li.className = "future";
    const head = el("div");
    head.appendChild(el("span", { className: "ver", text: v.version }));
    head.appendChild(document.createTextNode(v.title));
    li.appendChild(head);
    const ul = el("ul");
    v.highlights.forEach((h) => ul.appendChild(el("li", { text: h })));
    li.appendChild(ul);
    ol.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Roadmap
// ---------------------------------------------------------------------------
function renderRoadmapGroup(items, slot) {
  const container = requireSlot(slot);
  container.textContent = "";
  items.forEach((it) => {
    let cls = "rmcard";
    if (it.status === "current") cls += " is-current";
    else if (it.status === "planned") cls += " is-planned";
    const card = el("div", { className: cls });
    card.appendChild(el("h4", { text: it.name }));
    const badges = el("div", { className: "badges" });
    badges.appendChild(badge(it.status));
    if (it.local_status) badges.appendChild(badge(it.local_status));
    if (it.release_status) badges.appendChild(badge(it.release_status));
    card.appendChild(badges);
    card.appendChild(el("p", { text: it.summary }));
    if (it.evidence_ref && it.evidence_ref.length) {
      const details = el("details");
      details.appendChild(el("summary", { text: "交付与证据" }));
      const ul = el("ul");
      it.evidence_ref.forEach((r) => ul.appendChild(el("li", { text: r })));
      details.appendChild(ul);
      card.appendChild(details);
    }
    if (it.depends_on && it.depends_on.length) {
      card.appendChild(el("p", { className: "dep", text: "依赖：" + it.depends_on.join("、") }));
    }
    container.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// Engineering core & validation (FAST-001): evolution, mock quality,
// provenance completeness, artifact lifecycle. All mock values are labelled
// mock_engineering_validation and are never real-model results.
// ---------------------------------------------------------------------------
function pct(value) {
  if (value == null) return "—";
  return Math.round(Number(value) * 100) + "%";
}

function renderEvolution(engineering, evaluation) {
  const host = requireSlot("engineering-evolution");
  host.textContent = "";
  const stages = [
    { name: "历史研究基线", state: "done",
      note: "真实 DeepSeek API 历史数据；聚合结果与图表已产出。" },
    { name: "可复现工程核心", state: "done",
      note: "TaskSpec → Runner → Provider → Parser → Validation → Score → Manifest（当前成熟度 "
        + (engineering.current_maturity_level || "pre-BMK-L1") + "）。" },
    { name: "确定性 mock 验证", state: "done",
      note: "mock 验收运行完成度 " + pct(engineering.mock_execution_quality
        && engineering.mock_execution_quality.completion_rate) + "；仅验证工程链路。" },
    { name: "真实模型试点", state: "next",
      note: "尚未运行（" + (evaluation.planned_real_pilot
        ? evaluation.planned_real_pilot.status : "planned_not_run") + "）；需单独授权。" },
  ];
  stages.forEach((s, i) => {
    const li = el("li", { className: "evo-step is-" + s.state });
    const head = el("div", { className: "evo-head" });
    head.appendChild(el("span", { className: "evo-idx", text: String(i + 1) }));
    head.appendChild(el("span", { className: "evo-name", text: s.name }));
    li.appendChild(head);
    li.appendChild(el("p", { className: "evo-note", text: s.note }));
    host.appendChild(li);
  });
}

function renderMockQuality(engineering) {
  const host = requireSlot("mock-quality");
  host.textContent = "";
  const eq = engineering.mock_execution_quality || {};
  const oq = engineering.mock_output_quality || {};
  const rows = [
    ["完成率", eq.completion_rate],
    ["首答解析成功率", oq.first_attempt_parse_success_rate],
    ["最终解析成功率", oq.final_parse_success_rate],
    ["最终 schema 合规率", oq.final_schema_compliance_rate],
    ["缺失题项率", oq.missing_item_rate],
    ["范围有效率", oq.range_validity_rate],
    ["repair 触发率", oq.repair_trigger_rate],
  ];
  rows.forEach(([label, value]) => {
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
  const tag = el("p", { className: "mq-tag" });
  tag.textContent = "确定性 mock 工程验证（provider=" + (engineering.mock_output_quality ? "mock" : "mock")
    + "）；非真实模型结果。";
  host.appendChild(tag);
}

// Four distinct verification states. author_attested / reconstructed must NOT
// be shown as "verified"; each state gets its own class and label.
var PROV_STATUS_LABEL = {
  repository_verified: "仓库可验证",
  author_attested: "作者说明",
  reconstructed: "代码重建",
  unknown: "未知",
};

function renderProvenance(evidence) {
  const host = requireSlot("provenance-matrix");
  host.textContent = "";
  const pc = evidence.provenance_completeness || { dimensions: [] };
  pc.dimensions.forEach((d) => {
    const status = d.verification_status || "unknown";
    const cls = PROV_STATUS_LABEL[status] ? status : "unknown";
    const cell = el("div", { className: "prov-cell prov-" + cls });
    cell.appendChild(el("span", { className: "prov-dim", text: d.dimension }));
    cell.appendChild(el("span", {
      className: "prov-type",
      text: PROV_STATUS_LABEL[status] || status,
    }));
    host.appendChild(cell);
  });
}

function renderArtifactChain(engineering) {
  const host = requireSlot("artifact-chain");
  host.textContent = "";
  (engineering.artifact_lifecycle || []).forEach((role) => {
    host.appendChild(el("li", { className: "artifact-node", text: role }));
  });
}

function renderEngineeringCore(engineering, evaluation, evidence) {
  renderEvolution(engineering, evaluation);
  renderMockQuality(engineering);
  renderProvenance(evidence);
  renderArtifactChain(engineering);
}

// ---------------------------------------------------------------------------
// Real provider readiness (REAL-SETUP-001). Never renders a fabricated real
// metric: unrun values arrive as null / "not_run" / "not_applicable" and are
// shown as such. All data comes from engineering_status.real_provider_readiness.
// ---------------------------------------------------------------------------
var READINESS_STATE_CLASS = {
  offline_validated: "ok",
  not_configured: "pending",
  not_run: "pending",
  requires_runtime_verification: "pending",
  not_applicable: "muted",
  available: "ok",
};

function readinessValue(v) {
  if (v == null) return "null";
  return String(v);
}

function renderReadiness(engineering) {
  const rp = (engineering && engineering.real_provider_readiness) || {};
  const statusHost = requireSlot("readiness-status");
  statusHost.textContent = "";
  const rows = [
    ["Provider adapter", rp.adapter_status],
    ["Credentials", rp.credential_status],
    ["Model", rp.model_id_status],
    ["Pricing", rp.pricing_status],
    ["Dry-run planning", rp.dry_run_planning],
    ["Live API", rp.live_api_status],
    ["Live smoke", rp.smoke_status],
    ["Live pilot", rp.pilot_status],
    ["Result analysis", rp.result_analysis_status],
  ];
  rows.forEach(([label, value]) => {
    const v = readinessValue(value);
    const cls = READINESS_STATE_CLASS[v] || "pending";
    const cell = el("div", { className: "readiness-cell is-" + cls });
    cell.appendChild(el("span", { className: "readiness-label", text: label }));
    cell.appendChild(el("span", { className: "readiness-value", text: v }));
    statusHost.appendChild(cell);
  });

  const checklistHost = requireSlot("readiness-checklist");
  checklistHost.textContent = "";
  const reqs = [
    "verify_current_official_base_url",
    "verify_current_official_model_id",
    "verify_current_official_pricing",
    "configure_api_key_in_environment",
    "explicitly_enable_live_api",
    "explicitly_confirm_paid_run",
  ];
  reqs.forEach((r) => checklistHost.appendChild(el("li", { className: "readiness-req", text: r })));

  const planHost = requireSlot("readiness-plan");
  planHost.textContent = "";
  const plan = [
    ["smoke", 12, 1],
    ["pilot", 60, 5],
  ];
  plan.forEach(([name, records, nPerCell]) => {
    const card = el("div", { className: "plan-card" });
    card.appendChild(el("span", { className: "plan-name", text: name }));
    card.appendChild(el("span", { className: "plan-records", text: records + " 条计划" }));
    card.appendChild(el("span", { className: "plan-note", text: "6 × 2 单元格 · 每格 " + nPerCell }));
    planHost.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// Navigation: mobile toggle + scrollspy
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
    const id = a.getAttribute("href").slice(1);
    const sec = document.getElementById(id);
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

// ---------------------------------------------------------------------------
// Lightweight runtime + layout diagnostics (only when ?diagnostics=1).
function diagnosticsEnabled() {
  return window.location.search.indexOf("diagnostics=1") !== -1;
}

function writeLayoutDiagnostics() {
  if (!diagnosticsEnabled()) return;
  const root = document.documentElement;
  root.dataset.docClientWidth = String(root.clientWidth);
  root.dataset.docScrollWidth = String(root.scrollWidth);
  const matrix = document.querySelector(".matrix-scroll");
  const figures = document.querySelector(".figures");
  if (matrix) {
    matrix.dataset.clientWidth = String(matrix.clientWidth);
    matrix.dataset.scrollWidth = String(matrix.scrollWidth);
  }
  if (figures) {
    figures.dataset.clientWidth = String(figures.clientWidth);
    figures.dataset.scrollWidth = String(figures.scrollWidth);
  }
}

async function main() {
  setupNav();
  setupDialog();
  try {
    const [summary, roadmap, versions, results, engineering, evaluation, evidence] =
      await Promise.all([
        loadJSON("data/site_summary.json"),
        loadJSON("data/roadmap.json"),
        loadJSON("data/version_history.json"),
        loadJSON("data/historical_results.json"),
        loadJSON("data/engineering_status.json"),
        loadJSON("data/evaluation_summary.json"),
        loadJSON("data/evidence_matrix.json"),
      ]);
    renderHero(summary);
    renderDesign(summary);
    renderResults(results);
    renderEngineeringCore(engineering, evaluation, evidence);
    renderReadiness(engineering);
    renderVersions(versions);
    renderRoadmapGroup(roadmap.phases, "roadmap-phases");
    renderRoadmapGroup(roadmap.track_s, "roadmap-track");
    document.documentElement.dataset.renderComplete = "true";
    requestAnimationFrame(() => {
      requestAnimationFrame(writeLayoutDiagnostics);
    });
  } catch (err) {
    document.documentElement.dataset.renderComplete = "false";
    const banner = document.getElementById("load-error");
    if (banner) {
      banner.hidden = false;
      const directFile = window.location.protocol === "file:";
      if (directFile) {
        banner.textContent =
          "页面初始化失败：" + err.message +
          "。当前页面需要通过本地静态服务器访问，例如：" +
          " python -m http.server 8000 --directory site";
      } else {
        banner.textContent =
          "页面初始化失败：" + err.message +
          "。请检查页面结构、data-slot 与 site/data 文件是否一致。";
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", main);
