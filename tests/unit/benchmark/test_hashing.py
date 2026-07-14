"""Unit tests for canonical serialization + hashing (FAST-001)."""

from __future__ import annotations

from freewill_attribution.benchmark import hashing


def test_canonical_json_is_key_order_stable():
    a = {"b": 1, "a": 2, "c": {"y": 1, "x": 2}}
    b = {"a": 2, "c": {"x": 2, "y": 1}, "b": 1}
    assert hashing.canonical_json(a) == hashing.canonical_json(b)
    assert hashing.hash_object(a) == hashing.hash_object(b)


def test_newline_normalization():
    assert hashing.normalize_newlines("a\r\nb\rc") == "a\nb\nc"
    assert hashing.hash_text("a\r\nb") == hashing.hash_text("a\nb")


def test_hash_is_sha256_hex_length():
    digest = hashing.hash_object({"k": "v"})
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_file_matches_bytes(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello world")
    import hashlib

    assert hashing.hash_file(p) == hashlib.sha256(b"hello world").hexdigest()
