"""Transitional command-line interface (FND-005 / FND-005.1).

Usage:

    python -m freewill_attribution.cli --help
    python -m freewill_attribution.cli run --mock --n-per-cell 2 --out <dir>

This CLI uses only the Python standard library (argparse). The ``run`` command
delegates to the safe legacy entry point via ``runner.run_legacy_study`` and
returns the legacy process exit code.

Current transitional scope: this package CLI only exposes **mock** runs. The
``--mock`` flag is therefore required; real API execution is not exposed by
this CLI yet (it awaits DEC-012 and formal run governance). The CLI does not
read API keys and does not default to writing the repository ``outputs/``
directory (the legacy script enforces a safe --out).
"""

from __future__ import annotations

import argparse

from . import runner


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser (separated for testability)."""
    parser = argparse.ArgumentParser(
        prog="python -m freewill_attribution.cli",
        description="Transitional CLI over the safe legacy run entry point.",
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

    # argparse enforces a required subcommand, so this is defensive only.
    parser.error("No command provided.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
