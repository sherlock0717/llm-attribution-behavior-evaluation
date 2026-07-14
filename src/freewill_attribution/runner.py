"""Runner: legacy adapter (historical workflow) + benchmark vertical slice (FAST-001).

This module has two clearly separated parts:

1. **Legacy historical workflow** (``build_legacy_run_command`` /
   ``run_legacy_study``): a thin subprocess adapter over the frozen v1 script
   ``src/run_simulated_study.py``. It is retained ONLY as a historical/legacy
   workflow and is NOT used as the execution path of the new benchmark runner.

2. **Benchmark vertical slice** (``run_benchmark``): the new reproducible run
   core. It drives TaskSpec -> Stimulus -> Prompt -> Provider -> Raw Response ->
   Parser -> Validation -> Optional Repair -> Score -> Aggregate -> Manifest,
   writing all artifacts under ``artifacts/runs/<run_id>/`` (Git ignored). It
   never calls a real API and reads no API keys. Only the deterministic mock
   provider is wired in this round.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .paths import PROJECT_ROOT, SOURCE_DIR, get_legacy_run_script

# --- path_safety bootstrap (top-level module lives at the src/ layout root) ---
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
from path_safety import resolve_output_dir  # noqa: E402

from .benchmark import artifacts as artifact_io  # noqa: E402
from .benchmark import registry  # noqa: E402
from .benchmark.hashing import hash_file, hash_object, hash_text  # noqa: E402
from .benchmark.models import (  # noqa: E402
    AggregateReport,
    ArtifactRef,
    AttemptParseStatus,
    AttemptValidationStatus,
    FailureRecord,
    ModelSpec,
    ResponseRecord,
    RunManifest,
    RunStatus,
    TaskSpec,
)
from . import reporting  # noqa: E402
from .providers.base import ProviderRequest  # noqa: E402
from .providers.mock import MockProvider  # noqa: E402
from .tasks.freewill_attribution import parsing, prompting, scoring, spec, stimuli  # noqa: E402


class RunConfigError(RuntimeError):
    """Raised when the task/model config is incompatible with the task pack."""


# ===========================================================================
# 1. Legacy historical workflow (unchanged; retained for parity/tests)
# ===========================================================================


def build_legacy_run_command(
    *,
    output_dir: str | Path,
    n_per_cell: int = 20,
    seed: int = 20260425,
    temperature: float = 1.0,
    mock: bool = False,
    fresh: bool = False,
) -> list[str]:
    """Build the argument list for invoking the legacy run script."""
    script = get_legacy_run_script()
    command = [
        sys.executable,
        str(script),
        "--out",
        str(output_dir),
        "--n-per-cell",
        str(n_per_cell),
        "--seed",
        str(seed),
        "--temperature",
        str(temperature),
    ]
    if mock:
        command.append("--mock")
    if fresh:
        command.append("--fresh")
    return command


def run_legacy_study(
    *,
    output_dir: str | Path,
    n_per_cell: int = 20,
    seed: int = 20260425,
    temperature: float = 1.0,
    mock: bool = False,
    fresh: bool = False,
) -> int:
    """Run the legacy study script as a subprocess and return its exit code."""
    command = build_legacy_run_command(
        output_dir=output_dir,
        n_per_cell=n_per_cell,
        seed=seed,
        temperature=temperature,
        mock=mock,
        fresh=fresh,
    )
    result = subprocess.run(command)  # noqa: S603 - list args, no shell
    return result.returncode


# ===========================================================================
# 2. Benchmark vertical slice (new reproducible run core)
# ===========================================================================

BENCHMARK_ID = "llm-attribution-behavior"
BENCHMARK_VERSION = "0.1-draft"


@dataclass
class BenchmarkRunResult:
    run_id: str
    run_dir: Path
    manifest: RunManifest
    aggregate_report: AggregateReport
    records: list[ResponseRecord]


def default_run_id(task_id: str, n_per_cell: int, seed: int) -> str:
    short = task_id.replace("freewill-attribution-", "fa-")
    return f"{short}-n{n_per_cell}-seed{seed}"


def _detect_git_commit(explicit: str | None) -> tuple[str, list[str]]:
    """Return ``(git_commit, provenance_notes)``.

    When ``explicit`` is provided it is used verbatim. Otherwise ``git rev-parse
    HEAD`` is run against the repository root. If git is unavailable the commit
    is recorded as ``"unknown"`` and a provenance note explains why (we never
    fabricate a commit id).
    """
    if explicit:
        return explicit, []
    try:
        proc = subprocess.run(  # noqa: S603 - fixed args, no shell
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        sha = proc.stdout.strip()
        if proc.returncode == 0 and sha:
            return sha, []
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown", [
        "git_commit could not be determined (git unavailable or not a git "
        "checkout); recorded as 'unknown' rather than fabricated."
    ]


def _repo_relative(path: str | Path) -> str:
    """Return ``path`` relative to the repo root (falls back to the file name)."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.name


