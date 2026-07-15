#!/usr/bin/env python
"""Build the showcase narrative JSON layer (SHOWCASE-RELEASE-001).

This script is READ-ONLY with respect to research assets. It:
  - only reads repository source files (outputs/, configs/, docs/, pyproject);
  - reuses the *validated* extractors in ``build_site_data`` so it never
    re-estimates models and never hand-writes a statistic;
  - never writes outputs/, never calls the network or any API;
  - fails loudly when a required file, column or cell is missing.

It produces four JSON documents that drive the continuous research + engineering
narrative of the public page (numbers are always JSON-sourced, never hardcoded
in HTML):

    site/data/showcase_story.json          -- top-level facts + result takeaways
    site/data/measurement_summary.json     -- constructs, items, ranges, reliability
    site/data/analysis_results.json        -- the full measurement -> results chain
    site/data/reproducibility_summary.json -- the evaluation engineering contract

Usage:
    python scripts/build_showcase_data.py
    python scripts/build_showcase_data.py --out site/data
    python scripts/build_showcase_data.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import build_site_data as bsd  # noqa: E402  (sibling script, validated extractors)
import stimuli  # noqa: E402  (v1 stimulus materials; scenario case content, read-only)
import yaml  # noqa: E402

BuildError = bsd.BuildError

# ---------------------------------------------------------------------------
# Static, human-maintained metadata (prose / labels / roles only — NO numbers
# that can be computed from the repository).
# ---------------------------------------------------------------------------

# Construct display metadata. `range` and `n_items` are validated against the
# repository (reliability_summary.csv); the label/role here are prose only.
CONSTRUCT_META = {
    "factual_manipulation_check": {
        "label": "事实操纵检验", "role": "操纵检验", "range": "0–2",
        "note": "只根据【决策过程】判断材料是否列出方案、比较理由、提到反思修正。"},
    "subjective_process_completeness": {
        "label": "主观过程完整性", "role": "操纵检验", "range": "1–7",
        "note": "观察者主观感到决策过程是否完整、可回应理由、非稀疏结论。"},
    "agency": {
        "label": "能动性", "role": "主要结果", "range": "1–7",
        "note": "决策者是否像在自我控制、按理由行动、可调整与修正。"},
    "free_will_attribution": {
        "label": "自由意志归因", "role": "主要结果", "range": "1–7",
        "note": "决策者是否被看作本可选择、按自己意向、拥有选择自由。"},
    "autonomy": {
        "label": "自主性", "role": "次要结果", "range": "1–7",
        "note": "决策者是否自主作出选择、非被情境或指令推着走。"},
    "experience": {
        "label": "体验感受", "role": "心智知觉对照", "range": "1–7",
        "note": "决策者是否被看作能感到痛苦、恐惧、愉悦等（心智知觉的体验维度）。"},
    "perceived_intelligence": {
        "label": "感知智能", "role": "协变量", "range": "1–7",
        "note": "决策者是否被看作理解情境、处理有逻辑、判断质量高。"},
    "outcome_accountability": {
        "label": "结果责任", "role": "责任子维度", "range": "1–7",
        "note": "决策者是否应为结果承担责任、与结果存在责任关系。"},
    "moral_praise_blame": {
        "label": "道德褒贬", "role": "责任子维度", "range": "1–7",
        "note": "决策者是否可因选择受到赞扬或责备、可被道德评价。"},
    "process_accountability": {
        "label": "过程可归责", "role": "责任子维度", "range": "1–7",
        "note": "决策者是否应为其判断过程作出解释、过程是否可归责。"},
}

# Aggregate super-construct (not one of the 34 items; sum of three subdims).
RESPONSIBILITY_TOTAL_META = {
    "key": "responsibility_total",
    "label": "责任归因总分",
    "range": "1–7",
    "note": "由结果责任、道德褒贬、过程可归责三个子维度聚合，属探索性结果。",
    "components": ["outcome_accountability", "moral_praise_blame", "process_accountability"],
}

# Constructs profiled across the six conditions (must all exist in the report
# means table). Order = reading order on the page.
PROFILE_CONSTRUCTS = [
    "subjective_process_completeness",
    "agency",
    "free_will_attribution",
    "perceived_intelligence",
    "responsibility_total",
]

# Identity main effect: report these constructs (all present in anova_summary).
IDENTITY_CONSTRUCTS = [
    "agency", "free_will_attribution", "autonomy", "experience",
    "outcome_accountability", "perceived_intelligence",
    "subjective_process_completeness",
]

# Controlled regression: process effect across specs for these DVs.
CONTROLLED_DVS = [
    "agency", "free_will_attribution", "responsibility_total",
    "autonomy", "process_accountability",
]
CONTROLLED_SPECS = ["dummy_process_only", "control_both"]

# Planned contrasts: registered contrasts actually present in the source file
# for these DVs. We NEVER invent a contrast not present in planned_contrasts.csv.
CONTRAST_DVS = ["agency", "free_will_attribution"]

CONTRAST_LABELS = {
    "alternatives_vs_direct_choice": "列出可选方案 vs 直接选择",
    "reasons_concise_vs_direct_choice_long": "简洁理由权衡 vs 长文本直接选择",
    "reflection_feedback_vs_reasons": "反思与反馈修正 vs 完整理由权衡",
    "reflection_feedback_vs_direct_choice_long": "反思与反馈修正 vs 长文本直接选择",
}

DV_LABELS = {k: v["label"] for k, v in CONSTRUCT_META.items()}
DV_LABELS["responsibility_total"] = RESPONSIBILITY_TOTAL_META["label"]

# Scenario display names (prose only; scenario_id set is validated from data).
# domain is shown separately on the card, so the label here is just the case name.
SCENARIO_LABELS = {
    "moral_friend_report": "是否举报朋友的错误",
    "self_control_deadline": "截止期限前的取舍",
    "relationship_honesty": "对朋友作品是否坦诚",
    "risk_project_choice": "稳妥还是创新方案",
    "responsibility_mistake": "是否主动承认失误",
    "obedience_unfair_order": "面对不公平的上级要求",
    "privacy_shortcut": "是否走隐私捷径",
    "team_credit": "团队功劳如何归属",
}

STABILITY_POINTS = [
    "能动性随过程结构总体上升，是方向最稳定的主结果；n=30 稳定性复核维持同一方向。",
    "自由意志归因的直接过程效应在加入控制变量后并不稳定，更像经由能动性间接发生，属探索性诊断。",
    "责任相关维度（结果责任、道德褒贬、过程可归责）方向不如能动性稳定，仅作探索性呈现。",
    "已识别的方法问题——历史 prompt 同时暴露构念名与判断规则、构念间高相关——在 v2 协议中通过盲化构念名与修订暴露策略处理。",
    "当前结论仅描述单一模型在这套材料下的输出行为，稳定性与复核均在同一历史数据内进行，不外推为人类心理规律。",
]

RESULT_TAKEAWAYS = [
    "把决策过程讲得更完整（从只报结论到给出理由、反思与修正），模型对决策者的能动性评分总体升高，这是最稳定的差异。",
    "身份标签本身影响明显：在自由意志、责任与体验维度上，模型对人类与 AI 决策者的评分存在系统差异，但在感知智能与操纵检验上差异很弱。",
    "在同时控制感知智能与文本长度后，过程对能动性的效应仍然显著；对自由意志的直接效应则不再显著。",
    "自由意志归因更像经由能动性的关联性间接路径发生，而非过程的直接效应；感知智能的间接路径区间跨 0。",
    "以上都是单一模型在这套材料下的输出行为描述，对应的是模型的归因反应本身。",
]

# Evaluation core: a five-step flow, one executable command block, and a single
# compact artifact table (replacing the former 11-stage pipeline + 11 artifact
# nodes + 7 hash cards).
EVAL_STEPS = [
    {"step": "选择任务和模型配置",
     "note": "确定任务规格（TaskSpec）与模型配置，可用 mock 或真实 provider。"},
    {"step": "执行统一命令",
     "note": "用同一条命令行入口发起一次运行。"},
    {"step": "解析、校验并计分",
     "note": "解析响应、做 schema 与范围校验，聚合为构念分数。"},
    {"step": "将运行产物写入独立目录",
     "note": "每次运行写入独立目录，历史 outputs/ 只读、互不覆盖。"},
    {"step": "查看运行清单和聚合报告",
     "note": "运行清单（RunManifest）记录配置与产物哈希，聚合报告（AggregateReport）汇总执行与输出质量。"},
]

EVAL_COMMANDS = [
    "uv sync --frozen",
    "python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <临时目录>",
    "python -m pytest -q",
]

ARTIFACT_TABLE = [
    {"label": "配置快照", "purpose": "冻结解析后配置、任务规格与模型规格。"},
    {"label": "Prompt 与刺激快照", "purpose": "记录本次运行使用的 Prompt 模板与刺激材料。"},
    {"label": "原始与规范化响应", "purpose": "保存逐条原始响应及其解析后的结构化结果。"},
    {"label": "计分与失败记录", "purpose": "记录构念分数与无法解析或校验失败的条目。"},
    {"label": "聚合报告", "purpose": "汇总完成率、解析成功率与 schema 合规等执行指标。"},
    {"label": "运行清单", "purpose": "串联上述输入与产物的 SHA-256，支持追溯与审计。"},
]

EVAL_HASH_NOTE = (
    "任务规格、模型配置、Prompt、刺激集、计分规格与运行产物各自记录 SHA-256，"
    "运行清单据此把一次运行的输入与产物关联起来，使运行可被逐步骤追溯。")

REPRO_COMMANDS = [
    {"label": "环境安装（锁定依赖）", "cmd": "uv sync --frozen"},
    {"label": "mock 快速运行（写临时目录）",
     "cmd": "python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <临时目录>"},
    {"label": "真实运行离线 dry-run（只规划、不发送、不计费）",
     "cmd": "python -m freewill_attribution.cli run --provider deepseek --dry-run --run-profile smoke"},
    {"label": "测试", "cmd": "python -m pytest -q"},
    {"label": "生成站点数据", "cmd": "python scripts/build_site_data.py && "
     "python scripts/build_public_report.py && python scripts/build_showcase_data.py"},
    {"label": "本地预览", "cmd": "python -m http.server 8000 --directory site"},
]

DOC_ENTRIES = [
    {"label": "研究方法", "path": "docs/research_design_blueprint.md"},
    {"label": "结果报告", "path": "outputs/final_simulated_pilot_report.md"},
    {"label": "证据来源声明", "path": "docs/audit/v1_provenance_statement.md"},
    {"label": "真实运行手册", "path": "docs/runs/REAL_PILOT_RUNBOOK.md"},
    {"label": "真实接入离线准备", "path": "docs/runs/REAL_PROVIDER_READINESS.md"},
]

KEY_DIRECTORIES = [
    {"path": "src/freewill_attribution/", "note": "评测运行器、Provider 接口与计分逻辑"},
    {"path": "configs/", "note": "任务、模型、Prompt 与研究配置契约"},
    {"path": "outputs/", "note": "历史聚合结果、统计产物与图表（只读、不覆盖）"},
    {"path": "site/", "note": "静态展示页与其数据"},
    {"path": "docs/", "note": "研究协议、证据审计与运行手册"},
]

# Real model access: a single statement + a five-step flow. Precise smoke/pilot
# counts stay in the runbook (docs/runs/*), not on the public page.
REAL_PROVIDER_STATEMENT = (
    "真实模型接入流程已经预设。运行时核验模型、价格和凭据后，"
    "可以沿用同一套任务配置、解析、计分和产物规范执行真实运行。")

REAL_PROVIDER_FLOW = [
    "核验运行配置", "小规模连通性检查", "分层试运行", "质量复核", "生成脱敏报告",
]

# From a single attribution task toward a general, comparable evaluation.
BENCHMARK_ROADMAP_FLOW = [
    "任务契约", "数据版本", "多模型运行", "稳健性评测", "人工校准", "基准卡与标准报告",
]


# ---------------------------------------------------------------------------
# Small source readers
# ---------------------------------------------------------------------------

def _reliability_rows() -> list[dict[str, str]]:
    return bsd._read_csv("outputs/reliability_summary.csv")


def _identity_means() -> dict[str, dict[str, float]]:
    """Per-identity mean of each construct, computed from scale_scores.csv."""
    rows = bsd._read_csv("outputs/scale_scores.csv")
    if not rows:
        raise BuildError("scale_scores.csv has no rows")
    buckets: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        ident = row["identity_label"]
        buckets.setdefault(ident, {})
        for dv in IDENTITY_CONSTRUCTS:
            if dv not in row:
                raise BuildError(f"scale_scores.csv missing column '{dv}'")
            buckets[ident].setdefault(dv, []).append(float(row[dv]))
    out: dict[str, dict[str, float]] = {}
    for ident, dvs in buckets.items():
        out[ident] = {dv: statistics.fmean(vals) for dv, vals in dvs.items()}
    return out


# ---------------------------------------------------------------------------
# showcase_story.json
# ---------------------------------------------------------------------------

def _scenario_cards(data_ids: set[str]) -> list[dict]:
    """Scenario case cards, read faithfully from src/stimuli.py (never rewritten).

    The scenario_id set is cross-checked against the historical data so the page
    can never show a case that is not backed by the actual materials.
    """
    stim_ids = {s.scenario_id for s in stimuli.SCENARIOS}
    if stim_ids != data_ids:
        raise BuildError(
            f"scenario id mismatch: stimuli={sorted(stim_ids)} data={sorted(data_ids)}")
    cards = []
    for s in stimuli.SCENARIOS:  # keep the canonical stimuli order
        label = SCENARIO_LABELS.get(s.scenario_id)
        if not label:
            raise BuildError(f"missing SCENARIO_LABELS entry for '{s.scenario_id}'")
        cards.append({
            "id": s.scenario_id,
            "domain": s.domain,
            "label": label,
            "context": s.context,
            "option_a": s.option_a,
            "option_b": s.option_b,
            "fixed_choice": s.fixed_choice,
        })
    return cards


# DOI must look like a real DOI (10.<registrant>/<suffix>); empty is allowed for
# a book-only theoretical source that carries a publisher URL instead.
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")

# Expected research-source ids and their canonical page order. This guards the
# page against silently gaining/losing a source card.
RESEARCH_SOURCE_IDS = [
    "mind_perception",
    "free_will_beliefs",
    "perceived_intelligence",
    "reasons_responsiveness_responsibility",
    "self_authored_checks",
]


def _research_sources() -> dict:
    """Research & measurement sources, read from the human-verified manifest.

    Every card is a contextual adaptation of prior theory/scale constructs, not a
    direct reuse of a complete published scale; the self-authored checks carry no
    external scale. DOIs are format-checked so a malformed reference fails loudly.
    """
    block = bsd._manifest().get("research_sources")
    if not isinstance(block, dict):
        raise BuildError("site_manifest.yaml research_sources block missing")
    for field in ("intro_zh", "usage_note_zh"):
        if not block.get(field):
            raise BuildError(f"research_sources missing '{field}'")
    raw = block.get("sources")
    if not isinstance(raw, list) or not raw:
        raise BuildError("research_sources.sources missing")
    by_id = {}
    for s in raw:
        if not isinstance(s, dict) or not s.get("id"):
            raise BuildError("research_sources entry missing id")
        by_id[s["id"]] = s
    if set(by_id) != set(RESEARCH_SOURCE_IDS):
        raise BuildError(
            f"research_sources id mismatch: manifest={sorted(by_id)} "
            f"expected={sorted(RESEARCH_SOURCE_IDS)}")

    sources = []
    all_refs = []
    for sid in RESEARCH_SOURCE_IDS:  # stable canonical order
        s = by_id[sid]
        for field in ("label_zh", "citation_short", "role_zh", "usage_zh"):
            if not s.get(field):
                raise BuildError(f"research_source '{sid}' missing '{field}'")
        constructs = s.get("constructs_zh")
        if not isinstance(constructs, list) or not constructs:
            raise BuildError(f"research_source '{sid}' missing constructs_zh")
        refs = []
        for ref in (s.get("references") or []):
            full = (ref.get("full") or "").strip()
            if not full:
                raise BuildError(f"research_source '{sid}' reference missing 'full'")
            doi = (ref.get("doi") or "").strip()
            if doi and not _DOI_RE.match(doi):
                raise BuildError(f"research_source '{sid}' has malformed DOI '{doi}'")
            entry = {"full": full, "doi": doi, "url": (ref.get("url") or "").strip()}
            refs.append(entry)
            all_refs.append({"source": sid, **entry})
        # self-authored sources legitimately have no external reference
        if sid != "self_authored_checks" and not refs:
            raise BuildError(f"research_source '{sid}' must carry at least one reference")
        sources.append({
            "id": sid,
            "label": s["label_zh"],
            "citation_short": s["citation_short"],
            "constructs": list(constructs),
            "role": s["role_zh"],
            "usage": s["usage_zh"],
            "references": refs,
        })

    detail_docs = []
    for d in (block.get("detail_docs") or []):
        if not isinstance(d, dict) or not d.get("path") or not d.get("note_zh"):
            raise BuildError("research_sources.detail_docs entry malformed")
        detail_docs.append({"path": d["path"], "note": d["note_zh"]})
    if not detail_docs:
        raise BuildError("research_sources.detail_docs missing")

    return {
        "intro": block["intro_zh"],
        "usage_note": block["usage_note_zh"],
        "sources": sources,
        "references": all_refs,
        "detail_docs": detail_docs,
    }


def build_showcase_story() -> dict:
    rows = bsd._read_csv("outputs/scale_scores.csv")
    records = len(rows)
    scenarios = sorted({r["scenario_id"] for r in rows})
    domains = sorted({r["domain"] for r in rows})

    study = yaml.safe_load(bsd._read_text("configs/study.default.yaml"))
    process_conditions = study["design"]["process_conditions"]
    identity_labels = study["design"]["identity_labels"]

    rel = _reliability_rows()
    total_items = sum(int(r["n_items"]) for r in rel)
    total_constructs = len(rel)

    core_facts = [
        {"key": "process_condition_count", "value": len(process_conditions),
         "label": "过程条件"},
        {"key": "identity_condition_count", "value": len(identity_labels),
         "label": "行动者身份"},
        {"key": "historical_record_count", "value": records, "label": "历史记录"},
        {"key": "scenario_count", "value": len(scenarios), "label": "情境"},
        {"key": "item_count", "value": total_items, "label": "测量题项"},
        {"key": "construct_count", "value": total_constructs, "label": "测量构念"},
        {"key": "mock_reproducible_run", "value": "已实现", "label": "可复现 mock 运行"},
        {"key": "offline_provider_ready", "value": "已完成", "label": "真实接口离线准备"},
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title_zh": "LLM 归因行为评测",
        "subtitle_en": "A Reproducible Study and Evaluation Prototype",
        "positioning_zh": (
            "围绕模型如何对行动者的能动性、自由意志与责任作出归因，"
            "构建从历史研究、任务契约到可复现运行与证据审计的测试型评测基准。"),
        "core_facts": core_facts,
        "scenarios": _scenario_cards(set(scenarios)),
        "domains": domains,
        "research_sources": _research_sources(),
        "result_takeaways": RESULT_TAKEAWAYS,
    }


# ---------------------------------------------------------------------------
# measurement_summary.json
# ---------------------------------------------------------------------------

def build_measurement_summary() -> dict:
    rel = _reliability_rows()
    constructs = []
    total_items = 0
    for row in rel:
        key = row["scale"]
        meta = CONSTRUCT_META.get(key)
        if not meta:
            raise BuildError(f"reliability_summary.csv has unmapped construct '{key}'")
        n_items = int(row["n_items"])
        total_items += n_items
        constructs.append({
            "key": key,
            "label": meta["label"],
            "role": meta["role"],
            "n_items": n_items,
            "n_cases": int(row["n_cases_complete"]),
            "alpha": round(float(row["cronbach_alpha"]), 3),
            "range": meta["range"],
            "note": meta["note"],
        })
    # canonical ordering: manipulation checks, primary, secondary/covariate,
    # responsibility subdims — but keep it data-driven & stable by role then key.
    role_order = {"操纵检验": 0, "主要结果": 1, "次要结果": 2,
                  "心智知觉对照": 3, "协变量": 4, "责任子维度": 5}
    constructs.sort(key=lambda c: (role_order.get(c["role"], 9), c["key"]))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_constructs": len(constructs),
        "total_items": total_items,
        "scoring_note": "每个构念的分数为其题项的均值（事实操纵检验计 0–2，其余题项计 1–7）。",
        "reliability_note": (
            "Cronbach α 为合成（模型模拟）数据上的内部一致性指标，"
            "不等于效度，也不构成人类被试的信效度证据。"),
        "responsibility_total": RESPONSIBILITY_TOTAL_META,
        "constructs": constructs,
    }


# ---------------------------------------------------------------------------
# analysis_results.json
# ---------------------------------------------------------------------------

def _condition_profile() -> dict:
    conditions = bsd.build_site_summary()["design"]["process_conditions"]
    order = [c["key"] for c in conditions]
    labels = {c["key"]: c["label"] for c in conditions}
    series = []
    for dv in PROFILE_CONSTRUCTS:
        values = bsd._report_condition_map(dv)
        points = []
        for cond in order:
            if cond not in values:
                raise BuildError(f"condition profile: {dv} missing '{cond}'")
            points.append({"condition": cond, "label": labels[cond],
                           "value": round(values[cond], 3)})
        series.append({
            "construct": dv, "label": DV_LABELS[dv], "points": points,
        })
    return {"conditions": order, "condition_labels": labels, "series": series,
            "scale_note": "构念分数区间 1–7，各序列使用同一坐标便于比较。"}


def _identity_effect() -> dict:
    rows = bsd._read_csv("outputs/anova_summary.csv")
    means = _identity_means()
    idents = sorted(means.keys())
    effects = []
    seen = set()
    for row in rows:
        dv = row.get("dv")
        if row.get("effect") != "C(identity_label)" or dv not in IDENTITY_CONSTRUCTS:
            continue
        seen.add(dv)
        m = {ident: round(means[ident][dv], 3) for ident in idents}
        higher = max(m, key=m.get)
        effects.append({
            "construct": dv, "label": DV_LABELS[dv],
            "F": round(float(row["F"]), 2),
            "p": float(row["p"]),
            "partial_eta_sq": round(float(row["partial_eta_sq"]), 3),
            "means_by_identity": m,
            "higher_identity": higher,
        })
    missing = set(IDENTITY_CONSTRUCTS) - seen
    if missing:
        raise BuildError(f"anova_summary.csv missing identity effect for {missing}")
    order = {k: i for i, k in enumerate(IDENTITY_CONSTRUCTS)}
    effects.sort(key=lambda e: order[e["construct"]])
    return {
        "identities": idents,
        "estimator": "两因素方差分析（过程 × 身份）的身份主效应",
        "note": "效应量为 partial η²；源文件为 F 检验，未提供均值差的置信区间。",
        "effects": effects,
    }


def _planned_contrasts() -> dict:
    rows = bsd._read_csv("outputs/planned_contrasts.csv")
    groups = {dv: [] for dv in CONTRAST_DVS}
    for row in rows:
        dv = row.get("dv")
        if dv not in groups:
            continue
        contrast = row["contrast"]
        groups[dv].append({
            "contrast": contrast,
            "label": CONTRAST_LABELS.get(contrast, contrast),
            "mean_a": round(float(row["mean_a"]), 3),
            "mean_b": round(float(row["mean_b"]), 3),
            "diff": round(float(row["diff_a_minus_b"]), 3),
            "t": round(float(row["t"]), 3),
            "p": float(row["p"]),
            "direction": "a>b" if float(row["diff_a_minus_b"]) > 0 else "a<b",
        })
    out = []
    for dv in CONTRAST_DVS:
        if not groups[dv]:
            raise BuildError(f"planned_contrasts.csv missing contrasts for dv={dv}")
        out.append({"dv": dv, "label": DV_LABELS[dv], "contrasts": groups[dv]})
    return {
        "note": ("对比为源文件中实际登记的过程条件对比；源文件提供差值、t 与 p，"
                 "未提供置信区间，页面不计算源文件中不存在的区间或显著性。"),
        "groups": out,
    }


def _controlled_regression() -> dict:
    rows = bsd._read_csv("outputs/controlled_regression_summary.csv")
    index = {(r["dv"], r["spec"]): r for r in rows}
    out = []
    for dv in CONTROLLED_DVS:
        specs = []
        for spec in CONTROLLED_SPECS:
            r = index.get((dv, spec))
            if not r:
                raise BuildError(f"controlled_regression_summary.csv missing {dv}/{spec}")
            specs.append({
                "spec": spec,
                "process_F": round(float(r["process_F"]), 3),
                "process_p": float(r["process_p"]),
                "r_squared": round(float(r["r_squared"]), 3),
                "survives": float(r["process_p"]) < 0.05,
            })
        out.append({"dv": dv, "label": DV_LABELS[dv], "specs": specs})
    return {
        "spec_labels": {
            "dummy_process_only": "仅过程（未加控制）",
            "control_both": "同时控制感知智能与文本长度",
        },
        "note": ("展示过程条件的整体效应在加入控制变量前后的变化；"
                 "control_both 同时控制感知智能与文本长度。"),
        "rows": out,
    }


def _mediation() -> dict:
    med = json.loads(bsd._read_text("outputs/parallel_mediation_summary.json"))
    def path(name, label, mid_label, a, b, ind, lo, hi):
        return {
            "name": name, "label": label, "mid": mid_label,
            "a": round(float(med[a]), 4), "b": round(float(med[b]), 4),
            "indirect": round(float(med[ind]), 4),
            "ci_low": round(float(med[lo]), 4),
            "ci_high": round(float(med[hi]), 4),
            "crosses_zero": bool(float(med[lo]) <= 0 <= float(med[hi])),
        }
    return {
        "outcome": "自由意志归因",
        "predictor": "过程结构等级",
        "controls": list(med.get("controls", [])),
        "direct_c_prime": round(float(med["direct_c_prime"]), 4),
        "paths": [
            path("agency", "关联性主路径", "能动性",
                 "a_agency", "b_agency", "indirect_agency",
                 "agency_indirect_ci_2.5", "agency_indirect_ci_97.5"),
            path("perceived_intelligence", "关联性次路径", "感知智能",
                 "a_intelligence", "b_intelligence", "indirect_intelligence",
                 "intelligence_indirect_ci_2.5", "intelligence_indirect_ci_97.5"),
        ],
        "note": ("关联性间接路径诊断，非因果中介证明、非机制验证；"
                 "仅当自助区间不跨 0 时说该探索性估计方向一致。"),
    }


def build_analysis_results() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "condition_profile": _condition_profile(),
        "identity_effect": _identity_effect(),
        "planned_contrasts": _planned_contrasts(),
        "controlled_regression": _controlled_regression(),
        "mediation": _mediation(),
        "stability": {"points": STABILITY_POINTS},
    }


# ---------------------------------------------------------------------------
# reproducibility_summary.json
# ---------------------------------------------------------------------------

def build_reproducibility_summary() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "eval_steps": EVAL_STEPS,
        "eval_commands": EVAL_COMMANDS,
        "artifact_table": ARTIFACT_TABLE,
        "hash_note": EVAL_HASH_NOTE,
        "repro_commands": REPRO_COMMANDS,
        "doc_entries": DOC_ENTRIES,
        "key_directories": KEY_DIRECTORIES,
        "real_provider": {
            "statement": REAL_PROVIDER_STATEMENT,
            "flow": REAL_PROVIDER_FLOW,
            "runbook": "docs/runs/REAL_PILOT_RUNBOOK.md",
        },
        "benchmark_roadmap": {"flow": BENCHMARK_ROADMAP_FLOW},
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_all() -> dict[str, dict]:
    return {
        "showcase_story.json": build_showcase_story(),
        "measurement_summary.json": build_measurement_summary(),
        "analysis_results.json": build_analysis_results(),
        "reproducibility_summary.json": build_reproducibility_summary(),
    }


def _dumps(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _comparable(obj: dict) -> dict:
    obj = dict(obj)
    obj.pop("generated_at", None)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build showcase narrative JSON data.")
    parser.add_argument("--out", default="site/data")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        built = build_all()
    except BuildError as exc:
        print(f"build_showcase_data: ERROR: {exc}", file=sys.stderr)
        return 2

    out_dir = (ROOT / args.out).resolve()

    if args.check:
        mismatched = []
        for name, obj in built.items():
            existing_path = out_dir / name
            if not existing_path.is_file():
                mismatched.append(f"{name} (missing)")
                continue
            try:
                existing = json.loads(existing_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                mismatched.append(f"{name} (invalid JSON)")
                continue
            if _comparable(existing) != _comparable(obj):
                mismatched.append(name)
        if mismatched:
            print("showcase data is OUT OF DATE: " + ", ".join(mismatched), file=sys.stderr)
            return 1
        print("showcase data is up to date")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in built.items():
        (out_dir / name).write_text(_dumps(obj), encoding="utf-8")
        print(f"wrote {args.out}/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
