"""Command-line interface (FND-005 legacy ``run`` + FAST-001 ``benchmark-run``).

Usage:

    python -m freewill_attribution.cli --help
    python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <dir>
    python -m freewill_attribution.cli benchmark-run --mock --n-per-cell 2 \
        --artifact-root <dir>

Two subcommands:

- ``run`` (legacy / historical workflow): delegates to the safe legacy entry
  point via ``runner.run_legacy_study`` and returns the legacy exit code. It
  still requires ``--mock`` and an explicit ``--out``.
- ``benchmark-run`` (FAST-001): the new reproducible mock benchmark vertical
  slice. It writes artifacts under ``artifacts/runs/<run_id>/`` and requires the
  ``--mock`` flag (no real provider is available; no API key is read).
"""

from __future__ import annotations

import argparse

from . import runner
from .benchmark import registry


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser (separated for testability)."""
    parser = argparse.ArgumentParser(
        prog="python -m freewill_attribution.cli",
        description="Attribution study CLI: legacy run + benchmark vertical slice.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run a mock simulated study via the safe legacy entry point.",
    )
    run_parser.add_argument(
        "--out",
        required=True,
        help="Explicit safe output directory. Required; must not be the "
        "repository outputs/ directory (enforced by the legacy script).",
    )
    run_parser.add_argument("--n-per-cell", type=int, default=20)
    run_parser.add_argument("--seed", type=int, default=20260425)
    run_parser.add_argument("--temperature", type=float, default=1.0)
    run_parser.add_argument(
        "--mock",
        action="store_true",
        required=True,
        help=(
            "Required in the current transitional CLI. "
            "Generate rule-based synthetic data without API calls. "
            "Real API execution is not exposed by this CLI yet."
        ),
    )
    run_parser.add_argument(
        "--fresh",
        action="store_true",
        help="Remove previous raw/wide response files in the output directory.",
    )

    bench = subparsers.add_parser(
        "benchmark-run",
        help="Run the mock benchmark vertical slice (writes artifacts/runs/<run_id>/).",
        # Disable prefix abbreviation so the removed --task alias is not silently
        # accepted as an abbreviation of --task-config.
        allow_abbrev=False,
    )
    bench.add_argument(
        "--artifact-root",
        required=True,
        help="Root directory for run artifacts. A runs/<run_id>/ subtree is "
        "created here. Must not be the repository outputs/ directory.",
    )
    bench.add_argument("--n-per-cell", type=int, default=1)
    bench.add_argument("--seed", type=int, default=20260425)
    bench.add_argument("--max-repair-attempts", type=int, default=1)
    bench.add_argument(
        "--task-config",
        dest="task_config",
        default=str(registry.TASK_DEFAULT_YAML),
        help="Run TaskSpec YAML that drives the run "
        "(default: configs/tasks/attribution_behavior.yaml). This is the RUN "
        "TaskSpec (run capability + condition/identity/metric schema). The "
        "scenarios, condition text, items and Prompt come from the fixed "
        "material task contract at tasks/attribution_behavior/; switching to a "
        "different material contract via the CLI is not supported this round.",
    )
    bench.add_argument(
        "--model-config",
        default=str(registry.MODEL_MOCK_YAML),
        help="Model config YAML (default: configs/model.mock.yaml). Mock only.",
    )
    bench.add_argument("--run-id", default=None)
    bench.add_argument("--fresh", action="store_true", help="Remove prior artifacts in the run dir.")
    bench.add_argument("--resume", action="store_true", help="Resume: skip already-completed records.")
    bench.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "deepseek"],
        help="Provider to use. Only 'mock' actually executes this round; "
        "'deepseek' is offline-validated and supports --dry-run only.",
    )
    bench.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan a future real run offline (no network, no API key). Writes "
        "artifacts/plans/<plan_id>/ only; generates no responses/scores/cost.",
    )
    bench.add_argument(
        "--run-profile",
        default="smoke",
        choices=["smoke", "pilot"],
        help="Dry-run profile: smoke (12 records) or pilot (60 records).",
    )
    bench.add_argument(
        "--real-api",
        action="store_true",
        help="(Deferred) opt in to a real paid API call. Refused this round; "
        "additional preconditions must all be satisfied.",
    )
    bench.add_argument(
        "--confirm-paid-run",
        action="store_true",
        help="(Deferred) explicit confirmation of a paid run. Refused this round.",
    )
    bench.add_argument(
        "--mock",
        action="store_true",
        help="Use the deterministic mock provider (default provider). No real "
        "API is called and no API key is read.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return runner.run_legacy_study(
            output_dir=args.out,
            n_per_cell=args.n_per_cell,
            seed=args.seed,
            temperature=args.temperature,
            mock=args.mock,
            fresh=args.fresh,
        )

    if args.command == "benchmark-run":
        # --- offline dry-run planner (no network, no API key) ----------------
        if args.dry_run:
            model_config = args.model_config
            if args.provider == "deepseek" and model_config == str(registry.MODEL_MOCK_YAML):
                model_config = str(registry.MODEL_DEEPSEEK_EXAMPLE_YAML)
            result = runner.plan_dry_run(
                model_config=model_config,
                run_profile=args.run_profile,
                seed=args.seed,
                artifact_root=args.artifact_root,
                task_config=args.task_config,
                real_api=args.real_api,
                confirm_paid_run=args.confirm_paid_run,
            )
            print(f"dry_run plan_id={result.plan_id}")
            print(f"planned_records={result.planned_records}")
            print(f"plan_dir={result.plan_dir}")
            print("live_run_blockers=" + ("; ".join(result.blockers) or "(none)"))
            print("network_calls_made=0 api_key_read=false")
            return 0

        # --- deferred real provider: refuse a live run this round ------------
        if args.provider == "deepseek":
            print(
                "live deepseek run is refused this round; the real provider is "
                "offline_validated only. Use --dry-run to plan a future run. "
                "No API key was read and no network request was made.",
            )
            return 2

        # --- mock provider (default): execute the reproducible mock slice ----
        result = runner.run_benchmark(
            seed=args.seed,
            n_per_cell=args.n_per_cell,
            artifact_root=args.artifact_root,
            task_config=args.task_config,
            model_config=args.model_config,
            max_repair_attempts=args.max_repair_attempts,
            fresh=args.fresh,
            resume=args.resume,
            run_id=args.run_id,
        )
        manifest = result.manifest
        print(f"run_id={result.run_id}")
        print(f"status={manifest.status.value}")
        print(f"planned={manifest.planned_records} completed={manifest.completed_records} "
              f"failed={manifest.failed_records}")
        print(f"run_dir={result.run_dir}")
        return 0 if manifest.status.value in ("completed", "partial") else 1

    # argparse enforces a required subcommand, so this is defensive only.
    parser.error("No command provided.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
