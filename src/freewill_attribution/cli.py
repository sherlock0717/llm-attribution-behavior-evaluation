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
    bench.add_argument("--task-config", default=None, help="Optional task config path (reserved).")
    bench.add_argument("--model-config", default=None, help="Optional model config path (reserved).")
    bench.add_argument("--run-id", default=None)
    bench.add_argument("--fresh", action="store_true", help="Remove prior artifacts in the run dir.")
    bench.add_argument("--resume", action="store_true", help="Resume: skip already-completed records.")
    bench.add_argument(
        "--mock",
        action="store_true",
        required=True,
        help="Required. Only the deterministic mock provider is available; no "
        "real API is called and no API key is read.",
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
        result = runner.run_benchmark(
            seed=args.seed,
            n_per_cell=args.n_per_cell,
            artifact_root=args.artifact_root,
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
