"""Shared test fixtures."""

from __future__ import annotations

import pytest

from usac_data import USACClient


@pytest.fixture
def client() -> USACClient:
    """USACClient with default settings for testing."""
    return USACClient(app_token="test-key-placeholder")
