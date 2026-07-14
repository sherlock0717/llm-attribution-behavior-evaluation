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


def _artifact_path(resolved: Path, base_dir: str | Path | None) -> str:
    """Return the stored ArtifactRef path.

    When ``base_dir`` is given the path is stored RELATIVE to the run directory
    (portable, no local absolute path leaks into the manifest). When it is None
    the absolute posix path is stored (legacy behaviour, unit-test helpers).
    """
    if base_dir is None:
        return resolved.as_posix()
    return resolved.resolve().relative_to(Path(base_dir).resolve()).as_posix()


def write_text_artifact(
    path: str | Path, text: str, *, role: str, base_dir: str | Path | None = None
) -> ArtifactRef:
    """Write newline-normalized UTF-8 text and return its ArtifactRef."""
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_newlines(text)
    resolved.write_text(normalized, encoding="utf-8", newline="\n")
    data = resolved.read_bytes()
    return ArtifactRef(
        path=_artifact_path(resolved, base_dir),
        sha256=hash_file(resolved),
        size_bytes=len(data),
        media_type=_media_type_for(resolved),
        role=role,
    )


def write_json_artifact(
    path: str | Path, obj: Any, *, role: str, base_dir: str | Path | None = None
) -> ArtifactRef:
    """Write a pretty JSON artifact (stable key order) and return its ArtifactRef."""
    resolved = Path(path)
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)
    return write_text_artifact(resolved, text + "\n", role=role, base_dir=base_dir)


def write_jsonl_artifact(
    path: str | Path,
    rows: Iterable[dict[str, Any]],
    *,
    role: str,
    base_dir: str | Path | None = None,
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
        path=_artifact_path(resolved, base_dir),
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


def resolve_artifact_path(base_dir: str | Path, rel: str) -> Path:
    """Resolve ``rel`` strictly inside ``base_dir``.

    Only ``base_dir / relative_path`` is allowed. Absolute paths, drive-letter
    paths and ``..`` parent-escapes are rejected with :class:`ValueError`.
    """
    base_resolved = Path(base_dir).resolve()
    p = Path(rel)
    if p.is_absolute() or p.drive or str(rel).startswith(("/", "\\")):
        raise ValueError(f"artifact path must be relative to the run dir, got absolute: {rel}")
    if any(part == ".." for part in p.parts):
        raise ValueError(f"artifact path must not contain a parent escape ('..'): {rel}")
    candidate = (base_resolved / p).resolve()
    if candidate != base_resolved and base_resolved not in candidate.parents:
        raise ValueError(f"artifact path escapes the run dir: {rel}")
    return candidate


def verify_artifacts(artifacts: Iterable[ArtifactRef], base_dir: str | Path) -> list[str]:
    """Re-check each ArtifactRef against the file on disk.

    Every ArtifactRef.path must be a portable, run-dir-relative path (see
    :func:`resolve_artifact_path`). Absolute paths and parent escapes are
    reported as problems. Returns a list of human-readable mismatch
    descriptions (empty when all artifacts resolve, exist and match).
    """
    problems: list[str] = []
    for ref in artifacts:
        try:
            candidate = resolve_artifact_path(base_dir, ref.path)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        if not candidate.exists():
            problems.append(f"missing artifact: {ref.path}")
            continue
        if hash_file(candidate) != ref.sha256:
            problems.append(f"hash mismatch: {ref.path}")
    return problems


__all__ = [
    "write_text_artifact",
    "write_json_artifact",
    "write_jsonl_artifact",
    "read_jsonl",
    "resolve_artifact_path",
    "verify_artifacts",
]
