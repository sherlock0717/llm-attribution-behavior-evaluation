"""Tests for scripts/build_showcase_data.py (SHOWCASE-RELEASE-001).

Never calls the network / any API, never modifies outputs/; only reads
repository source files plus the generated site/data JSON.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_showcase_data.py"
DATA_DIR = REPO_ROOT / "site" / "data"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_showcase_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_showcase_data"] = module
    spec.loader.exec_module(module)
    return module


bsc = _load_module()


def test_build_all_has_four_documents():
    built = bsc.build_all()
    assert set(built) == {
        "showcase_story.json",
        "measurement_summary.json",
        "analysis_results.json",
        "reproducibility_summary.json",
    }


def test_measurement_summary_counts():
    m = bsc.build_measurement_summary()
    assert m["total_constructs"] == 10
    assert m["total_items"] == 34
    for c in m["constructs"]:
        assert c["n_items"] >= 1
        assert c["range"] in ("0–2", "1–7")
        assert 0.0 <= c["alpha"] <= 1.0


def test_story_core_facts_are_derived():
    s = bsc.build_showcase_story()
    facts = {f["key"]: f["value"] for f in s["core_facts"]}
    assert facts["historical_record_count"] == 360
    assert facts["process_condition_count"] == 6
    assert facts["identity_condition_count"] == 2
    assert facts["scenario_count"] == 8
    assert facts["item_count"] == 34
    assert facts["construct_count"] == 10
    assert s["title_zh"] == "LLM 归因行为评测"
    assert s["subtitle_en"] == "A Reproducible Study and Evaluation Prototype"


def test_story_scenarios_carry_case_content():
    s = bsc.build_showcase_story()
    cards = {c["id"]: c for c in s["scenarios"]}
    assert len(cards) == 8
    # scenario case content is read faithfully from src/stimuli.py
    for stim in bsc.stimuli.SCENARIOS:
        c = cards[stim.scenario_id]
        assert c["context"] == stim.context
        assert c["option_a"] == stim.option_a
        assert c["option_b"] == stim.option_b
        assert c["fixed_choice"] == stim.fixed_choice
        assert c["domain"] == stim.domain
        assert c["label"]


def test_reproducibility_summary_shape():
    r = bsc.build_reproducibility_summary()
    assert len(r["eval_steps"]) == 5
    assert r["eval_commands"] and all(isinstance(c, str) for c in r["eval_commands"])
    assert len(r["artifact_table"]) == 6
    assert len(r["real_provider"]["flow"]) == 5
    assert len(r["benchmark_roadmap"]["flow"]) == 6
    # precise smoke/pilot counts must not leak into the public JSON
    blob = str(r["real_provider"]) + str(r["benchmark_roadmap"])
    assert "12" not in blob and "60" not in blob


def test_analysis_mediation_crosses_zero_flags():
    a = bsc.build_analysis_results()
    paths = {p["name"]: p for p in a["mediation"]["paths"]}
    assert paths["agency"]["crosses_zero"] is False
    assert paths["perceived_intelligence"]["crosses_zero"] is True


def test_controlled_regression_survival_pattern():
    a = bsc.build_analysis_results()
    rows = {r["dv"]: r for r in a["controlled_regression"]["rows"]}
    agency = {s["spec"]: s for s in rows["agency"]["specs"]}
    fw = {s["spec"]: s for s in rows["free_will_attribution"]["specs"]}
    # agency process effect survives control_both; free-will does not
    assert agency["control_both"]["survives"] is True
    assert fw["control_both"]["survives"] is False


def test_planned_contrasts_are_source_present_only():
    a = bsc.build_analysis_results()
    for g in a["planned_contrasts"]["groups"]:
        assert g["contrasts"]
        for c in g["contrasts"]:
            # source file has diff/t/p but NO confidence interval; never fabricate one
            assert "ci_low" not in c and "ci_high" not in c


def test_build_is_deterministic():
    assert bsc.build_measurement_summary()["constructs"] == \
        bsc.build_measurement_summary()["constructs"]
    a1 = bsc.build_analysis_results()
    a1.pop("generated_at")
    a2 = bsc.build_analysis_results()
    a2.pop("generated_at")
    assert a1 == a2


def test_missing_source_raises_build_error(tmp_path, monkeypatch):
    monkeypatch.setattr(bsc.bsd, "ROOT", tmp_path)
    with pytest.raises(bsc.BuildError):
        bsc.build_measurement_summary()


@pytest.mark.skipif(not DATA_DIR.exists(), reason="site/data not generated yet")
def test_check_mode_reports_up_to_date():
    assert bsc.main(["--check"]) == 0
