"""Static checks for the showcase page (SITE-003 / SITE-004).

No network calls; only reads files under site/.
"""

from __future__ import annotations

import hashlib
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

JSON_FILES = [
    "site_summary.json",
    "roadmap.json",
    "version_history.json",
    "historical_results.json",
]

SECTION_IDS = [
    "hero", "research-question", "experimental-design", "pipeline",
    "historical-results", "evidence-limitations", "reproducibility",
    "version-history", "roadmap", "repository-links",
]

SELECTED_FIGURES = [
    "mean_agency.png",
    "mean_free_will_attribution.png",
    "mean_subjective_process_completeness.png",
]


def test_core_files_exist():
    assert INDEX.is_file()
    assert CSS.is_file()
    assert JS.is_file()
    assert (SITE / "README.md").is_file()
    for name in JSON_FILES:
        assert (DATA / name).is_file(), name
    for fig in SELECTED_FIGURES:
        assert (FIGURES / fig).is_file(), fig


def test_json_files_are_valid():
    for name in JSON_FILES:
        json.loads((DATA / name).read_text(encoding="utf-8"))


def test_index_contains_all_sections():
    html = INDEX.read_text(encoding="utf-8")
    for sid in SECTION_IDS:
        assert f'id="{sid}"' in html, sid


def test_no_inline_event_handlers():
    html = INDEX.read_text(encoding="utf-8")
    assert re.search(r"\son[a-z]+\s*=", html) is None


def test_no_cdn_or_remote_assets_in_head_tags():
    html = INDEX.read_text(encoding="utf-8")
    # <script src="..."> and <link href="..."> must be local (no http/https).
    for m in re.finditer(r"<script[^>]*\ssrc=\"([^\"]+)\"", html):
        assert not m.group(1).startswith(("http://", "https://", "//")), m.group(1)
    for m in re.finditer(r"<link[^>]*\shref=\"([^\"]+)\"", html):
        assert not m.group(1).startswith(("http://", "https://", "//")), m.group(1)


def test_js_has_no_third_party_imports():
    js = JS.read_text(encoding="utf-8")
    # No remote assets or ES module imports from URLs (comments mentioning
    # "CDN" as prose are fine; we check for actual remote references).
    assert "https://" not in js
    assert "http://" not in js
    assert "://cdn" not in js.lower()
    assert re.search(r'\bfrom\s+["\']https?://', js) is None
    assert re.search(r'\bimport\s+.*\bfrom\b', js) is None


def test_no_hardcoded_statistics_in_html():
    html = INDEX.read_text(encoding="utf-8")
    # Statistical values must come from JSON, not be hardcoded in markup.
    for forbidden in ["360", "12.19", "0.2699", "4.308", "5.200", "F = ", "p < ."]:
        assert forbidden not in html, forbidden


def test_figures_match_source_hashes():
    for fig in SELECTED_FIGURES:
        site_fig = FIGURES / fig
        source_fig = REPO_ROOT / "outputs" / "plots" / fig
        assert (
            hashlib.sha256(site_fig.read_bytes()).hexdigest()
            == hashlib.sha256(source_fig.read_bytes()).hexdigest()
        ), fig


def test_historical_results_json_shape():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    assert hr["claims"]
    assert len(hr["figures"]) == 3
    for fig in hr["figures"]:
        assert len(fig["sha256"]) == 64


def test_site_summary_release_status_not_passing():
    s = json.loads((DATA / "site_summary.json").read_text(encoding="utf-8"))
    assert s["release_verification_status"] == "pending_verification"
    # never advertise CI as passing
    blob = json.dumps(s, ensure_ascii=False).lower()
    assert "passing" not in blob


@pytest.mark.parametrize("name", JSON_FILES)
def test_json_utf8_no_bom(name):
    raw = (DATA / name).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), name


# --- SITE-005.1 additions --------------------------------------------------

def test_no_visual_asset_pending_placeholder():
    html = INDEX.read_text(encoding="utf-8")
    assert "Visual asset pending" not in html
    assert 'data-visual-id="VIS-002"' not in html
    assert 'data-visual-id="VIS-003"' not in html


def test_no_parent_relative_links():
    html = INDEX.read_text(encoding="utf-8")
    assert 'href="../' not in html
    assert 'href="/docs/' not in html
    assert 'href="/outputs/' not in html