def _load_and_validate_specs(
    task_config: str | Path,
    model_config: str | Path,
    provider_name: str,
) -> tuple[TaskSpec, ModelSpec]:
    """Load + validate the declarative TaskSpec/ModelSpec against the task pack.

    Fails loudly (``RunConfigError``) on any incompatibility. There is NO silent
    fallback to hard-coded defaults: a run only proceeds when the contract on
    disk truly drives it.
    """
    task_spec = registry.load_task_spec(task_config)
    model_spec = registry.load_model_spec(model_config)

    problems = spec.taskspec_consistency_problems(task_spec)
    if not task_spec.executable:
        problems.append("task is not executable (executable=false)")
    supported = list(task_spec.model_dump().get("supported_providers") or [])
    if provider_name not in supported:
        problems.append(
            f"provider {provider_name!r} not in task.supported_providers {supported}"
        )
    if model_spec.provider != "mock":
        problems.append(
            f"model provider must be 'mock' this round, got {model_spec.provider!r}"
        )
    if problems:
        raise RunConfigError(
            "Task/model config is not compatible with the implemented task pack: "
            + "; ".join(problems)
        )
    return task_spec, model_spec


def _scoring_spec_payload() -> dict[str, Any]:
    return {
        "aggregation": "item_mean",
        "scales": {k: sorted(v) for k, v in spec.SCALE_ITEMS.items()},
        "condition_contrasts": [list(c) for c in spec.CONDITION_CONTRASTS],
        "scoring_version": "0.1",
    }


