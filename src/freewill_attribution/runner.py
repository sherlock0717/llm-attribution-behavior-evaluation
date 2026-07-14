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

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import SOURCE_DIR, get_legacy_run_script

# --- path_safety bootstrap (top-level module lives at the src/ layout root) ---
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
from path_safety import resolve_output_dir  # noqa: E402

from .benchmark import artifacts as artifact_io  # noqa: E402
from .benchmark.hashing import hash_object, hash_text  # noqa: E402
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
)
from . import reporting  # noqa: E402
from .providers.base import ProviderRequest  # noqa: E402
from .providers.mock import MockProvider  # noqa: E402
from .tasks.freewill_attribution import parsing, prompting, scoring, spec, stimuli  # noqa: E402


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


def _default_model_spec() -> ModelSpec:
    return ModelSpec(
        provider=MockProvider.provider_name,
        model_id=MockProvider.model_id,
        model_version_snapshot=None,
        sampling_parameters={"temperature": 0.0, "deterministic": True},
        capabilities=["rule_based", "deterministic"],
        endpoint_type="mock",
    )


def _task_spec_payload(task_id: str, n_per_cell: int, seed: int) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_version": spec.TASK_VERSION,
        "conditions": spec.PROCESS_CONDITIONS,
        "identities": spec.IDENTITY_LABELS,
        "item_ids": spec.ITEM_IDS,
        "item_ranges": {k: list(v) for k, v in spec.ITEM_RANGE.items()},
        "batching": "all_items",
        "construct_label_blinding": True,
        "n_per_cell": n_per_cell,
        "seed": seed,
    }


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
    benchmark_id: str = BENCHMARK_ID,
    task_id: str | None = None,
    provider: Any | None = None,
    model_spec: ModelSpec | None = None,
    max_repair_attempts: int = 1,
    fresh: bool = False,
    resume: bool = False,
    run_id: str | None = None,
    git_commit: str | None = None,
    fault_map: dict[str, str] | None = None,
) -> BenchmarkRunResult:
    """Execute the mock benchmark vertical slice and write all artifacts.

    ``fault_map`` maps ``record_id -> fault`` (test-only) to force a malformed /
    incomplete first attempt and exercise the repair path. Normal runs pass None.
    """
    if n_per_cell < 1:
        raise ValueError("n_per_cell must be >= 1")

    provider = provider or MockProvider()
    model_spec = model_spec or _default_model_spec()
    task_id = task_id or spec.TASK_ID
    fault_map = fault_map or {}
    started_at = datetime.now(timezone.utc)

    run_id = run_id or default_run_id(task_id, n_per_cell, seed)
    runs_parent = Path(artifact_root) / "runs" / run_id
    run_dir = resolve_output_dir(runs_parent, create=True)
    figures_dir = run_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = run_dir / "normalized_responses.jsonl"
    if fresh:
        for name in [
            "manifest.json",
            "resolved_config.json",
            "task_spec.json",
            "model_spec.json",
            "prompt_template.txt",
            "prompt_snapshots.jsonl",
            "stimuli_snapshot.jsonl",
            "raw_responses.jsonl",
            "normalized_responses.jsonl",
            "scores.jsonl",
            "failures.jsonl",
            "aggregate_report.json",
        ]:
            candidate = run_dir / name
            if candidate.exists():
                candidate.unlink()

    design = stimuli.build_design(n_per_cell, seed)
    planned = len(design)

    already_done: set[str] = set()
    if resume and normalized_path.exists():
        for row in artifact_io.read_jsonl(normalized_path):
            if row.get("validation_status") == AttemptValidationStatus.OK.value:
                already_done.add(str(row.get("record_id")))

    all_attempt_records: list[ResponseRecord] = []
    raw_rows: list[dict[str, Any]] = []
    prompt_snapshot_rows: list[dict[str, Any]] = []
    normalized_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    failure_rows: list[FailureRecord] = []
    scored_for_agg: list[dict[str, Any]] = []
    raw_text_lengths: dict[str, int] = {}

    prompt_template = prompting.prompt_template_text()
    prompt_template_hash = hash_text(prompt_template)

    def _prompt_ref(text: str) -> str:
        return f"sha256:{hash_text(text)}"

    for row in design:
        record_id = row["record_id"]
        if record_id in already_done:
            continue

        attempt = 1
        final_ratings: dict[str, int] = {}
        final_status = AttemptValidationStatus.NOT_VALIDATED
        parent_attempt_id: str | None = None

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
            response = provider.generate(request)

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

    # --- resume union: merge previously completed rows from disk ------------
    if resume and already_done:
        processed_ids = {r["record_id"] for r in normalized_rows}
        keep_ids = already_done - processed_ids
        if keep_ids:
            prior_raw = [
                r for r in artifact_io.read_jsonl(run_dir / "raw_responses.jsonl")
                if r.get("record_id") in keep_ids
            ]
            prior_prompts = [
                r for r in artifact_io.read_jsonl(run_dir / "prompt_snapshots.jsonl")
                if r.get("record_id") in keep_ids
            ]
            prior_scores = [
                r for r in artifact_io.read_jsonl(run_dir / "scores.jsonl")
                if r.get("record_id") in keep_ids
            ]
            prior_norm = [
                r for r in artifact_io.read_jsonl(normalized_path)
                if r.get("record_id") in keep_ids
            ]
            raw_rows = prior_raw + raw_rows
            prompt_snapshot_rows = prior_prompts + prompt_snapshot_rows
            score_rows = prior_scores + score_rows
            normalized_rows = prior_norm + normalized_rows

            for nr in prior_norm:
                rid = nr["record_id"]
                ratings = {k: v for k, v in nr.get("ratings", {}).items() if v is not None}
                parsed = {"items": [{"item_id": k, "rating": v} for k, v in ratings.items()]}
                all_attempt_records.append(
                    ResponseRecord(
                        record_id=rid,
                        run_id=run_id,
                        task_id=task_id,
                        condition=nr["condition"],
                        identity=nr["identity"],
                        stimulus_id=nr["stimulus_id"],
                        scenario_id=nr["scenario_id"],
                        request_index=0,
                        batch_id="all_items",
                        attempt=int(nr.get("final_attempt", 1)),
                        parse_status=AttemptParseStatus.OK,
                        validation_status=AttemptValidationStatus(nr["validation_status"]),
                        parsed_response=parsed,
                    )
                )
                finals = [r for r in prior_raw if r.get("record_id") == rid]
                if finals:
                    raw_text_lengths[rid] = len(str(finals[-1].get("raw_text", "")))
                if nr.get("validation_status") == AttemptValidationStatus.OK.value:
                    scored_for_agg.append(
                        {
                            "condition": nr["condition"],
                            "identity": nr["identity"],
                            "scores": nr.get("scores", {}),
                        }
                    )
        normalized_rows.sort(key=lambda r: r["record_id"])
        raw_rows.sort(key=lambda r: (r.get("record_id", ""), r.get("attempt", 0)))

    # --- aggregate + metrics -------------------------------------------------
    agg_scores = scoring.aggregate_scores(scored_for_agg)
    metrics = reporting.compute_metrics(
        planned=planned,
        records=all_attempt_records,
        scored_records=scored_for_agg,
        aggregate_scores=agg_scores,
        raw_text_lengths=raw_text_lengths,
    )

    # --- write artifacts -----------------------------------------------------
    task_payload = _task_spec_payload(task_id, n_per_cell, seed)
    model_payload = model_spec.model_dump(mode="json")
    scoring_payload = _scoring_spec_payload()
    resolved_config = {
        "benchmark_id": benchmark_id,
        "benchmark_version": BENCHMARK_VERSION,
        "task_id": task_id,
        "task_version": spec.TASK_VERSION,
        "seed": seed,
        "n_per_cell": n_per_cell,
        "max_repair_attempts": max_repair_attempts,
        "provider": model_spec.provider,
        "model_id": model_spec.model_id,
        "prompt_template_id": prompting.PROMPT_TEMPLATE_ID,
        "prompt_template_version": prompting.PROMPT_TEMPLATE_VERSION,
    }

    stimulus_set = stimuli.canonical_stimulus_set()
    stimulus_snapshot_rows = stimuli.stimulus_snapshot(design)

    artifacts: list[ArtifactRef] = []
    artifacts.append(artifact_io.write_json_artifact(run_dir / "resolved_config.json", resolved_config, role="resolved_config"))
    artifacts.append(artifact_io.write_json_artifact(run_dir / "task_spec.json", task_payload, role="task_spec"))
    artifacts.append(artifact_io.write_json_artifact(run_dir / "model_spec.json", model_payload, role="model_spec"))
    artifacts.append(artifact_io.write_json_artifact(run_dir / "scoring_spec.json", scoring_payload, role="scoring_spec"))
    artifacts.append(artifact_io.write_text_artifact(run_dir / "prompt_template.txt", prompt_template, role="prompt_template"))
    artifacts.append(artifact_io.write_jsonl_artifact(run_dir / "prompt_snapshots.jsonl", prompt_snapshot_rows, role="prompt_snapshots"))
    artifacts.append(artifact_io.write_jsonl_artifact(run_dir / "stimuli_snapshot.jsonl", stimulus_snapshot_rows, role="stimuli_snapshot"))
    artifacts.append(artifact_io.write_jsonl_artifact(run_dir / "raw_responses.jsonl", raw_rows, role="raw_responses"))
    artifacts.append(artifact_io.write_jsonl_artifact(normalized_path, normalized_rows, role="normalized_responses"))
    artifacts.append(artifact_io.write_jsonl_artifact(run_dir / "scores.jsonl", score_rows, role="scores"))
    artifacts.append(artifact_io.write_jsonl_artifact(run_dir / "failures.jsonl", [f.model_dump(mode="json") for f in failure_rows], role="failures"))

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
    artifacts.append(
        artifact_io.write_json_artifact(
            run_dir / "aggregate_report.json", aggregate_report.model_dump(mode="json"), role="aggregate_report"
        )
    )

    manifest = RunManifest(
        run_id=run_id,
        status=status,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        git_commit=git_commit,
        benchmark_version=BENCHMARK_VERSION,
        task_version=spec.TASK_VERSION,
        resolved_config_hash=hash_object(resolved_config),
        task_spec_hash=hash_object(task_payload),
        model_spec_hash=hash_object(model_payload),
        prompt_template_hash=prompt_template_hash,
        prompt_snapshot_set_hash=hash_object(prompt_snapshot_rows),
        stimulus_set_hash=hash_object(stimulus_set),
        scoring_spec_hash=hash_object(scoring_payload),
        provider=model_spec.provider,
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
    )
    artifact_io.write_json_artifact(run_dir / "manifest.json", manifest.model_dump(mode="json"), role="manifest")

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


__all__ = [
    "build_legacy_run_command",
    "run_legacy_study",
    "BENCHMARK_ID",
    "BENCHMARK_VERSION",
    "BenchmarkRunResult",
    "default_run_id",
    "run_benchmark",
]
