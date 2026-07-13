"""Integration tests for the cross-platform mock run wrappers (FND-008).

These tests cover static contracts of ``scripts/run_all.ps1`` and
``scripts/run_all.sh`` plus platform behaviour (the appropriate wrapper for the
current OS). They never call the real API, never set PYTHONPATH, always run
from a working directory outside the repository, and remove DEEPSEEK_API_KEY
from the subprocess environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
PS1 = SCRIPTS / "run_all.ps1"
SH = SCRIPTS / "run_all.sh"
ROOT_PS1 = REPO_ROOT / "run_all.ps1"
REPO_OUTPUTS = REPO_ROOT / "outputs"

SEED = 20260425
IS_WINDOWS = os.name == "nt"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _clean_env():
    env = dict(os.environ)
    env.pop("DEEPSEEK_API_KEY", None)
    env["MPLBACKEND"] = "Agg"
    env.pop("PYTHONPATH", None)
    return env


def _ps1_text():
    return PS1.read_text(encoding="utf-8")


def _sh_bytes():
    return SH.read_bytes()


def _sh_text():
    return SH.read_text(encoding="utf-8")


def _find_powershell():
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _find_bash():
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def _run_ps1(args, cwd):
    shell = _find_powershell()
    if shell is None:
        pytest.skip("No PowerShell (pwsh/powershell) available on this platform.")
    cmd = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=_clean_env())


def _run_sh(args, cwd):
    shell = _find_bash()
    if shell is None:
        if IS_WINDOWS:
            pytest.skip("No bash available on this Windows host.")
        raise AssertionError("bash is required on non-Windows platforms but was not found.")
    cmd = [shell, str(SH), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=_clean_env())


def _run_wrapper(args, cwd):
    if IS_WINDOWS:
        return _run_ps1(args, cwd)
    return _run_sh(args, cwd)


def _wrapper_mock_args(out_dir, n_per_cell=1, extra=None):
    extra = extra or []
    if IS_WINDOWS:
        args = ["-Mock", "-NPerCell", str(n_per_cell), "-Seed", str(SEED), "-OutDir", str(out_dir)]
    else:
        args = ["--mock", "--n-per-cell", str(n_per_cell), "--seed", str(SEED), "--out", str(out_dir)]
    return args + extra


def _count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _outputs_manifest():
    manifest = {}
    if not REPO_OUTPUTS.exists():
        return manifest
    for p in REPO_OUTPUTS.rglob("*"):
        if p.is_file():
            data = p.read_bytes()
            manifest[p.relative_to(REPO_OUTPUTS).as_posix()] = (
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
    return manifest


# --------------------------------------------------------------------------
# Static contract tests
# --------------------------------------------------------------------------


def test_both_scripts_exist():
    assert PS1.is_file()
    assert SH.is_file()


def test_root_run_all_ps1_still_exists():
    assert ROOT_PS1.is_file()


def test_bash_shebang_first_line():
    first = _sh_bytes().split(b"\n", 1)[0]
    assert first == b"#!/usr/bin/env bash"


def test_bash_has_no_bom():
    assert not _sh_bytes().startswith(b"\xef\xbb\xbf")


def test_bash_has_no_crlf():
    assert b"\r" not in _sh_bytes()


@pytest.mark.parametrize("token", [
    "freewill_attribution.cli",
    "run",
    "--mock",
    "--out",
    "--n-per-cell",
    "--seed",
    "--temperature",
])
def test_both_scripts_contain_required_tokens(token):
    assert token in _ps1_text()
    assert token in _sh_text()


@pytest.mark.parametrize("token", [
    "DEEPSEEK_API_KEY",
    "load_client",
    "call_deepseek",
    "--real-api",
    "run_simulated_study.py",
])
def test_scripts_have_no_forbidden_tokens(token):
    assert token not in _ps1_text()
    assert token not in _sh_text()


def test_scripts_do_not_call_root_run_all():
    # The wrappers must not shell out to the repo-root run_all.ps1.
    assert "run_all.ps1" not in _sh_text()
    # In the PS1 wrapper, only its own header/usage mentions run_all.ps1 as text;
    # ensure there is no invocation of the root script (& ... run_all.ps1 / call).
    ps = _ps1_text()
    assert "..\\run_all.ps1" not in ps
    assert "../run_all.ps1" not in ps


def test_bash_has_no_eval():
    text = _sh_text()
    assert "eval " not in text
    assert "eval\t" not in text


def test_powershell_has_no_invoke_expression():
    assert "Invoke-Expression" not in _ps1_text()
    assert "iex " not in _ps1_text()


def test_powershell_has_no_start_process():
    assert "Start-Process" not in _ps1_text()


def test_default_output_uses_system_temp():
    assert "GetTempPath" in _ps1_text()
    assert "freewill-attribution" in _ps1_text()
    sh = _sh_text()
    assert "TMPDIR" in sh
    assert "freewill-attribution" in sh


def test_default_output_is_not_repo_outputs():
    # The assembled --out default must never be the repository outputs directory.
    assert '--out\n    outputs' not in _ps1_text()
    for text in (_ps1_text(), _sh_text()):
        # No default assignment pointing the output at repo outputs/.
        assert 'out_dir="outputs"' not in text
        assert 'ResolvedOut = "outputs"' not in text
        assert "$RepoRoot\\outputs" not in text
        assert '$repo_root/outputs' not in text


# --------------------------------------------------------------------------
# Platform behaviour tests
# --------------------------------------------------------------------------


def test_help_exits_zero_without_output(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    args = ["-Help"] if IS_WINDOWS else ["--help"]
    result = _run_wrapper(args, cwd=work)
    assert result.returncode == 0, result.stderr
    assert list(work.iterdir()) == []


def test_missing_mock_fails(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    target = tmp_path / "must-not-exist"
    if IS_WINDOWS:
        args = ["-NPerCell", "1", "-Seed", str(SEED), "-OutDir", str(target)]
    else:
        args = ["--n-per-cell", "1", "--seed", str(SEED), "--out", str(target)]
    result = _run_wrapper(args, cwd=work)
    assert result.returncode == 2, (result.returncode, result.stderr)
    assert "mock" in (result.stderr + result.stdout).lower()
    assert not target.exists()


def test_explicit_safe_output_with_spaces(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    out_dir = tmp_path / "safe out dir"
    result = _run_wrapper(_wrapper_mock_args(out_dir), cwd=work)
    assert result.returncode == 0, result.stderr
    raw = out_dir / "raw_simulated_responses.jsonl"
    wide = out_dir / "simulated_responses_wide.csv"
    assert raw.is_file()
    assert wide.is_file()
    assert _count_jsonl(raw) == 12
    for line in raw.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            assert rec.get("synthetic") is True
            assert rec.get("short_reason") == "mock synthetic response"


def test_wrapper_matches_direct_cli_bytewise(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    wrapper_dir = tmp_path / "wrapper out"
    direct_dir = tmp_path / "direct out"

    wrapped = _run_wrapper(_wrapper_mock_args(wrapper_dir), cwd=work)
    assert wrapped.returncode == 0, wrapped.stderr

    direct = subprocess.run(
        [sys.executable, "-m", "freewill_attribution.cli", "run", "--mock",
         "--n-per-cell", "1", "--seed", str(SEED), "--out", str(direct_dir)],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=_clean_env(),
    )
    assert direct.returncode == 0, direct.stderr

    for name in ("raw_simulated_responses.jsonl", "simulated_responses_wide.csv"):
        assert (wrapper_dir / name).read_bytes() == (direct_dir / name).read_bytes(), name


def test_wrapper_rejects_repo_outputs(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    before = _outputs_manifest()
    result = _run_wrapper(_wrapper_mock_args(REPO_OUTPUTS), cwd=work)
    assert result.returncode != 0
    assert _outputs_manifest() == before


def test_fresh_preserves_sentinel(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    out_dir = tmp_path / "fresh out"

    first = _run_wrapper(_wrapper_mock_args(out_dir), cwd=work)
    assert first.returncode == 0, first.stderr

    sentinel = out_dir / "sentinel.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    fresh_flag = ["-Fresh"] if IS_WINDOWS else ["--fresh"]
    second = _run_wrapper(_wrapper_mock_args(out_dir, extra=fresh_flag), cwd=work)
    assert second.returncode == 0, second.stderr

    assert (out_dir / "raw_simulated_responses.jsonl").is_file()
    assert (out_dir / "simulated_responses_wide.csv").is_file()
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "keep me"


def test_default_temp_output(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    args = ["-Mock", "-NPerCell", "1", "-Seed", str(SEED)] if IS_WINDOWS \
        else ["--mock", "--n-per-cell", "1", "--seed", str(SEED)]
    result = _run_wrapper(args, cwd=work)
    assert result.returncode == 0, result.stderr

    out_line = [line for line in result.stdout.splitlines() if line.startswith("OUTPUT_DIR=")]
    assert out_line, result.stdout
    out_dir = Path(out_line[0].split("=", 1)[1].strip())
    try:
        assert out_dir.is_dir()
        # Must not be inside the repository.
        assert REPO_ROOT not in out_dir.resolve().parents
        assert (out_dir / "raw_simulated_responses.jsonl").is_file()
        assert (out_dir / "simulated_responses_wide.csv").is_file()
    finally:
        if out_dir.exists() and REPO_ROOT not in out_dir.resolve().parents:
            shutil.rmtree(out_dir, ignore_errors=True)


# --------------------------------------------------------------------------
# FND-008.1: Bash missing / empty option-value guards
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args, option_name",
    [
        (["--out"], "--out"),
        (["--out", "--fresh", "--mock"], "--out"),
        (["--mock", "--out="], "--out"),
        (["--mock", "--n-per-cell"], "--n-per-cell"),
        (["--mock", "--n-per-cell", "--fresh"], "--n-per-cell"),
        (["--mock", "--n-per-cell="], "--n-per-cell"),
        (["--mock", "--seed"], "--seed"),
        (["--mock", "--seed", "--fresh"], "--seed"),
        (["--mock", "--seed="], "--seed"),
        (["--mock", "--temperature"], "--temperature"),
        (["--mock", "--temperature", "--fresh"], "--temperature"),
        (["--mock", "--temperature="], "--temperature"),
    ],
)
def test_bash_rejects_missing_or_empty_option_values(tmp_path, args, option_name):
    work = tmp_path / "cwd"
    work.mkdir()

    result = _run_sh(args, cwd=work)

    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    combined = result.stdout + result.stderr
    assert option_name in combined
    assert (
        "missing value" in combined.lower()
        or "empty value" in combined.lower()
    )
    # The malformed value must be rejected before any output path is assembled.
    assert "OUTPUT_DIR=" not in result.stdout
    # No output file/dir may be created in the caller's cwd.
    assert list(work.iterdir()) == []


def test_bash_accepts_negative_seed(tmp_path):
    """A leading single-dash value like -1 must be forwarded, not rejected.

    ``-1`` does not begin with ``--`` so the wrapper must treat it as the value
    of ``--seed`` and hand it to the CLI. Whether the CLI ultimately accepts a
    negative seed is the CLI's concern; the wrapper's job is only to forward it
    (i.e. to reach the CLI rather than fail early with a missing/empty value).
    """
    work = tmp_path / "cwd"
    work.mkdir()
    out_dir = tmp_path / "neg seed out"
    args = [
        "--mock",
        "--seed", "-1",
        "--n-per-cell", "1",
        "--out", str(out_dir),
    ]
    result = _run_sh(args, cwd=work)

    combined = (result.stdout + result.stderr).lower()
    # The wrapper must not reject the negative seed as a missing/empty value.
    assert "missing value for --seed" not in combined
    assert "empty value for --seed" not in combined
    assert "unknown argument" not in combined
    # The wrapper passed its guards and invoked the CLI (it printed OUTPUT_DIR
    # and forwarded the seed). Either the CLI succeeded and wrote 12 records, or
    # the CLI itself rejected the negative seed -- both prove we entered the CLI.
    assert "OUTPUT_DIR=" in result.stdout
    raw = out_dir / "raw_simulated_responses.jsonl"
    if result.returncode == 0:
        assert raw.is_file()
        assert _count_jsonl(raw) == 12
    else:
        # A non-zero exit here must come from the CLI (e.g. numpy seed range),
        # never from the wrapper's argument parser.
        assert "seed" in combined


# --------------------------------------------------------------------------
# FND-008.1: PowerShell empty -OutDir guard
# --------------------------------------------------------------------------


@pytest.mark.parametrize("out_value", ["", "   "])
def test_powershell_rejects_empty_outdir(tmp_path, out_value):
    if _find_powershell() is None:
        pytest.skip("No PowerShell (pwsh/powershell) available on this platform.")
    work = tmp_path / "cwd"
    work.mkdir()

    result = _run_ps1(["-Mock", "-OutDir", out_value], cwd=work)

    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    combined = result.stdout + result.stderr
    assert "OutDir" in combined
    assert "OUTPUT_DIR=" not in result.stdout
    assert list(work.iterdir()) == []
