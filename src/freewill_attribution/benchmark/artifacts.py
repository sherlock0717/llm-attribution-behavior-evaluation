"""Artifact writing helpers for benchmark runs (FAST-001).

All run artifacts are written under ``artifacts/runs/<run_id>/`` (Git ignored).
Historical ``outputs/`` is never written here. Every artifact gets an
:class:`ArtifactRef` with a SHA-256 and byte size so the manifest can be
re-verified against the files on disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .hashing import hash_file, normalize_newlines
from .models import ArtifactRef

_MEDIA_TYPES = {
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".png": "image/png",
}


def _media_type_for(path: Path) -> str:
    return _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")


def write_text_artifact(path: str | Path, text: str, *, role: str) -> ArtifactRef:
    """Write newline-normalized UTF-8 text and return its ArtifactRef."""
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_newlines(text)
    resolved.write_text(normalized, encoding="utf-8", newline="\n")
    data = resolved.read_bytes()
    return ArtifactRef(
        path=resolved.as_posix(),
        sha256=hash_file(resolved),
        size_bytes=len(data),
        media_type=_media_type_for(resolved),
        role=role,
    )


def write_json_artifact(path: str | Path, obj: Any, *, role: str) -> ArtifactRef:
    """Write a pretty JSON artifact (stable key order) and return its ArtifactRef."""
    resolved = Path(path)
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)
    return write_text_artifact(resolved, text + "\n", role=role)


def write_jsonl_artifact(
    path: str | Path, rows: Iterable[dict[str, Any]], *, role: str
) -> ArtifactRef:
    """Write a JSONL artifact and return its ArtifactRef (with record_count)."""
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    lines: list[str] = []
    for row in rows:
        lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
        count += 1
    text = ("\n".join(lines) + "\n") if lines else ""
    resolved.write_text(text, encoding="utf-8", newline="\n")
    data = resolved.read_bytes()
    return ArtifactRef(
        path=resolved.as_posix(),
        sha256=hash_file(resolved),
        size_bytes=len(data),
        media_type=_media_type_for(resolved),
        record_count=count,
        role=role,
    )


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in resolved.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def verify_artifacts(artifacts: Iterable[ArtifactRef], base_dir: str | Path) -> list[str]:
    """Re-check each ArtifactRef against the file on disk.

    Returns a list of human-readable mismatch descriptions (empty when all
    artifacts match their recorded hash and size).
    """
    base = Path(base_dir)
    problems: list[str] = []
    for ref in artifacts:
        candidate = Path(ref.path)
        if not candidate.is_absolute():
            candidate = base / Path(ref.path).name
        if not candidate.exists():
            problems.append(f"missing artifact: {ref.path}")
            continue
        actual = hash_file(candidate)
        if actual != ref.sha256:
            problems.append(f"hash mismatch: {ref.path}")
    return problems


__all__ = [
    "write_text_artifact",
    "write_json_artifact",
    "write_jsonl_artifact",
    "read_jsonl",
    "verify_artifacts",
]
