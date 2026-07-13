"""Unit tests for the minimal freewill_attribution package (FND-005)."""

from __future__ import annotations

import subprocess
import sys

import pytest

import freewill_attribution
from freewill_attribution import paths, runner


def test_import_has_no_side_effects(tmp_path):
    # Importing the package in a fresh working directory must not create files.
    work = tmp_path / "cwd"
    work.mkdir()
    result = subprocess.run(
        [sys.executable, "-c", "import freewill_attribution"],
        cwd=str(work),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(work.iterdir()) == []


def test_package_version_is_readable():
    assert isinstance(freewill_attribution.__version__, str)
    assert freewill_attribution.__version__.strip() != ""


def test_path_relationships():
    assert paths.PACKAGE_DIR.name == "freewill_attribution"
    assert paths.SOURCE_DIR == paths.PACKAGE_DIR.parent
    assert paths.SOURCE_DIR.name == "src"
    assert paths.PROJECT_ROOT == paths.SOURCE_DIR.parent
    assert paths.LEGACY_RUN_SCRIPT == paths.SOURCE_DIR / "run_simulated_study.py"


def test_legacy_run_script_exists():
    script = paths.get_legacy_run_script()
    assert script.is_file()
    assert script.name == "run_simulated_study.py"
    assert script.is_absolute()


def test_build_command_uses_sys_executable(tmp_path):
    cmd = runner.build_legacy_run_command(output_dir=tmp_path / "run")
    assert cmd[0] == sys.executable
    assert cmd[1] == str(paths.get_legacy_run_script())


def test_numeric_params_are_forwarded(tmp_path):
    out = tmp_path / "run"
    cmd = runner.build_legacy_run_command(
        output_dir=out, n_per_cell=3, seed=7, temperature=0.5
    )
    assert cmd[cmd.index("--out") + 1] == str(out)
    assert cmd[cmd.index("--n-per-cell") + 1] == "3"
    assert cmd[cmd.index("--seed") + 1] == "7"
    assert cmd[cmd.index("--temperature") + 1] == "0.5"


def test_mock_and_fresh_flags_present_when_true(tmp_path):
    cmd = runner.build_legacy_run_command(
        output_dir=tmp_path / "run", mock=True, fresh=True
    )
    assert "--mock" in cmd
    assert "--fresh" in cmd


def test_mock_and_fresh_flags_absent_when_false(tmp_path):
    cmd = runner.build_legacy_run_command(
        output_dir=tmp_path / "run", mock=False, fresh=False
    )
    assert "--mock" not in cmd
    assert "--fresh" not in cmd


def test_command_is_list_not_shell_string(tmp_path):
    cmd = runner.build_legacy_run_command(output_dir=tmp_path / "run")
    assert isinstance(cmd, list)
    assert all(isinstance(part, str) for part in cmd)


def test_build_parser_has_run_subcommand():
    from freewill_attribution import cli

    parser = cli.build_parser()
    args = parser.parse_args(["run", "--mock", "--out", "somewhere"])
    assert args.command == "run"
    assert args.out == "somewhere"
    assert args.n_per_cell == 20
    assert args.seed == 20260425
    assert args.temperature == 1.0
    assert args.mock is True
    assert args.fresh is False


def test_run_without_out_exits_nonzero():
    from freewill_attribution import cli

    parser = cli.build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["run", "--mock"])
    assert excinfo.value.code != 0


def test_run_requires_explicit_mock_flag():
    from freewill_attribution import cli

    parser = cli.build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["run", "--out", "somewhere"])
    assert excinfo.value.code != 0


def test_missing_mock_does_not_reach_runner(monkeypatch):
    from freewill_attribution import cli

    calls = []

    def _fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("run_legacy_study must not be called without --mock")

    monkeypatch.setattr(cli.runner, "run_legacy_study", _fail)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--out", "somewhere"])
    assert excinfo.value.code != 0
    assert calls == []
