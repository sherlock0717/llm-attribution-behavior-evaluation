"""Offline tests for the DeepSeek provider adapter (REAL-SETUP-001).

These tests NEVER touch the network and NEVER read a real API key. Sockets are
disabled to prove no accidental connection is attempted. Only a FakeDeepSeekClient
is injected.
"""

from __future__ import annotations

import socket

import pytest
import yaml

from freewill_attribution.benchmark import registry
from freewill_attribution.providers import deepseek
from freewill_attribution.providers.base import ProviderErrorCategory


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def _blocked(*args, **kwargs):  # pragma: no cover - only fires on violation
        raise AssertionError("network access attempted in an offline test")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def _example_config():
    return yaml.safe_load(registry.MODEL_DEEPSEEK_EXAMPLE_YAML.read_text(encoding="utf-8"))


class FakeDeepSeekClient:
    """A fake client. Records calls; never connects anywhere."""

    def __init__(self, response=None, error=None, fail_times=0):
        self.response = response
        self.error = error
        self.fail_times = fail_times
        self.calls = 0
        self.seen_api_key = None

    def complete(self, request, *, api_key, base_url, timeout_seconds):
        self.calls += 1
        self.seen_api_key = api_key
        if self.error is not None and self.calls <= self.fail_times:
            raise self.error
        if self.response is not None:
            return self.response
        return deepseek.DeepSeekProviderResponse(
            text='{"items": []}',
            model_id="fake-model",
            request_id="fake-request-id",
            finish_reason="stop",
            latency_ms=None,
        )


def test_provider_init_does_not_touch_network():
    # Constructing the provider must not connect (fixture would fail if it did).
    provider = deepseek.DeepSeekProvider(FakeDeepSeekClient(), _example_config())
    assert provider.provider_name == "deepseek"


def test_example_config_has_no_key_and_blocks_live_by_default():
    cfg = _example_config()
    blob = yaml.safe_dump(cfg)
    assert "DEEPSEEK_API_KEY" in blob  # only the env-var NAME, not a value
    assert "sk-" not in blob
    assert cfg["enabled"] is False
    assert cfg["live_api_allowed"] is False
    assert cfg["credential"]["value_stored_in_config"] is False


def test_live_blocked_when_missing_model_id():
    cfg = _example_config()
    cfg.update(enabled=True, live_api_allowed=True, base_url="https://example.invalid")
    cfg["pricing_snapshot"] = {"status": "verified", "input_cache_hit": 0.1,
                               "input_cache_miss": 0.2, "output": 0.3, "unit_tokens": 1000000}
    blockers = deepseek.live_run_blockers(cfg, real_api=True, confirm_paid_run=True)
    assert any("model_id" in b for b in blockers)


def test_live_blocked_when_missing_base_url():
    cfg = _example_config()
    cfg.update(enabled=True, live_api_allowed=True, model_id="x")
    cfg["pricing_snapshot"] = {"status": "verified", "input_cache_hit": 0.1,
                               "input_cache_miss": 0.2, "output": 0.3, "unit_tokens": 1000000}
    blockers = deepseek.live_run_blockers(cfg, real_api=True, confirm_paid_run=True)
    assert any("base_url" in b for b in blockers)


def test_live_blocked_when_pricing_unverified():
    cfg = _example_config()
    cfg.update(enabled=True, live_api_allowed=True, base_url="https://x", model_id="x")
    blockers = deepseek.live_run_blockers(cfg, real_api=True, confirm_paid_run=True)
    assert any("pricing" in b for b in blockers)


def test_live_blocked_without_real_api_flag():
    cfg = _example_config()
    blockers = deepseek.live_run_blockers(cfg, real_api=False, confirm_paid_run=True)
    assert any("--real-api" in b for b in blockers)


def test_live_blocked_without_confirm_paid_run_flag():
    cfg = _example_config()
    blockers = deepseek.live_run_blockers(cfg, real_api=True, confirm_paid_run=False)
    assert any("--confirm-paid-run" in b for b in blockers)


def test_generate_refuses_before_reading_key():
    # Even with a fake client, generate() must refuse (gate) and never read key.
    provider = deepseek.DeepSeekProvider(FakeDeepSeekClient(), _example_config())
    with pytest.raises(deepseek.DeepSeekError):
        provider.generate(
            deepseek.DeepSeekRequest(prompt="p", model_id="x"),
            real_api=True, confirm_paid_run=True,  # config still disabled
        )


def test_status_classification_maps_correctly():
    assert deepseek.classify_status(401) == ProviderErrorCategory.AUTH_FAILURE
    assert deepseek.classify_status(402) == ProviderErrorCategory.BUDGET_OR_BALANCE_FAILURE
    assert deepseek.classify_status(429) == ProviderErrorCategory.RATE_LIMITED
    assert deepseek.classify_status(500) == ProviderErrorCategory.PROVIDER_UNAVAILABLE
    assert deepseek.classify_status(503) == ProviderErrorCategory.PROVIDER_UNAVAILABLE
    assert deepseek.classify_status(400) == ProviderErrorCategory.REQUEST_INVALID


def test_retry_on_retryable_then_success_via_fake_client():
    # A fully-enabled fake config so the gate passes; client injected (no net).
    cfg = _example_config()
    cfg.update(enabled=True, live_api_allowed=True, base_url="https://x", model_id="fake-model",
               provider_retry_attempts=3)
    cfg["pricing_snapshot"] = {"status": "verified", "input_cache_hit": 0.1,
                               "input_cache_miss": 0.2, "output": 0.3, "unit_tokens": 1000000}
    retryable = deepseek.DeepSeekError("boom", category=ProviderErrorCategory.RATE_LIMITED)
    client = FakeDeepSeekClient(error=retryable, fail_times=2)
    provider = deepseek.DeepSeekProvider(client, cfg)
    resp = provider.generate(
        deepseek.DeepSeekRequest(prompt="p", model_id="fake-model"),
        real_api=True, confirm_paid_run=True, api_key="test-only-fake-key", max_attempts=3,
    )
    assert client.calls == 3
    assert resp.text == '{"items": []}'


def test_non_retryable_error_not_retried():
    cfg = _example_config()
    cfg.update(enabled=True, live_api_allowed=True, base_url="https://x", model_id="fake-model")
    cfg["pricing_snapshot"] = {"status": "verified", "input_cache_hit": 0.1,
                               "input_cache_miss": 0.2, "output": 0.3, "unit_tokens": 1000000}
    fatal = deepseek.DeepSeekError("auth", category=ProviderErrorCategory.AUTH_FAILURE)
    client = FakeDeepSeekClient(error=fatal, fail_times=5)
    provider = deepseek.DeepSeekProvider(client, cfg)
    with pytest.raises(deepseek.DeepSeekError):
        provider.generate(
            deepseek.DeepSeekRequest(prompt="p", model_id="fake-model"),
            real_api=True, confirm_paid_run=True, api_key="test-only-fake-key",
        )
    assert client.calls == 1


def test_key_not_in_error_message():
    provider = deepseek.DeepSeekProvider(FakeDeepSeekClient(), _example_config())
    try:
        provider.load_api_key(env={})  # empty env -> AUTH_FAILURE, no value leaked
    except deepseek.DeepSeekError as exc:
        assert "sk-" not in str(exc)
