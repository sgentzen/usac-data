"""Custom exceptions for usac-data."""

from __future__ import annotations


class USACError(Exception):
    """Base exception for usac-data."""


class USACRetryError(USACError):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, dataset_id: str, attempts: int) -> None:
        self.dataset_id = dataset_id
        self.attempts = attempts
        super().__init__(
            f"Request to dataset '{dataset_id}' failed after {attempts} retries"
        )
