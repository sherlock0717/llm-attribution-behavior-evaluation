"""Static checks for the public showcase page (SHOWCASE-RELEASE-001).

No network calls; only reads files under site/. These enforce the frozen public
naming, the continuous section structure, and the public-content rules
(no internal task codes, no target-audience wording, no old repo name, no
hardcoded statistics, four-state provenance).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE = REPO_ROOT / "site"
INDEX = SITE / "index.html"
CSS = SITE / "assets" / "css" / "site.css"
JS = SITE / "assets" / "js" / "site.js"
DATA = SITE / "data"
FIGURES = SITE / "assets" / "figures"

HTML = INDEX.read_text(encoding="utf-8")
JS_SRC = JS.read_text(encoding="utf-8")
CSS_SRC = CSS.read_text(encoding="utf-8")

JSON_FILES = [
    "site_summary.json",
    "showcase_story.json",
    "measurement_summary.json",
    "analysis_results.json",
    "historical_results.json",
    "engineering_status.json",
    "evidence_matrix.json",
    "reproducibility_summary.json",
]

SECTION_IDS = [
    "overview", "research-question", "design-measurement", "research-sources",
    "historical-data", "analysis", "results-summary", "evaluation-core",
    "mock-validation", "real-provider", "reproducibility", "future-work",
]

SELECTED_FIGURES = [
    "mean_agency.png",
    "mean_free_will_attribution.png",
    "mean_subjective_process_completeness.png",
]

MAIN_TITLE = "LLM 归因行为评测"
SUBTITLE = "A Reproducible Study and Evaluation Prototype"
NEW_SLUG = "llm-attribution-behavior-evaluation"
OLD_SLUG = "llm-agent-free-will-attribution"


# --- files / structure -----------------------------------------------------

def test_core_files_exist():
    assert INDEX.is_file() and CSS.is_file() and JS.is_file()
    assert (SITE / "README.md").is_file()
    for name in JSON_FILES:
        assert (DATA / name).is_file(), name
    for fig in SELECTED_FIGURES:
        assert (FIGURES / fig).is_file(), fig


def test_json_files_are_valid():
    for name in JSON_FILES:
        json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", JSON_FILES)
def test_json_utf8_no_bom(name):
    assert not (DATA / name).read_bytes().startswith(b"\xef\xbb\xbf"), name


def test_index_contains_all_sections():
    for sid in SECTION_IDS:
        assert f'id="{sid}"' in HTML, sid


# --- (14) frozen public naming ---------------------------------------------

def test_main_title_exact():
    assert re.search(r"<h1>\s*LLM 归因行为评测\s*</h1>", HTML)


def test_subtitle_exact():
    assert '<p class="subtitle">A Reproducible Study and Evaluation Prototype</p>' in HTML


def test_html_title_correct():
    assert "<title>LLM 归因行为评测｜A Reproducible Study and Evaluation Prototype</title>" in HTML


def test_positioning_uses_test_evaluation_benchmark():
    assert "测试型评测基准" in HTML


# --- (14) no version numbers / old names -----------------------------------

def test_no_public_version_numbers():
    for bad in ["v0.3", "v1.0", "Version History", "版本路线图", "0.2.0.dev0"]:
        assert bad not in HTML, bad


def test_no_old_public_titles():
    for bad in ["大语言模型自由意志归因研究原型",
                "大语言模型 Agent 决策结构",
                "LLM Free-Will Attribution"]:
        assert bad not in HTML, bad


def test_no_old_repo_slug_anywhere():
    assert OLD_SLUG not in HTML


def test_github_links_use_new_slug():
    hrefs = re.findall(r'href="(https://github\.com/[^"]+)"', HTML)
    assert hrefs, "expected at least one GitHub link"
    for h in hrefs:
        assert NEW_SLUG in h, h
        assert OLD_SLUG not in h, h


# --- (14) no internal dev language / task codes ----------------------------

def test_no_internal_task_codes_in_html():
    for bad in ["Phase ", "Phase1", "Track S", "FND-", "SITE-", "RES-",
                "RUN-", "BMK-", "FAST-", "RBC-", "backlog"]:
        assert bad not in HTML, bad


def test_no_target_audience_wording():
    for bad in ["求职", "招聘者", "作品集", "面向 AI 数据评测岗位",
                "面向后训练岗位", "为了投递", "方便面试"]:
        assert bad not in HTML, bad


def test_no_forbidden_english_headings():
    for bad in ["Historical Baseline", "Mock Validation", "Provider Readiness",
                "Evidence Matrix", "Roadmap", "Pipeline", "Benchmark Status",
                "Engineering Core"]:
        assert bad not in HTML, bad


# --- (14) no hardcoded statistics ------------------------------------------

def test_no_hardcoded_statistics_in_html():
    for bad in ["360", "12.19", "0.2699", "4.308", "5.200", "34 个题项",
                "F = ", "p < ."]:
        assert bad not in HTML, bad


# --- (14) markup hygiene ---------------------------------------------------

def test_no_inline_event_handlers():
    assert re.search(r"\son[a-z]+\s*=", HTML) is None


def test_no_cdn_or_remote_assets_in_head_tags():
    # Scripts must be local; only meta rel=canonical/og may be absolute URLs.
    for m in re.finditer(r'<script[^>]*\ssrc="([^"]+)"', HTML):
        assert not m.group(1).startswith(("http://", "https://", "//")), m.group(1)
    for m in re.finditer(r'<link[^>]*\srel="stylesheet"[^>]*\shref="([^"]+)"', HTML):
        assert not m.group(1).startswith(("http://", "https://", "//")), m.group(1)


def test_js_has_no_third_party_imports():
    # No remote assets or ES-module URL imports. The SVG namespace URI is not a
    # network dependency and is allowed.
    assert "https://" not in JS_SRC
    assert 'fetch("http' not in JS_SRC
    assert "://cdn" not in JS_SRC.lower()
    assert re.search(r'\bfrom\s+["\']https?://', JS_SRC) is None
    assert re.search(r'\bimport\s+.*\bfrom\b', JS_SRC) is None


# --- (14) anchors, local resources -----------------------------------------

def test_all_local_hrefs_resolve():
    ids = set(re.findall(r'id="([^"]+)"', HTML))
    for href in re.findall(r'href="([^"]+)"', HTML):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if href.startswith("#"):
            assert href[1:] in ids, "missing anchor target: " + href
        else:
            assert (SITE / href).exists(), "broken local href: " + href


def test_nav_anchors_are_valid_sections():
    nav = HTML.split('id="site-nav-list"', 1)[1].split("</nav>", 1)[0]
    for href in re.findall(r'href="#([^"]+)"', nav):
        assert f'id="{href}"' in HTML, href


# --- (14) chart slots / JS wiring ------------------------------------------

def test_every_javascript_slot_exists_in_html():
    defined = set(re.findall(r'data-slot="([^"]+)"', HTML))
    used = set(re.findall(r'(?:slotEl|requireSlot|setSlot)\("([^"]+)"', JS_SRC))
    missing = used - defined
    assert not missing, "JS references missing slots: " + ", ".join(sorted(missing))


def test_core_chart_slots_present():
    for name in ["hero-corefacts", "process-cards", "design-matrix",
                 "scenario-cards", "research-source-cards", "research-references",
                 "condition-profile", "identity-effect",
                 "planned-contrasts", "controlled-regression", "mediation-path",
                 "figures", "mock-quality", "eval-steps", "artifact-table",
                 "readiness-flow", "benchmark-flow"]:
        assert f'data-slot="{name}"' in HTML, name


def test_render_pipeline_and_diagnostics_present():
    for call in ["renderConditionProfile(", "renderFigures(", "renderMediation(",
                 "renderReadiness(", "renderMockQuality(", "renderProcessConditions(",
                 "renderScenarios(", "renderResearchSources(", "renderEvalSteps(",
                 "renderBenchmarkRoadmap("]:
        assert call in JS_SRC, call
    assert 'renderComplete = "true"' in JS_SRC
    assert 'renderComplete = "false"' in JS_SRC
    assert "writeLayoutDiagnostics" in JS_SRC
    assert "diagnostics=1" in JS_SRC


# --- (14) provider readiness only in one section ---------------------------

def test_provider_readiness_single_section():
    assert HTML.count('id="real-provider"') == 1
    # the offline-validated statement is rendered from JSON, once, into one slot
    assert HTML.count('data-slot="readiness-statement"') == 1
    assert HTML.count('data-slot="readiness-flow"') == 1


def test_no_fabricated_real_metrics_in_html():
    for bad in ["0 ms", "$0", "0 token", "0.0 美元", "0ms"]:
        assert bad not in HTML, bad


# --- (11 / 14) real readiness metrics stay null in data --------------------

def test_real_provider_actual_metrics_are_null():
    eng = json.loads((DATA / "engineering_status.json").read_text(encoding="utf-8"))
    rr = eng["real_provider_readiness"]
    for key in ["actual_token_usage", "actual_cost_usd", "actual_latency_ms",
                "actual_completion_rate", "actual_parse_success_rate"]:
        assert rr[key] is None, key
    assert rr["smoke_status"] == "not_run"
    assert rr["pilot_status"] == "not_run"
    assert rr["network_calls_made"] == 0


# --- (20) provenance four-state consistency --------------------------------

def test_provenance_four_states_consistent():
    ev = json.loads((DATA / "evidence_matrix.json").read_text(encoding="utf-8"))
    pc = ev["provenance_completeness"]
    dims = pc["dimensions"]
    states = {d["verification_status"] for d in dims}
    assert states == {"repository_verified", "author_attested", "reconstructed", "unknown"}
    total = (pc["repository_verified_count"] + pc["author_attested_count"]
             + pc["reconstructed_count"] + pc["unknown_count"])
    assert total == pc["total_count"] == len(dims)
    # every dimension carries a Chinese display label + group for the matrix
    for d in dims:
        assert d.get("label")
        assert d.get("group")


# --- figures integrity ------------------------------------------------------

def test_figures_match_source_hashes():
    for fig in SELECTED_FIGURES:
        site_fig = FIGURES / fig
        source_fig = REPO_ROOT / "outputs" / "plots" / fig
        assert (hashlib.sha256(site_fig.read_bytes()).hexdigest()
                == hashlib.sha256(source_fig.read_bytes()).hexdigest()), fig


def test_historical_results_json_shape():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    assert hr["claims"]
    assert len(hr["figures"]) == 3
    for fig in hr["figures"]:
        assert len(fig["sha256"]) == 64
        assert fig.get("read_note")


# --- mediation structured fields (unchanged research contract) -------------

def test_mediation_metrics_structured():
    an = json.loads((DATA / "analysis_results.json").read_text(encoding="utf-8"))
    paths = an["mediation"]["paths"]
    agency = next(p for p in paths if p["name"] == "agency")
    intel = next(p for p in paths if p["name"] == "perceived_intelligence")
    assert agency["crosses_zero"] is False
    assert intel["crosses_zero"] is True


# --- responsive hygiene -----------------------------------------------------

def test_css_responsive_hygiene():
    assert "minmax(0, 1fr)" in CSS_SRC
    assert "min-width: 0" in CSS_SRC
    assert "overflow-wrap: anywhere" in CSS_SRC
    assert "overflow-x: hidden" not in CSS_SRC
    assert "@media (max-width: 390px)" in CSS_SRC


# --- concept visual (kept from prior redesign) -----------------------------

CONCEPT_IMG = FIGURES / "attribution-research-concept.png"
INVENTORY = REPO_ROOT / "docs" / "showcase" / "PUBLIC_ASSET_INVENTORY.md"
CONCEPT_SHA = "FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7"


def test_research_concept_image_is_valid_and_referenced():
    data = CONCEPT_IMG.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert 'width="{}"'.format(width) in HTML
    assert 'height="{}"'.format(height) in HTML
    digest = hashlib.sha256(data).hexdigest().upper()
    assert digest == CONCEPT_SHA
    assert CONCEPT_SHA in INVENTORY.read_text(encoding="utf-8")


def test_research_concept_in_research_question_with_caption():
    rq = HTML.split('id="research-question"', 1)[1].split("</section>", 1)[0]
    assert "attribution-research-concept.png" in rq
    assert "不承载统计结果" in rq


# --- SHOWCASE-FIX-001: copy / layout cleanup -------------------------------

def _load_stimuli():
    spec = importlib.util.spec_from_file_location(
        "stimuli", REPO_ROOT / "src" / "stimuli.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_read_image_prefix():
    # (2) the "读图：" prefix must not appear in the page or its script
    assert "读图：" not in HTML
    assert "读图：" not in JS_SRC


def test_no_forbidden_word_list():
    # (2) no self-checking forbidden-word list, and no forbidden claims
    for bad in ["「证明了」", "揭示了真实心理机制", "模型具备自由意志",
                "与人类完全一致", "不使用「证明了」"]:
        assert bad not in HTML, bad


def test_no_evidence_boundary_section():
    # (3, 4) the evidence-boundary section and its nav entry are removed
    assert 'id="evidence-boundary"' not in HTML
    assert "证据与来源边界" not in HTML
    nav = HTML.split('id="site-nav-list"', 1)[1].split("</nav>", 1)[0]
    assert "证据边界" not in nav
    assert "renderProvenance" not in JS_SRC
    assert "provenance-matrix" not in HTML


def test_no_public_pilot_counts_or_status_table():
    # (5, 6) no public 12/60 plan, no not_run/null status table
    for bad in ["12 / 60", "12 条真实 smoke", "60 条真实 pilot",
                "12 条 smoke", "60 条 pilot", "not_run", "readiness-status",
                "readiness-checklist", "readiness-plan"]:
        assert bad not in HTML, bad


def test_no_old_footer_text():
    # (7) footer simplified to title + GitHub link only
    for bad in ["研究数据源提交", "历史 DeepSeek API 模型输出", "测试型评测基准原型",
                'data-slot="source-commit"', 'data-slot="data-as-of"',
                'data-slot="generated-at"']:
        assert bad not in HTML, bad


def test_no_diagnostic_or_grad_markup():
    # (9) no diagnostic class / grad-tag / length-control special marking.
    # (Note: the legitimate "diagnostics" layout feature is unrelated and kept.)
    for token in ["grad-tag", "grad-node", "LENGTH_CONTROL_KEY"]:
        assert token not in JS_SRC, token
    for token in ["grad-tag", "grad-node", ".diagnostic"]:
        assert token not in CSS_SRC, token


def test_process_condition_cards_uniform():
    # (8) six process conditions render as uniform cards
    assert 'data-slot="process-cards"' in HTML
    assert "renderProcessConditions(" in JS_SRC
    assert ".pc-card" in CSS_SRC


def test_matrix_corner_has_visible_text_color():
    # (12) the design matrix corner cell must set an explicit visible colour
    corner = re.search(r"\.design-matrix \.corner \{[^}]*\}", CSS_SRC)
    assert corner, "missing .design-matrix .corner rule"
    assert "color: var(--text)" in corner.group(0)


def test_general_benchmark_flow_present():
    # (13) the general-evaluation roadmap flow exists
    assert 'data-slot="benchmark-flow"' in HTML
    assert "renderBenchmarkRoadmap(" in JS_SRC
    assert "从单一任务到通用评测" in HTML


def test_scenarios_have_case_content_matching_stimuli():
    # (10, 11) eight scenario cards carry context/options/choice, faithful to stimuli
    story = json.loads((DATA / "showcase_story.json").read_text(encoding="utf-8"))
    cards = {c["id"]: c for c in story["scenarios"]}
    assert len(cards) == 8
    stim = _load_stimuli()
    for s in stim.SCENARIOS:
        c = cards[s.scenario_id]
        for field in ("context", "option_a", "option_b", "fixed_choice"):
            assert c.get(field), (s.scenario_id, field)
        assert c["context"] == s.context
        assert c["option_a"] == s.option_a
        assert c["option_b"] == s.option_b
        assert c["fixed_choice"] == s.fixed_choice
        assert c["domain"] == s.domain


# --- SHOWCASE-FIX-002: research & measurement sources ----------------------

README = REPO_ROOT / "README.md"
README_SRC = README.read_text(encoding="utf-8")
STORY = json.loads((DATA / "showcase_story.json").read_text(encoding="utf-8"))
RESEARCH_SOURCES = STORY["research_sources"]
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")

EXPECTED_SOURCE_IDS = [
    "mind_perception", "free_will_beliefs", "perceived_intelligence",
    "reasons_responsiveness_responsibility", "self_authored_checks",
]


def test_page_has_research_sources_section():
    # (4) the page carries a "研究与测量来源" section, placed after 实验设计
    assert 'id="research-sources"' in HTML
    assert "研究与测量来源" in HTML
    dm = HTML.index('id="design-measurement"')
    rs = HTML.index('id="research-sources"')
    hd = HTML.index('id="historical-data"')
    assert dm < rs < hd


def test_page_has_no_evidence_boundary_section_still():
    # (5) the removed evidence-boundary section must not come back
    assert 'id="evidence-boundary"' not in HTML
    assert "证据与来源边界" not in HTML


def test_readme_has_research_sources_section():
    # (3) README carries the source section between 实验设计 and 历史数据
    assert "## 研究与测量来源" in README_SRC
    assert README_SRC.index("## 实验设计") < README_SRC.index("## 研究与测量来源")
    assert README_SRC.index("## 研究与测量来源") < README_SRC.index("## 历史数据与主要结果")


def test_readme_has_only_approved_edits():
    # (2) approved copy changes are present; disallowed/old wording is gone
    assert "会如何改变模型对行动者能动性、自由意志与责任的归因评分" in README_SRC
    assert "## 模拟运行验证" in README_SRC
    assert "## 从单一任务到通用评测" in README_SRC
    assert "暂不作因果机制解释" in README_SRC
    for bad in ["数据边界：", "## Mock 工程验证", "## 多模型测评计划",
                "随时可复现", "而非因果中介证明", "每格 2 条", "每格 1 条",
                "smoke 为每格"]:
        assert bad not in README_SRC, bad


def test_readme_preserves_manual_main_content():
    # (1) unapproved parts of the manual main README are preserved verbatim
    for keep in [
        "A Reproducible Study and Evaluation Prototype",
        "可复现的测试型评测基准原型",
        "它评价的是**模型输出中的归因行为**",
        "自由意志的评分是直接受过程影响，还是先经过能动性这一中间步骤",
        "材料（参考心理学领域相关前沿研究设计）覆盖 8 个情境",
        "链路：情境 → 过程条件 → 身份标签 → 题项响应 → 构念分数 → 条件与身份比较",
    ]:
        assert keep in README_SRC, keep


def test_readme_and_page_share_title_and_terms():
    # (22) README and page share the frozen title and terminology
    assert MAIN_TITLE in README_SRC and MAIN_TITLE in HTML
    assert SUBTITLE in README_SRC and SUBTITLE in HTML
    assert "研究与测量来源" in README_SRC and "研究与测量来源" in HTML


def test_source_cards_count_and_order_stable():
    # (6) exactly the five sources, in canonical order
    ids = [s["id"] for s in RESEARCH_SOURCES["sources"]]
    assert ids == EXPECTED_SOURCE_IDS


def test_every_source_card_has_constructs_and_usage():
    # (7) each source carries constructs + a usage description + role
    for s in RESEARCH_SOURCES["sources"]:
        assert s["constructs"], s["id"]
        assert s["role"], s["id"]
        assert s["usage"], s["id"]


def test_all_dois_are_well_formed():
    # (8) every DOI present must be a well-formed DOI
    seen = 0
    for ref in RESEARCH_SOURCES["references"]:
        if ref["doi"]:
            assert DOI_RE.match(ref["doi"]), ref["doi"]
            seen += 1
    assert seen >= 4  # four journal references carry DOIs


def test_full_references_present():
    # (9) the full reference list is non-empty and every entry has full text
    assert RESEARCH_SOURCES["references"]
    for ref in RESEARCH_SOURCES["references"]:
        assert ref["full"].strip()


def _source(sid):
    return next(s for s in RESEARCH_SOURCES["sources"] if s["id"] == sid)


def test_gray_maps_to_agency_and_experience():
    # (10) mind perception source covers agency + experience
    s = _source("mind_perception")
    assert "Gray" in s["citation_short"]
    assert "能动性" in s["constructs"] and "体验性" in s["constructs"]


def test_free_will_source_maps_to_fwi_and_fadplus():
    # (11) free-will attribution source cites FWI and FAD-Plus
    s = _source("free_will_beliefs")
    assert "FWI" in s["citation_short"] and "FAD-Plus" in s["citation_short"]
    assert "自由意志" in s["constructs"]
    dois = {r["doi"] for r in s["references"]}
    assert "10.1016/j.concog.2014.01.006" in dois
    assert "10.1080/00223891.2010.528483" in dois


def test_godspeed_maps_to_perceived_intelligence():
    # (12) perceived intelligence source is Godspeed
    s = _source("perceived_intelligence")
    assert "Godspeed" in s["citation_short"]
    assert s["references"][0]["doi"] == "10.1007/s12369-008-0001-3"


def test_fischer_ravizza_is_theory_background():
    # (13) reasons-responsiveness / responsibility source is theory, not a scale
    s = _source("reasons_responsiveness_responsibility")
    assert "Fischer" in s["citation_short"]
    assert "责任" in "".join(s["constructs"])
    assert "不是直接采用的心理量表" in s["role"]


def test_self_authored_checks_have_no_external_scale():
    # (14) self-authored manipulation checks carry no external reference
    s = _source("self_authored_checks")
    assert s["references"] == []
    assert "自编" in s["citation_short"] or "自编" in s["role"]


def test_autonomy_not_claimed_as_a_complete_scale():
    # (15) autonomy is never claimed to come directly from a complete scale
    doc = (REPO_ROOT / "docs" / "research_and_measurement_sources.md").read_text(encoding="utf-8")
    assert "自主性与行动控制相关理论背景" in doc
    for bad in ["Self-Determination Theory 量表", "直接采用自主性量表",
                "autonomy 量表原题"]:
        assert bad not in doc, bad


def test_page_does_not_claim_complete_scale_use_or_inherited_validity():
    # (16, 17) page never claims direct use of a complete scale or inherited validity
    blob = HTML + json.dumps(RESEARCH_SOURCES, ensure_ascii=False)
    # positive over-claims must never appear; the legitimate negation
    # "并非对原量表的完整直接使用" is expected and must NOT be flagged.
    for bad in ["直接使用完整量表", "直接使用成熟量表", "沿用原量表信效度",
                "继承原量表信效度"]:
        assert bad not in blob, bad


def test_item_ids_and_texts_unchanged():
    # (18) src/scales.py item ids and texts are untouched by this task
    stim_scales = _load_scales()
    ids = [it.item_id for it in stim_scales.ITEMS]
    assert len(ids) == 34
    assert len(set(ids)) == 34
    # a couple of anchor texts must remain verbatim
    texts = {it.item_id: it.text for it in stim_scales.ITEMS}
    assert texts["agency_self_control"] == "该决策者能够控制自己的行动，而不是只被情境推着走。"
    assert texts["subjective_not_sparse"] == "我认为材料中的决策过程不是只有一个稀疏结论。"


def _load_scales():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scales", REPO_ROOT / "src" / "scales.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_public_future_pilot_numbers_on_page_or_readme():
    # (21) no concrete future smoke/pilot counts leak into page or README
    for bad in ["12 条真实 smoke", "60 条真实 pilot", "12 / 60",
                "每格 2 条", "每格 1 条"]:
        assert bad not in HTML, bad
        assert bad not in README_SRC, bad