def run_benchmark(
    *,
    seed: int,
    n_per_cell: int,
    artifact_root: str | Path,
    task_config: str | Path | None = None,
    model_config: str | Path | None = None,
    benchmark_id: str = BENCHMARK_ID,
    provider: Any | None = None,
    max_repair_attempts: int = 1,
    fresh: bool = False,
    resume: bool = False,
    run_id: str | None = None,
    git_commit: str | None = None,
    fault_map: dict[str, str] | None = None,
) -> BenchmarkRunResult:
    """Execute the mock benchmark vertical slice and write all artifacts.

    The run is DRIVEN BY the declarative contracts on disk: the TaskSpec YAML
    (default ``configs/tasks/freewill_attribution.v2.yaml``) and the model
    config YAML (default ``configs/model.mock.yaml``) are loaded, validated
    against the implemented task pack, and used as the source of the recorded
    ``task_spec.json`` / ``model_spec.json`` and their hashes.

    ``fault_map`` maps ``record_id -> fault`` (test-only) to force a malformed /
    incomplete first attempt (or a provider exception) and exercise the repair /
    failure paths. Normal runs pass None.
    """
    if n_per_cell < 1:
        raise ValueError("n_per_cell must be >= 1")

    task_config = Path(task_config) if task_config else registry.TASK_V2_YAML
    model_config = Path(model_config) if model_config else registry.MODEL_MOCK_YAML

    provider = provider or MockProvider()
    provider_name = getattr(provider, "provider_name", "mock")

    # Contract-driven: load + validate the declarative specs (fail loudly, no
    # silent fallback to hard-coded defaults).
    task_spec, model_spec = _load_and_validate_specs(task_config, model_config, provider_name)
    task_id = task_spec.task_id
    fault_map = fault_map or {}
    started_at = datetime.now(timezone.utc)
    git_commit_value, provenance_notes = _detect_git_commit(git_commit)

    run_id = run_id or default_run_id(task_id, n_per_cell, seed)
    runs_parent = Path(artifact_root) / "runs" / run_id
    # Validate the path is a safe output target (rejects outputs/, src/, ...).
    run_dir = resolve_output_dir(runs_parent, create=False)

    # --- overwrite protection / fresh / resume ------------------------------
    existing = run_dir.exists() and (
        (run_dir / "manifest.json").exists()
        or (run_dir / "response_records.jsonl").exists()
    )
    if fresh:
        # run_dir has already passed the safe-output-path check above, so the
        # whole tree (including stale figures/ or any future files) is removed.
        if run_dir.exists():
            shutil.rmtree(run_dir)
    elif existing and not resume:
        raise RunConfigError(
            f"Run directory already exists with prior artifacts: {run_dir.as_posix()}. "
            "Refusing to overwrite. Pass fresh=True to recreate it or resume=True "
            "to continue the existing run."
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = run_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = run_dir / "normalized_responses.jsonl"
    response_records_path = run_dir / "response_records.jsonl"

    # --- resume: restore prior attempts from response_records.jsonl ---------
    prior_attempts_by_id: dict[str, list[dict[str, Any]]] = {}
    prior_raw_by_id: dict[str, list[dict[str, Any]]] = {}
    prior_prompt_by_id: dict[str, list[dict[str, Any]]] = {}
    prior_norm_by_id: dict[str, dict[str, Any]] = {}
    prior_scores_by_id: dict[str, list[dict[str, Any]]] = {}
    done_ids: set[str] = set()
    if resume:
        for rec in artifact_io.read_jsonl(response_records_path):
            prior_attempts_by_id.setdefault(str(rec.get("record_id")), []).append(rec)
        for row in artifact_io.read_jsonl(run_dir / "raw_responses.jsonl"):
            prior_raw_by_id.setdefault(str(row.get("record_id")), []).append(row)
        for row in artifact_io.read_jsonl(run_dir / "prompt_snapshots.jsonl"):
            prior_prompt_by_id.setdefault(str(row.get("record_id")), []).append(row)
        for row in artifact_io.read_jsonl(normalized_path):
            prior_norm_by_id[str(row.get("record_id"))] = row
        for row in artifact_io.read_jsonl(run_dir / "scores.jsonl"):
            prior_scores_by_id.setdefault(str(row.get("record_id")), []).append(row)
        for rid, attempts in prior_attempts_by_id.items():
            last = max(attempts, key=lambda a: a.get("attempt", 0))
            if last.get("validation_status") == AttemptValidationStatus.OK.value:
                done_ids.add(rid)

    design = stimuli.build_design(n_per_cell, seed)
    planned = len(design)

    all_attempt_records: list[ResponseRecord] = []
    raw_rows: list[dict[str, Any]] = []
    prompt_snapshot_rows: list[dict[str, Any]] = []
    normalized_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    response_record_rows: list[dict[str, Any]] = []
    failure_rows: list[FailureRecord] = []
    scored_for_agg: list[dict[str, Any]] = []
    raw_text_lengths: dict[str, int] = {}

    prompt_template = prompting.prompt_template_text()
    prompt_template_hash = hash_text(prompt_template)

    def _prompt_ref(text: str) -> str:
        return f"sha256:{hash_text(text)}"

    for row in design:
        record_id = row["record_id"]

        # ---- resume reuse: keep ALL prior attempts verbatim (no fabrication) ----
        if resume and record_id in done_ids:
            for rec in sorted(
                prior_attempts_by_id.get(record_id, []), key=lambda a: a.get("attempt", 0)
            ):
                all_attempt_records.append(ResponseRecord.model_validate(rec))
                response_record_rows.append(rec)
            raw_rows.extend(prior_raw_by_id.get(record_id, []))
            prompt_snapshot_rows.extend(prior_prompt_by_id.get(record_id, []))
            if record_id in prior_norm_by_id:
                normalized_rows.append(prior_norm_by_id[record_id])
            score_rows.extend(prior_scores_by_id.get(record_id, []))
            reused_raw = prior_raw_by_id.get(record_id, [])
            if reused_raw:
                last_raw = max(reused_raw, key=lambda r: r.get("attempt", 0))
                raw_text_lengths[record_id] = len(str(last_raw.get("raw_text", "")))
            nr = prior_norm_by_id.get(record_id, {})
            if nr.get("validation_status") == AttemptValidationStatus.OK.value:
                scored_for_agg.append(
                    {"condition": nr["condition"], "identity": nr["identity"],
                     "scores": nr.get("scores", {})}
                )
            continue

        # ---- run this record ----
        attempt = 1
        final_ratings: dict[str, int] = {}
        final_status = AttemptValidationStatus.NOT_VALIDATED
        parent_attempt_id: str | None = None
        last_detail: dict = {}

        while True:
            base_prompt = prompting.render_prompt(row)
            if attempt > 1:
                prompt_text = base_prompt + "\n" + prompting.repair_instruction(
                    missing=last_detail.get("missing", []),
                    out_of_range=last_detail.get("out_of_range", []),
                )
            else:
                prompt_text = base_prompt

            fault = fault_map.get(record_id) if attempt == 1 else None
            request = ProviderRequest(
                prompt=prompt_text,
                task_id=task_id,
                condition=row["condition"],
                identity=row["identity"],
                scenario_id=row["scenario_id"],
                seed=seed,
                request_index=attempt - 1,
                attempt=attempt,
                item_specs=tuple(spec.ITEM_SPECS),
                structure_level=row["structure_level"],
                choice_valence=row["choice_valence"],
                fault=fault,
            )
            try:
                response = provider.generate(request)
            except Exception as exc:  # noqa: BLE001 - a provider fault must not lose the run
                # A single provider exception must NOT crash the whole run
                # without a manifest: record a FailureRecord and finalize the
                # record as failed. Real retry/budget policy is RUN-003.
                failure_rows.append(
                    FailureRecord(
                        failure_code="PROVIDER_UNAVAILABLE",
                        stage="provider",
                        failure_scope="record",
                        terminal_scope="record",
                        severity="error",
                        record_id=record_id,
                        attempt=attempt,
                        message=f"provider raised for record {record_id}: "
                        f"{type(exc).__name__}",
                        context={"attempt": attempt},
                    )
                )
                final_status = AttemptValidationStatus.NOT_VALIDATED
                break

            parsed, parse_status, _pmsg = parsing.parse_response(response.text)
            if parsed is None:
                ratings: dict[str, int] = {}
                validation_status = AttemptValidationStatus.SCHEMA_FAILURE
                last_detail = {"missing": list(spec.ITEM_IDS), "out_of_range": []}
            else:
                ratings, validation_status, last_detail, _vmsg = parsing.validate_core(parsed)

            attempt_record_id = f"{record_id}#a{attempt}"
            raw_ref = f"sha256:{hash_text(response.text)}"
            record = ResponseRecord(
                record_id=record_id,
                run_id=run_id,
                task_id=task_id,
                condition=row["condition"],
                identity=row["identity"],
                stimulus_id=row["stimulus_id"],
                scenario_id=row["scenario_id"],
                request_index=attempt - 1,
                batch_id="all_items",
                attempt=attempt,
                parent_attempt_id=parent_attempt_id,
                persona_ref=f"sha256:{hash_object(row['persona'])}",
                prompt_ref=_prompt_ref(prompt_text),
                request_ref=f"sha256:{hash_text(request.prompt)}",
                raw_response_ref=raw_ref,
                parsed_response=parsed,
                parse_status=parse_status,
                validation_status=validation_status,
                latency_ms=response.latency_ms,
                usage=response.usage,
                provider_metadata=dict(response.raw_metadata),
            )
            all_attempt_records.append(record)
            response_record_rows.append(record.model_dump(mode="json"))

            raw_rows.append(
                {
                    "attempt_id": attempt_record_id,
                    "record_id": record_id,
                    "attempt": attempt,
                    "parent_attempt_id": parent_attempt_id,
                    "condition": row["condition"],
                    "identity": row["identity"],
                    "stimulus_id": row["stimulus_id"],
                    "provider": response.provider,
                    "model_id": response.model_id,
                    "finish_reason": response.finish_reason,
                    "latency_ms": response.latency_ms,
                    "usage": response.usage,
                    "raw_text": response.text,
                    "raw_response_sha256": hash_text(response.text),
                    "parse_status": parse_status.value,
                    "validation_status": validation_status.value,
                }
            )
            prompt_snapshot_rows.append(
                {
                    "attempt_id": attempt_record_id,
                    "record_id": record_id,
                    "attempt": attempt,
                    "prompt_sha256": hash_text(prompt_text),
                    "prompt_text": prompt_text,
                }
            )

            final_ratings = ratings
            final_status = validation_status
            raw_text_lengths[record_id] = len(response.text)

            if validation_status == AttemptValidationStatus.OK:
                break
            if attempt > max_repair_attempts:
                failure_rows.append(
                    FailureRecord(
                        failure_code="REPAIR_EXHAUSTED"
                        if attempt > 1
                        else _validation_failure_code(validation_status, parse_status),
                        stage="validation",
                        failure_scope="record",
                        terminal_scope="record",
                        severity="error",
                        record_id=record_id,
                        attempt=attempt,
                        message=f"record {record_id} failed after {attempt} attempt(s): "
                        f"{validation_status.value}",
                        context={"detail": last_detail},
                    )
                )
                break
            parent_attempt_id = attempt_record_id
            attempt += 1

        record_scores = scoring.score_ratings(final_ratings)
        normalized_rows.append(
            {
                "record_id": record_id,
                "run_id": run_id,
                "condition": row["condition"],
                "identity": row["identity"],
                "stimulus_id": row["stimulus_id"],
                "scenario_id": row["scenario_id"],
                "structure_level": row["structure_level"],
                "final_attempt": attempt,
                "validation_status": final_status.value,
                "ratings": final_ratings,
                "scores": record_scores,
            }
        )
        for scale, value in record_scores.items():
            score_rows.append(
                {
                    "record_id": record_id,
                    "metric_id": scale,
                    "raw_value": value,
                    "scoring_version": "0.1",
                }
            )
        if final_status == AttemptValidationStatus.OK:
            scored_for_agg.append(
                {"condition": row["condition"], "identity": row["identity"], "scores": record_scores}
            )

    # Deterministic ordering (design order is already deterministic; sort keeps
    # a fresh full run and a no-op resume byte-identical).
    normalized_rows.sort(key=lambda r: r["record_id"])
    raw_rows.sort(key=lambda r: (r.get("record_id", ""), r.get("attempt", 0)))
    prompt_snapshot_rows.sort(key=lambda r: (r.get("record_id", ""), r.get("attempt", 0)))
    score_rows.sort(key=lambda r: (r.get("record_id", ""), r.get("metric_id", "")))
    response_record_rows.sort(key=lambda r: (r.get("record_id", ""), r.get("attempt", 0)))

    # --- aggregate + metrics -------------------------------------------------
    agg_scores = scoring.aggregate_scores(scored_for_agg)
    metrics = reporting.compute_metrics(
        planned=planned,
        records=all_attempt_records,
        scored_records=scored_for_agg,
        aggregate_scores=agg_scores,
        raw_text_lengths=raw_text_lengths,
    )

    # --- write artifacts (portable, run-dir-relative paths) -----------------
    task_payload = task_spec.model_dump(mode="json")
    model_payload = model_spec.model_dump(mode="json")
    scoring_payload = _scoring_spec_payload()
    task_config_sha = hash_file(task_config)
    model_config_sha = hash_file(model_config)
    resolved_config = {
        "benchmark_id": benchmark_id,
        "benchmark_version": BENCHMARK_VERSION,
        "task_config_ref": _repo_relative(task_config),
        "task_config_sha256": task_config_sha,
        "model_config_ref": _repo_relative(model_config),
        "model_config_sha256": model_config_sha,
        "task_id": task_id,
        "task_version": task_spec.task_version,
        "provider": provider_name,
        "model_id": model_spec.model_id,
        "seed": seed,
        "n_per_cell": n_per_cell,
        "max_repair_attempts": max_repair_attempts,
        "artifact_root_relative": f"runs/{run_id}",
        "prompt_template_id": prompting.PROMPT_TEMPLATE_ID,
        "prompt_template_version": prompting.PROMPT_TEMPLATE_VERSION,
    }

    stimulus_set = stimuli.canonical_stimulus_set()
    stimulus_snapshot_rows = stimuli.stimulus_snapshot(design)

    def _json(name: str, obj: Any, role: str) -> ArtifactRef:
        return artifact_io.write_json_artifact(run_dir / name, obj, role=role, base_dir=run_dir)

    def _jsonl(name: str, rows: list[dict[str, Any]], role: str) -> ArtifactRef:
        return artifact_io.write_jsonl_artifact(run_dir / name, rows, role=role, base_dir=run_dir)

    artifacts: list[ArtifactRef] = [
        _json("resolved_config.json", resolved_config, "resolved_config"),
        _json("task_spec.json", task_payload, "task_spec"),
        _json("model_spec.json", model_payload, "model_spec"),
        _json("scoring_spec.json", scoring_payload, "scoring_spec"),
        artifact_io.write_text_artifact(
            run_dir / "prompt_template.txt", prompt_template, role="prompt_template", base_dir=run_dir
        ),
        _jsonl("prompt_snapshots.jsonl", prompt_snapshot_rows, "prompt_snapshots"),
        _jsonl("stimuli_snapshot.jsonl", stimulus_snapshot_rows, "stimuli_snapshot"),
        _jsonl("raw_responses.jsonl", raw_rows, "raw_responses"),
        _jsonl("response_records.jsonl", response_record_rows, "response_records"),
        _jsonl("normalized_responses.jsonl", normalized_rows, "normalized_responses"),
        _jsonl("scores.jsonl", score_rows, "scores"),
        _jsonl("failures.jsonl", [f.model_dump(mode="json") for f in failure_rows], "failures"),
    ]

    completed = int(metrics["execution_quality"]["completed_record_count"])
    failed = int(metrics["execution_quality"]["failed_record_count"])
    status = RunStatus.COMPLETED if failed == 0 else RunStatus.PARTIAL

    aggregate_report = reporting.build_aggregate_report(
        run_id=run_id,
        benchmark_id=benchmark_id,
        task_id=task_id,
        metrics=metrics,
        artifact_refs=list(artifacts),
        figure_refs=[],
    )
    artifacts.append(_json("aggregate_report.json", aggregate_report.model_dump(mode="json"), "aggregate_report"))

    manifest = RunManifest(
        run_id=run_id,
        status=status,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        git_commit=git_commit_value,
        benchmark_version=BENCHMARK_VERSION,
        task_version=task_spec.task_version,
        resolved_config_hash=hash_object(resolved_config),
        task_spec_hash=hash_object(task_payload),
        model_spec_hash=hash_object(model_payload),
        prompt_template_hash=prompt_template_hash,
        prompt_snapshot_set_hash=hash_object(prompt_snapshot_rows),
        stimulus_set_hash=hash_object(stimulus_set),
        scoring_spec_hash=hash_object(scoring_payload),
        provider=provider_name,
        model_id=model_spec.model_id,
        model_snapshot=model_spec.model_version_snapshot,
        planned_records=planned,
        completed_records=completed,
        failed_records=failed,
        retry_count=int(round((metrics["output_quality"].get("repair_trigger_rate") or 0.0) * planned)),
        parse_failure_count=sum(
            1 for r in all_attempt_records if r.parse_status != AttemptParseStatus.OK
        ),
        schema_failure_count=sum(
            1
            for r in all_attempt_records
            if r.validation_status != AttemptValidationStatus.OK
        ),
        token_usage=None,
        estimated_cost_usd=None,
        artifacts=list(artifacts),
        errors=failure_rows,
        provenance_notes=provenance_notes,
    )
    # manifest.json is the integrity index; it is NOT part of its own artifact
    # list. Its digest is written separately to manifest.sha256 (no self-cycle).
    manifest_path = run_dir / "manifest.json"
    artifact_io.write_json_artifact(
        manifest_path, manifest.model_dump(mode="json"), role="manifest", base_dir=run_dir
    )
    (run_dir / "manifest.sha256").write_text(
        hash_file(manifest_path) + "\n", encoding="utf-8", newline="\n"
    )

    # --- re-verify manifest artifacts against files on disk ------------------
    problems = artifact_io.verify_artifacts(artifacts, run_dir)
    if problems:
        raise RuntimeError("Artifact integrity check failed: " + "; ".join(problems))

    return BenchmarkRunResult(
        run_id=run_id,
        run_dir=run_dir,
        manifest=manifest,
        aggregate_report=aggregate_report,
        records=all_attempt_records,
    )


def _validation_failure_code(
    validation_status: AttemptValidationStatus, parse_status: AttemptParseStatus
) -> str:
    if parse_status == AttemptParseStatus.EMPTY:
        return "EMPTY_RESPONSE"
    if parse_status in (AttemptParseStatus.MALFORMED_JSON, AttemptParseStatus.PARSE_FAILURE):
        return "MALFORMED_JSON"
    mapping = {
        AttemptValidationStatus.MISSING_ITEM: "MISSING_ITEM",
        AttemptValidationStatus.OUT_OF_RANGE: "OUT_OF_RANGE",
        AttemptValidationStatus.DUPLICATE_ITEM: "DUPLICATE_RESPONSE_SUSPECTED",
        AttemptValidationStatus.UNKNOWN_ITEM: "SCHEMA_FAILURE",
        AttemptValidationStatus.SCHEMA_FAILURE: "SCHEMA_FAILURE",
    }
    return mapping.get(validation_status, "SCHEMA_FAILURE")


# ===========================================================================
# 3. Offline dry-run planner for the (deferred) real DeepSeek provider
# ===========================================================================

RUN_PROFILE_DEFAULTS = {"smoke": 1, "pilot": 5}


@dataclass
class DryRunResult:
    plan_id: str
    plan_dir: Path
    planned_records: int
    blockers: list[str]
    readiness: dict[str, Any]


def _scrub_model_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return a snapshot of the model config with any credential value removed.

    The template never stores a key, but we defensively drop anything that
    could carry one and assert the credential is environment-sourced.
    """
    snapshot = dict(config)
    cred = dict(snapshot.get("credential") or {})
    cred.pop("value", None)
    cred["value_stored_in_config"] = False
    snapshot["credential"] = cred
    # never carry a resolved key anywhere
    snapshot.pop("api_key", None)
    return snapshot


def plan_dry_run(
    *,
    model_config: str | Path,
    run_profile: str = "smoke",
    seed: int = 20260425,
    artifact_root: str | Path = "artifacts",
    task_config: str | Path | None = None,
    plan_id: str | None = None,
    real_api: bool = False,
    confirm_paid_run: bool = False,
) -> DryRunResult:
    """Plan a future real run WITHOUT any network or credential access.

    Writes plan artifacts under ``artifacts/plans/<plan_id>/`` (Git ignored).
    Generates NO responses, scores, usage, cost or latency. Reads NO API key.
    """
    from .providers import deepseek as _deepseek  # local import: no networking
    from . import budget as _budget

    task_config = Path(task_config) if task_config else registry.TASK_V2_YAML
    model_config = Path(model_config)

    raw_model = yaml.safe_load(model_config.read_text(encoding="utf-8")) or {}
    profiles = raw_model.get("run_profiles") or {}
    profile_cfg = profiles.get(run_profile) or {}
    n_per_cell = int(profile_cfg.get("n_per_cell", RUN_PROFILE_DEFAULTS.get(run_profile, 1)))

    task_spec = registry.load_task_spec(task_config)
    # Consistency with the implemented task pack (same guard as the mock runner).
    problems = spec.taskspec_consistency_problems(task_spec)
    if problems:
        raise RunConfigError("task config incompatible with task pack: " + "; ".join(problems))

    design = stimuli.build_design(n_per_cell, seed)
    planned = len(design)

    plan_id = plan_id or f"dryrun-deepseek-{run_profile}-seed{seed}"
    plan_dir = resolve_output_dir(Path(artifact_root) / "plans" / plan_id, create=False)
    if plan_dir.exists():
        shutil.rmtree(plan_dir)
    plan_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = prompting.prompt_template_text()

    # request plan: one entry per planned record (no response, no cost).
    request_rows: list[dict[str, Any]] = []
    for row in design:
        prompt_text = prompting.render_prompt(row)
        request_rows.append(
            {
                "record_id": row["record_id"],
                "condition": row["condition"],
                "identity": row["identity"],
                "scenario_id": row["scenario_id"],
                "stimulus_id": row["stimulus_id"],
                "prompt_sha256": hash_text(prompt_text),
                "max_tokens": int(raw_model.get("max_tokens", 2048)),
                "temperature": raw_model.get("temperature", 0),
                "response_format": (raw_model.get("response_format") or {}).get("type", "json_object"),
            }
        )
    stimuli_rows = stimuli.stimulus_snapshot(design)

    blockers = _deepseek.live_run_blockers(
        raw_model, real_api=real_api, confirm_paid_run=confirm_paid_run
    )
    pricing = _budget.PricingSnapshot.from_config(raw_model.get("pricing_snapshot"))
    cost_estimate = _budget.dry_run_cost_estimate(pricing)

    model_snapshot = _scrub_model_config(raw_model)
    task_payload = task_spec.model_dump(mode="json")
    resolved_config = {
        "benchmark_id": BENCHMARK_ID,
        "benchmark_version": BENCHMARK_VERSION,
        "task_config_ref": _repo_relative(task_config),
        "task_config_sha256": hash_file(task_config),
        "model_config_ref": _repo_relative(model_config),
        "model_config_sha256": hash_file(model_config),
        "task_id": task_spec.task_id,
        "task_version": task_spec.task_version,
        "provider": raw_model.get("provider", "deepseek"),
        "run_profile": run_profile,
        "seed": seed,
        "n_per_cell": n_per_cell,
        "planned_records": planned,
        "max_tokens": int(raw_model.get("max_tokens", 2048)),
        "artifact_root_relative": f"plans/{plan_id}",
        "prompt_template_id": prompting.PROMPT_TEMPLATE_ID,
        "prompt_template_version": prompting.PROMPT_TEMPLATE_VERSION,
    }

    cells: dict[str, int] = {}
    for row in design:
        key = f"{row['condition']}|{row['identity']}"
        cells[key] = cells.get(key, 0) + 1

    readiness = {
        "provider_adapter_status": "offline_validated",
        "credential_status": "not_configured",
        "live_api_status": "not_run",
        "real_smoke_status": "not_run",
        "real_pilot_status": "not_run",
        "model_id_status": "requires_runtime_verification",
        "pricing_status": "requires_runtime_verification",
        "result_analysis_status": "not_applicable",
        "network_calls_made": 0,
        "api_key_read": False,
        "live_run_blockers": blockers,
        "cost_estimate": cost_estimate,
        "requirements_before_live_run": raw_model.get("requirements_before_live_run", []),
    }
    plan = {
        "plan_id": plan_id,
        "provider": raw_model.get("provider", "deepseek"),
        "run_profile": run_profile,
        "planned_records": planned,
        "n_per_cell": n_per_cell,
        "concurrency": int(profile_cfg.get("concurrency", 1)),
        "cell_distribution": cells,
        "prompt_template_sha256": hash_text(prompt_template),
        "resolved_config_sha256": hash_object(resolved_config),
        "task_spec_sha256": hash_object(task_payload),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "OFFLINE dry-run plan only. No request was sent; no response, "
        "usage, cost or latency exists. Not a real run.",
    }

    artifact_io.write_json_artifact(plan_dir / "plan.json", plan, role="plan", base_dir=plan_dir)
    artifact_io.write_json_artifact(plan_dir / "resolved_config.json", resolved_config, role="resolved_config", base_dir=plan_dir)
    artifact_io.write_json_artifact(plan_dir / "task_spec.json", task_payload, role="task_spec", base_dir=plan_dir)
    artifact_io.write_json_artifact(plan_dir / "model_config_snapshot.json", model_snapshot, role="model_config_snapshot", base_dir=plan_dir)
    artifact_io.write_text_artifact(plan_dir / "prompt_template.txt", prompt_template, role="prompt_template", base_dir=plan_dir)
    artifact_io.write_jsonl_artifact(plan_dir / "stimuli_plan.jsonl", stimuli_rows, role="stimuli_plan", base_dir=plan_dir)
    artifact_io.write_jsonl_artifact(plan_dir / "request_plan.jsonl", request_rows, role="request_plan", base_dir=plan_dir)
    artifact_io.write_json_artifact(plan_dir / "readiness_report.json", readiness, role="readiness_report", base_dir=plan_dir)

    return DryRunResult(
        plan_id=plan_id,
        plan_dir=plan_dir,
        planned_records=planned,
        blockers=blockers,
        readiness=readiness,
    )


__all__ = [
    "build_legacy_run_command",
    "run_legacy_study",
    "BENCHMARK_ID",
    "BENCHMARK_VERSION",
    "BenchmarkRunResult",
    "RunConfigError",
    "DryRunResult",
    "default_run_id",
    "run_benchmark",
    "plan_dry_run",
]
