"""Contract consistency tests for RES-001 + BMK-001 (RBC-001.1 corrected).

Documentation and YAML contracts only. No runner/provider, no network.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs"
DOCS = ROOT / "docs"

TASK_V1 = CONFIGS / "tasks" / "freewill_attribution.v1.yaml"
TASK_V2 = CONFIGS / "tasks" / "freewill_attribution.v2.yaml"
BENCH = CONFIGS / "benchmarks" / "llm_attribution_behavior.v1.yaml"
METRICS = CONFIGS / "metrics" / "attribution_metrics.v1.yaml"
SOURCE_MAP = DOCS / "audit" / "research_protocol_source_map.md"
FAILURE_TAX = DOCS / "benchmark" / "FAILURE_TAXONOMY.md"
BENCH_SPEC = DOCS / "benchmark" / "BENCHMARK_SPEC.md"
METRIC_SPEC = DOCS / "benchmark" / "METRIC_SPEC.md"
V2_PROTO = DOCS / "protocols" / "freewill_attribution_v2.md"
BACKLOG = DOCS / "planning" / "EXECUTION_BACKLOG.md"

YAML_FILES = [TASK_V1, TASK_V2, BENCH, METRICS]

EXPECTED_CONDITIONS = [
    "direct_choice", "direct_choice_long", "alternatives",
    "reasons_concise", "reasons", "reflection_feedback",
]
EXPECTED_IDENTITIES = ["AI 决策者", "人类决策者"]

REQUIRED_TASKSPEC_FIELDS = [
    "task_id", "task_version", "protocol_ref", "constructs", "condition_schema",
    "identity_schema", "stimulus_set", "prompt_config", "response_schema",
    "scoring_config", "aggregation_config", "evidence_boundary", "status", "executable",
]
REQUIRED_BENCH_FIELDS = [
    "benchmark_id", "benchmark_version", "title", "description", "task_ids",
    "metric_ids", "current_maturity_level", "target_maturity_level",
    "release_status", "license_status", "created_at", "source_commit",
]

SECRET_KEY_NAMES = {"api_key", "api-key", "access_token", "secret", "authorization",
                    "bearer", "deepseek_api_key"}
SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"DEEPSEEK_API_KEY\s*=\s*\S+"),
    re.compile(r"api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9]{16,}", re.I),
    re.compile(r"authorization\s*:\s*bearer\s+\S+", re.I),
]
DOC_SCAN = [SOURCE_MAP, FAILURE_TAX, BENCH_SPEC, METRIC_SPEC,
            DOCS / "protocols" / "freewill_attribution_v1_historical.md", V2_PROTO]


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def registry_ids():
    return [m["metric_id"] for m in load(METRICS)["metrics"]]


# ---- basic ----
def test_yaml_safe_load():
    for p in YAML_FILES:
        assert p.exists()
        load(p)


def test_top_level_mapping():
    for p in YAML_FILES:
        assert isinstance(load(p), dict)


def test_benchmark_id_consistent():
    assert load(BENCH)["benchmark_id"] == "llm-attribution-behavior"


def test_task_ids_unique():
    ids = [load(TASK_V1)["task_id"], load(TASK_V2)["task_id"]]
    assert len(ids) == len(set(ids))


def test_benchmark_tasks_exist():
    task_ids = {load(TASK_V1)["task_id"], load(TASK_V2)["task_id"]}
    for tid in load(BENCH)["task_ids"]:
        assert tid in task_ids


def test_task_metrics_exist():
    reg = set(registry_ids())
    for task in (TASK_V1, TASK_V2):
        for mid in load(task)["scoring_config"]["metric_ids"]:
            assert mid in reg, f"{task.name}: unknown metric {mid}"


def test_benchmark_metric_ids_subset_registry():
    reg = set(registry_ids())
    for mid in load(BENCH)["metric_ids"]:
        assert mid in reg


def test_protocol_refs_exist():
    for task in (TASK_V1, TASK_V2):
        ref = (task.parent / load(task)["protocol_ref"]).resolve()
        assert ref.exists()


def test_failure_taxonomy_ref_exists():
    ref = (TASK_V2.parent / load(TASK_V2)["failure_taxonomy_ref"]).resolve()
    assert ref.exists() and FAILURE_TAX.exists()


# ---- v1 ----
def test_v1_executable_false_and_status():
    d = load(TASK_V1)
    assert d["executable"] is False
    assert d["status"] == "historical_reconstructed"


def test_v1_prompt_provenance_false():
    pp = load(TASK_V1)["prompt_config"]["prompt_provenance"]
    assert pp["exact_snapshot_available"] is False
    assert pp["exact_hash_available"] is False
    assert pp["reconstruction_status"] == "partial"


def test_v1_record_count_and_n_per_cell_in_legacy():
    lm = load(TASK_V1)["legacy_metadata"]
    assert lm["historical_record_count"] == 360
    assert lm["n_per_cell"] == 30


def test_v1_condition_and_identity_counts():
    d = load(TASK_V1)
    assert len(d["condition_schema"]["conditions"]) == 6
    assert len(d["identity_schema"]["identities"]) == 2


def test_v1_seed_and_model_are_reconstruction_only():
    lm = load(TASK_V1)["legacy_metadata"]
    assert "seed_code_default" in lm and "seed" not in lm  # not a confirmed run seed
    assert "model_id_reconstruction_candidate" in lm


# ---- v2 ----
def test_v2_mock_executable_status():
    # FAST-001: v2 is implemented against the MOCK provider only.
    d = load(TASK_V2)
    assert d["executable"] is True
    assert d["status"] == "implemented_mock"
    assert d["supported_providers"] == ["mock"]


def test_v2_response_schema_no_runner_owned_metadata():
    d = load(TASK_V2)["response_schema"]
    item_keys = set()
    for it in d["core"]["items"]:
        item_keys |= set(it.keys())
    assert item_keys <= {"item_id", "rating"}, f"core item has extra keys: {item_keys}"
    runner_owned = set(d["runner_owned_fields"])
    for meta in ["participant_id", "condition", "identity", "run_id", "task_id",
                 "stimulus_id", "scenario_id", "batch_id", "attempt", "response_version"]:
        assert meta in runner_owned
    assert "attention_check" in d["removed_from_core"]


def test_v2_core_batching_not_by_construct():
    b = load(TASK_V2)["prompt_config"]["batching"]
    assert b["decision_status"] == "unresolved"
    assert b["recommended_core_default"] == "all_items"
    assert b["recommended_core_default"] != "by_construct"


def test_v2_construct_label_blinding_name_accurate():
    pc = load(TASK_V2)["prompt_config"]
    assert "construct_label_blinding" in pc
    assert "construct_blinding" not in pc


def test_v2_mock_only_not_real_and_open_questions_frozen():
    # Mock-implemented, but must NOT claim a real provider or a real run.
    d = load(TASK_V2)
    assert d["supported_providers"] == ["mock"]
    assert "implementation_decisions" in d
    assert d["open_questions"] == []  # eight Q-* frozen into decisions
    # benchmark maturity must remain pre-BMK-L1 (no BMK-L1 achieved claim)
    assert load(BENCH)["current_maturity_level"] == "pre-BMK-L1"


# ---- benchmark maturity / fields ----
def test_benchmark_yaml_contains_all_required_spec_fields():
    d = load(BENCH)
    for f in REQUIRED_BENCH_FIELDS:
        assert f in d, f"benchmark missing required field {f}"


def test_v1_task_yaml_matches_required_taskspec_fields():
    d = load(TASK_V1)
    for f in REQUIRED_TASKSPEC_FIELDS:
        assert f in d, f"v1 task missing {f}"


def test_v2_task_yaml_matches_required_taskspec_fields():
    d = load(TASK_V2)
    for f in REQUIRED_TASKSPEC_FIELDS:
        assert f in d, f"v2 task missing {f}"


def test_current_maturity_is_not_target_maturity():
    d = load(BENCH)
    assert d["current_maturity_level"] == "pre-BMK-L1"
    assert d["target_maturity_level"] == "BMK-L1"
    assert d["current_maturity_level"] != d["target_maturity_level"]
    assert "maturity_level" not in d  # the old single field must be gone


def test_executable_state_v1_historical_v2_mock_only():
    # v1 stays a non-executable historical reconstruction.
    assert load(TASK_V1)["executable"] is False
    # v2 is executable ONLY via the mock provider; benchmark maturity unchanged.
    assert load(TASK_V2)["executable"] is True
    assert load(TASK_V2)["supported_providers"] == ["mock"]
    assert load(BENCH)["current_maturity_level"] == "pre-BMK-L1"


def test_maturity_not_claimed_achieved():
    txt = BENCH_SPEC.read_text(encoding="utf-8")
    assert "current_maturity_level" in txt and "target_maturity_level" in txt
    assert "pre-BMK-L1" in txt


# ---- metrics ----
def test_metric_ids_unique():
    ids = registry_ids()
    assert len(ids) == len(set(ids))


def test_metric_registry_count_is_computed_not_hardcoded():
    # registry expanded beyond original 39; count must be derivable from YAML.
    assert len(registry_ids()) >= 40
    assert "动态计算" in METRIC_SPEC.read_text(encoding="utf-8")


def test_v1_item_missing_rate_is_unknown():
    for m in load(METRICS)["metrics"]:
        if m["metric_id"] == "missing_item_rate":
            assert m.get("v1_historical_status") == "unknown"
            return
    raise AssertionError("missing_item_rate not registered")


def test_v2_comparison_metrics_are_registered():
    reg = set(registry_ids())
    for mid in ["first_attempt_parse_success_rate", "final_parse_success_rate",
                "first_attempt_schema_compliance_rate", "final_schema_compliance_rate",
                "repair_trigger_rate", "repair_success_rate",
                "response_length_chars", "response_length_tokens"]:
        assert mid in reg, f"comparison metric {mid} not registered"


def test_metric_ids_in_docs_exist_in_registry():
    reg = set(registry_ids())
    # metric ids referenced in v2 protocol quality metrics section (§15) and comparison (§17)
    text = V2_PROTO.read_text(encoding="utf-8")
    referenced = set(re.findall(r"(?<![\w-])((?:first_attempt|final)_(?:parse|schema)_\w+|"
                                r"repair_(?:trigger|success)_rate|response_length_\w+|"
                                r"missing_item_rate|range_validity_rate|condition_sensitivity|"
                                r"identity_effect|repeat_run_stability)", text))
    for mid in referenced:
        assert mid in reg, f"doc references unregistered metric {mid}"


def test_repair_trigger_direction_is_context():
    for m in load(METRICS)["metrics"]:
        if m["metric_id"] == "repair_trigger_rate":
            assert m["direction"] == "context"
            return
    raise AssertionError("repair_trigger_rate missing")


# ---- failure taxonomy ----
def _failure_rows():
    text = FAILURE_TAX.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\| ([A-Z][A-Z_]+) \| (\w+) \| (\w+) \| (\w+) \|", line)
        if m:
            rows.append(m.groups())
    return rows


def test_failure_codes_unique():
    codes = [r[0] for r in _failure_rows()]
    assert len(codes) >= 23
    assert len(codes) == len(set(codes))


def test_failure_taxonomy_has_scoring_failure():
    codes = {r[0] for r in _failure_rows()}
    assert "SCORING_FAILURE" in codes
    assert "PROMPT_RENDER_FAILURE" in codes
    assert "STIMULUS_INVALID" in codes
    assert "DUPLICATE_RESPONSE_SUSPECTED" in codes


def test_failure_codes_define_scope():
    valid_fscope = {"run", "request", "record", "artifact"}
    for code, stage, fscope, tscope in _failure_rows():
        assert fscope in valid_fscope, f"{code} bad failure_scope {fscope}"


def test_terminal_scope_is_valid():
    valid_tscope = {"none", "attempt", "record", "run"}
    for code, stage, fscope, tscope in _failure_rows():
        assert tscope in valid_tscope, f"{code} bad terminal_scope {tscope}"


# ---- planning ids ----
def _active_task_ids():
    text = BACKLOG.read_text(encoding="utf-8")
    m = re.search(r"<!-- ACTIVE_TASK_IDS_START -->(.*?)<!-- ACTIVE_TASK_IDS_END -->",
                  text, flags=re.S)
    assert m, "active task id block missing"
    ids = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if "|" in line:
            ids.append(line.split("|")[0].strip())
    return ids


def test_active_planning_task_ids_are_unique():
    ids = _active_task_ids()
    assert len(ids) == len(set(ids)), f"duplicate active task ids: {ids}"
    for key in ["RES-001", "BMK-001", "RUN-001"]:
        assert ids.count(key) == 1


def test_legacy_headings_are_marked():
    text = BACKLOG.read_text(encoding="utf-8")
    # any '### RES/BMK/RUN-<n> ·' heading must be LEGACY-marked
    for m in re.finditer(r"^### (?:LEGACY )?((?:RES|BMK|RUN)-\d+)(\(old\))? ·", text, flags=re.M):
        heading = m.group(0)
        assert "LEGACY" in heading, f"unmarked legacy heading: {heading}"


def test_run001_is_mock_run_core():
    ids = dict(l.split("|", 1) for l in
               re.search(r"START -->(.*?)<!-- ACTIVE", BACKLOG.read_text(encoding="utf-8"), re.S).group(1).strip().splitlines())
    title = ids["RUN-001 "].strip()
    assert "Mock Run Core" in title


# ---- source map / gate ----
def test_source_gate_pass_and_scope():
    t = SOURCE_MAP.read_text(encoding="utf-8")
    assert "PROTOCOL_SOURCE_GATE=PASS" in t
    assert "gate_scope: historical_protocol_reconstruction_only" in t


def test_source_map_not_claim_item_missing_zero():
    t = SOURCE_MAP.read_text(encoding="utf-8")
    # explicit: aggregate no-missing does NOT prove item-level presence
    assert ("无法证明" in t or "不能证明" in t) and "题项" in t


def test_condition_keys_match_source_map():
    smap = SOURCE_MAP.read_text(encoding="utf-8")
    for c in load(TASK_V1)["condition_schema"]["conditions"]:
        assert c in EXPECTED_CONDITIONS and c in smap


def test_identity_values_match_source_map():
    smap = SOURCE_MAP.read_text(encoding="utf-8")
    for i in load(TASK_V1)["identity_schema"]["identities"]:
        assert i in EXPECTED_IDENTITIES and i in smap


# ---- hygiene ----
def test_no_local_evidence_dir_in_repo():
    assert not (ROOT / "local_evidence").exists(), "local_evidence/ must not exist in repo worktree"


def test_no_secret_key_fields_in_yaml():
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                assert str(k).lower() not in SECRET_KEY_NAMES, f"secret key field: {k}"
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)
    for p in YAML_FILES:
        walk(load(p))


def test_no_secret_values():
    for p in YAML_FILES + DOC_SCAN:
        text = p.read_text(encoding="utf-8")
        for pat in SECRET_VALUE_PATTERNS:
            assert not pat.search(text), f"secret-like value in {p.name}"


def test_no_windows_abs_path_in_contracts():
    for p in YAML_FILES + DOC_SCAN:
        assert "C:\\Users\\" not in p.read_text(encoding="utf-8"), f"abs path in {p.name}"


def test_markdown_local_links_exist():
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in DOC_SCAN:
        if not md.exists():
            continue
        for target in link_re.findall(md.read_text(encoding="utf-8")):
            if target.startswith("http") or target.startswith("#"):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            assert (md.parent / target).resolve().exists(), f"broken link {target} in {md.name}"
