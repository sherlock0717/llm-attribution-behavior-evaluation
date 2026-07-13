#!/usr/bin/env bash
# Cross-platform mock run wrapper (FND-008) delegating to the package CLI.
#
# Thin wrapper over: python -m freewill_attribution.cli run
# Only explicit mock runs are supported. No real API mode, no API key is read,
# no research logic is copied, and the repository historical outputs/ is never
# written. Without --out, a unique system-temp directory is used. The CLI exit
# code is preserved.
set -euo pipefail

print_usage() {
    cat <<'USAGE'
Usage: run_all.sh --mock [--out PATH] [--n-per-cell N] [--seed N] [--temperature VALUE] [--fresh] [--help]

Runs a mock simulated study via 'python -m freewill_attribution.cli run'.
Only mock runs are supported; no real API mode, no API key is read.
Without --out, a unique system-temp directory is used (never the repository outputs/).

Examples:
  run_all.sh --mock --n-per-cell 1 --seed 20260425 --out /tmp/run
  run_all.sh --mock
USAGE
}

caller_pwd="$PWD"

mock=false
fresh=false
out_arg=""
have_out=false
n_per_cell=20
seed=20260425
temperature=1.0

err() {
    printf 'error: %s\n' "$1" >&2
}

require_separate_value() {
    # $1 = option name, $2 = remaining arg count ($#), $3 = candidate value ($2 of caller)
    option_name="$1"
    remaining_count="$2"
    next_value="${3-}"

    if [ "$remaining_count" -lt 2 ]; then
        err "missing value for $option_name"
        exit 2
    fi

    case "$next_value" in
        --*)
            err "missing value for $option_name"
            exit 2
            ;;
    esac

    if [ -z "$next_value" ]; then
        err "empty value for $option_name"
        exit 2
    fi
}

require_equal_value() {
    # $1 = option name, $2 = provided value (already split from --opt=value)
    option_name="$1"
    provided_value="$2"

    if [ -z "$provided_value" ]; then
        err "empty value for $option_name"
        exit 2
    fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --mock)
            mock=true
            shift
            ;;
        --fresh)
            fresh=true
            shift
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        --out)
            require_separate_value "--out" "$#" "${2-}"
            out_arg="$2"; have_out=true; shift 2
            ;;
        --out=*)
            value="${1#*=}"
            require_equal_value "--out" "$value"
            out_arg="$value"; have_out=true; shift
            ;;
        --n-per-cell)
            require_separate_value "--n-per-cell" "$#" "${2-}"
            n_per_cell="$2"; shift 2
            ;;
        --n-per-cell=*)
            value="${1#*=}"
            require_equal_value "--n-per-cell" "$value"
            n_per_cell="$value"; shift
            ;;
        --seed)
            require_separate_value "--seed" "$#" "${2-}"
            seed="$2"; shift 2
            ;;
        --seed=*)
            value="${1#*=}"
            require_equal_value "--seed" "$value"
            seed="$value"; shift
            ;;
        --temperature)
            require_separate_value "--temperature" "$#" "${2-}"
            temperature="$2"; shift 2
            ;;
        --temperature=*)
            value="${1#*=}"
            require_equal_value "--temperature" "$value"
            temperature="$value"; shift
            ;;
        *)
            err "unknown argument: $1"
            exit 2
            ;;
    esac
done

if [ "$mock" != true ]; then
    err "--mock is required (this wrapper only supports explicit mock runs)."
    exit 2
fi

script_dir="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd -P
)"
repo_root="$(
    cd -- "$script_dir/.."
    pwd -P
)"

uv_bin=""
if command -v uv >/dev/null 2>&1; then
    uv_bin="$(command -v uv)"
elif [ -x "$repo_root/.venv/bin/uv" ]; then
    uv_bin="$repo_root/.venv/bin/uv"
elif [ -x "$repo_root/.venv/Scripts/uv.exe" ]; then
    uv_bin="$repo_root/.venv/Scripts/uv.exe"
else
    err "uv not found on PATH or in <repo>/.venv. Install uv manually; this wrapper will not download it."
    exit 127
fi

if [ "$have_out" = true ]; then
    case "$out_arg" in
        /*|[A-Za-z]:[\\/]*)
            out_dir="$out_arg"
            ;;
        *)
            out_dir="$caller_pwd/$out_arg"
            ;;
    esac
else
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    rand="${RANDOM}${RANDOM}"
    out_dir="${TMPDIR:-/tmp}/freewill-attribution/run-${stamp}-$$-${rand}"
fi

uv_args=(
    run
    --frozen
    python
    -m
    freewill_attribution.cli
    run
    --mock
    --n-per-cell "$n_per_cell"
    --seed "$seed"
    --temperature "$temperature"
    --out "$out_dir"
)
if [ "$fresh" = true ]; then
    uv_args+=(--fresh)
fi

printf 'OUTPUT_DIR=%s\n' "$out_dir"

(
    cd -- "$repo_root"
    exec "$uv_bin" "${uv_args[@]}"
)
