"""Unit tests for artifact writers (FAST-001)."""

from __future__ import annotations

from freewill_attribution.benchmark import artifacts


def test_jsonl_artifact_records_count_and_hash(tmp_path):
    rows = [{"a": 1}, {"a": 2}, {"a": 3}]
    ref = artifacts.write_jsonl_artifact(tmp_path / "r.jsonl", rows, role="raw", base_dir=tmp_path)
    assert ref.record_count == 3
    assert ref.size_bytes > 0
    assert len(ref.sha256) == 64
    assert ref.path == "r.jsonl"  # portable, run-dir-relative
    assert artifacts.read_jsonl(tmp_path / "r.jsonl") == rows


def test_text_artifact_normalizes_newlines(tmp_path):
    ref = artifacts.write_text_artifact(
        tmp_path / "t.txt", "a\r\nb\r\n", role="prompt_template", base_dir=tmp_path
    )
    data = (tmp_path / "t.txt").read_bytes()
    assert b"\r" not in data
    assert ref.media_type == "text/plain"


def test_verify_artifacts_detects_tamper(tmp_path):
    ref = artifacts.write_json_artifact(tmp_path / "m.json", {"x": 1}, role="manifest", base_dir=tmp_path)
    assert artifacts.verify_artifacts([ref], tmp_path) == []
    (tmp_path / "m.json").write_text("{\"x\": 2}\n", encoding="utf-8")
    problems = artifacts.verify_artifacts([ref], tmp_path)
    assert problems and "hash mismatch" in problems[0]


def test_resolve_artifact_path_rejects_absolute(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        artifacts.resolve_artifact_path(tmp_path, str((tmp_path / "m.json").resolve()))


def test_resolve_artifact_path_rejects_parent_escape(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        artifacts.resolve_artifact_path(tmp_path, "../evil.json")


def test_resolve_artifact_path_allows_subdir(tmp_path):
    resolved = artifacts.resolve_artifact_path(tmp_path, "figures/x.png")
    assert resolved == (tmp_path / "figures" / "x.png").resolve()
