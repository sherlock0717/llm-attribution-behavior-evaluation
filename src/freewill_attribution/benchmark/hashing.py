"""Canonical serialization and SHA-256 hashing for benchmark artifacts (FAST-001).

Canonical serialization rules (must match BENCHMARK_SPEC.md / METRIC_SPEC.md):

- UTF-8 encoding.
- Stable key ordering (``sort_keys=True``).
- Normalized newline (LF only) for text payloads.
- SHA-256 over the normalized bytes.

This module performs no network I/O and never reads API keys. It only hashes
in-memory objects, strings and existing files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def normalize_newlines(text: str) -> str:
    """Normalize CRLF / CR to a single LF so hashes are platform-stable."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def canonical_json(obj: Any) -> str:
    """Serialize ``obj`` to a canonical JSON string.

    Uses stable key ordering, no ASCII escaping (UTF-8 friendly), and compact
    separators. The result is deterministic for equal inputs regardless of the
    original mapping insertion order.
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(obj: Any) -> bytes:
    """Return the canonical UTF-8 bytes for ``obj`` (newline-normalized)."""
    return normalize_newlines(canonical_json(obj)).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_object(obj: Any) -> str:
    """SHA-256 of the canonical serialization of ``obj``."""
    return sha256_hex(canonical_bytes(obj))


def hash_text(text: str) -> str:
    """SHA-256 of newline-normalized UTF-8 text."""
    return sha256_hex(normalize_newlines(text).encode("utf-8"))


def hash_file(path: str | Path) -> str:
    """SHA-256 of a file's raw bytes (streamed, no full read into one buffer)."""
    resolved = Path(path)
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "normalize_newlines",
    "canonical_json",
    "canonical_bytes",
    "sha256_hex",
    "hash_object",
    "hash_text",
    "hash_file",
]
