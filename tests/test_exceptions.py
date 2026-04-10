"""Tests for custom exceptions."""

from __future__ import annotations

from usac_data.exceptions import USACError, USACRetryError


def test_retry_error_message() -> None:
    exc = USACRetryError("abcd-1234", 3)
    assert "abcd-1234" in str(exc)
    assert "3" in str(exc)
    assert exc.dataset_id == "abcd-1234"
    assert exc.attempts == 3


def test_retry_error_is_usac_error() -> None:
    assert issubclass(USACRetryError, USACError)