def test_all_local_hrefs_resolve():
    html = INDEX.read_text(encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', html))
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if href.startswith("#"):
            assert href[1:] in ids, "missing anchor target: " + href
        else:
            assert (SITE / href).exists(), "broken local href: " + href


def test_repository_links_have_no_parent_paths():
    html = INDEX.read_text(encoding="utf-8")
    section = html.split('id="repository-links"', 1)[1]
    assert "../" not in section.split("</section>", 1)[0]


def test_pipeline_does_not_mark_package_as_historical():
    html = INDEX.read_text(encoding="utf-8")
    historical_nodes = re.findall(
        r'<li class="flow-node" data-kind="historical">.*?</li>', html, re.S
    )
    for node in historical_nodes:
        assert "src/freewill_attribution" not in node


def test_no_windows_linux_local_claim():
    html = INDEX.read_text(encoding="utf-8")
    assert "Windows/Linux 本地跑通" not in html


def test_process_gradient_and_diagnostic_present():
    html = INDEX.read_text(encoding="utf-8")
    assert 'data-slot="process-gradient"' in html
    assert 'data-slot="path-diagram"' in html


def test_js_has_no_figure_reads_constant():
    js = JS.read_text(encoding="utf-8")
    assert "FIGURE_READS" not in js
    assert "read_note" in js


def test_mediation_metrics_have_structured_fields():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    med = next(c for c in hr["claims"] if c["id"] == "parallel-mediation")
    assert med["metrics"], "mediation metrics missing"
    for m in med["metrics"]:
        for field in ("estimate", "ci_low", "ci_high", "path_role"):
            assert field in m, field


def test_agency_ci_excludes_zero_intelligence_ci_crosses_zero():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    med = next(c for c in hr["claims"] if c["id"] == "parallel-mediation")
    agency = next(m for m in med["metrics"] if m["name"] == "agency_indirect")
    intel = next(m for m in med["metrics"] if m["name"] == "perceived_intelligence_indirect")
    assert not (agency["ci_low"] <= 0 <= agency["ci_high"])  # excludes zero
    assert agency["crosses_zero"] is False
    assert intel["ci_low"] <= 0 <= intel["ci_high"]  # crosses zero
    assert intel["crosses_zero"] is True


def test_figures_have_read_note():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    for fig in hr["figures"]:
        assert fig.get("read_note")


def test_factual_check_wording_not_overclaimed():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    fc = next(c for c in hr["claims"] if c["id"] == "factual-check")
    blob = fc["title"] + fc["summary"]
    # Must not positively claim strict monotonicity / pairwise separation.
    assert "随决策过程结构递增" not in blob
    assert "六类材料可被模型区分" not in blob
    # Must state the hedged, integrated-difference framing.
    assert "整体" in blob
    assert ("不构成严格单调" in blob) or ("不宜说" in blob)


# --- SITE-005.2 additions --------------------------------------------------

CONCEPT_IMG = SITE / "assets" / "figures" / "attribution-research-concept.png"
ROOT_STAGING_IMG = REPO_ROOT / "fcdb0f90-6a14-4e45-9412-9b6325cf17a3.png"
INVENTORY = REPO_ROOT / "docs" / "showcase" / "PUBLIC_ASSET_INVENTORY.md"
CONCEPT_SHA = "FFCC3139FD2FBE71CC9049F06CF718BBBFBB6C56E2BF37210C8268FF702BC7F7"


def test_every_javascript_slot_exists_in_html():
    html = INDEX.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    defined = set(re.findall(r'data-slot="([^"]+)"', html))
    used = set(re.findall(r'(?:slotEl|requireSlot)\("([^"]+)"\)', js))
    missing = used - defined
    assert not missing, "JavaScript references missing slots: " + ", ".join(sorted(missing))


def test_figures_render_slot_exists():
    html = INDEX.read_text(encoding="utf-8")
    assert 'data-slot="figures"' in html


def test_require_slot_used_for_core_containers():
    js = JS.read_text(encoding="utf-8")
    for name in ["hero-metrics", "design-matrix", "results", "figures",
                 "path-diagram", "version-timeline"]:
        assert 'requireSlot("' + name + '")' in js, name


def test_render_pipeline_intact_and_diagnostics_present():
    js = JS.read_text(encoding="utf-8")
    for call in ["renderFigures(", "renderPathDiagram(", "renderVersions(",
                 "renderRoadmapGroup("]:
        assert call in js, call
    assert 'renderComplete = "true"' in js
    assert 'renderComplete = "false"' in js
    assert "writeLayoutDiagnostics" in js
    assert "diagnostics=1" in js


def test_research_concept_image_exists():
    assert CONCEPT_IMG.is_file()


def test_research_concept_image_is_valid_png():
    data = CONCEPT_IMG.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    html = INDEX.read_text(encoding="utf-8")
    assert 'width="{}"'.format(width) in html
    assert 'height="{}"'.format(height) in html


def test_research_concept_image_matches_inventory_hash():
    digest = hashlib.sha256(CONCEPT_IMG.read_bytes()).hexdigest().upper()
    assert digest == CONCEPT_SHA
    assert CONCEPT_SHA in INVENTORY.read_text(encoding="utf-8")


def test_research_concept_figure_has_alt():
    html = INDEX.read_text(encoding="utf-8")
    m = re.search(r'attribution-research-concept\.png"\s*\n?\s*alt="([^"]+)"', html)
    assert m is None or m.group(1).strip()
    # robust check: the concept img has a non-empty alt somewhere
    block = html.split("research-concept-figure", 1)[1]
    alt = re.search(r'alt="([^"]+)"', block)
    assert alt and alt.group(1).strip()


def test_research_concept_figure_has_caption():
    html = INDEX.read_text(encoding="utf-8")
    block = html.split("research-concept-figure", 1)[1].split("</figure>", 1)[0]
    assert "<figcaption>" in block
    assert "不承载统计结果" in block


def test_research_concept_visual_is_not_in_historical_figures():
    hr = json.loads((DATA / "historical_results.json").read_text(encoding="utf-8"))
    assert len(hr["figures"]) == 3
    for fig in hr["figures"]:
        assert "attribution-research-concept" not in fig["file"]
    # concept image lives in Research Question, not Historical Results
    html = INDEX.read_text(encoding="utf-8")
    rq = html.split('id="research-question"', 1)[1].split("</section>", 1)[0]
    assert "attribution-research-concept.png" in rq


def test_root_staging_image_is_removed():
    assert not ROOT_STAGING_IMG.exists()


def test_mobile_grids_use_minmax_zero():
    css = CSS.read_text(encoding="utf-8")
    assert ".results { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert ".figures { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert "repeat(3, minmax(0, 1fr))" in css  # meta-cards
    assert "min-width: 0" in css
    assert "overflow-wrap: anywhere" in css


def test_no_body_overflow_x_hidden_hack():
    css = CSS.read_text(encoding="utf-8")
    assert "overflow-x: hidden" not in css
