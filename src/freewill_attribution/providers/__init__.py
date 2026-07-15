"""Provider interfaces (FAST-001).

Only a deterministic mock provider is available this round. No real network
provider is implemented and no API key is read anywhere in this package.
"""

from __future__ import annotations

from .base import Provider, ProviderRequest, ProviderResponse
from .mock import MockProvider

__all__ = ["Provider", "ProviderRequest", "ProviderResponse", "MockProvider"]
