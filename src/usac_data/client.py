"""Low-level SODA API transport with pagination, retries, and rate limiting."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from usac_data.exceptions import USACRetryError
from usac_data.query import SoQLBuilder

logger = logging.getLogger(__name__)

USAC_DOMAIN = "opendata.usac.org"
BASE_URL = f"https://{USAC_DOMAIN}/resource"

DEFAULT_PAGE_SIZE = 10_000
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, doubles each retry
DEFAULT_TIMEOUT = 30.0


class USACClient:
    """Client for querying USAC Open Data via the Socrata SODA API.

    Supports both sync and async usage. Handles automatic pagination,
    retries with exponential backoff, and optional app token auth.

    Examples:
        Sync usage::

            client = USACClient(app_token="your-token")
            rows = client.get("abcd-1234", limit=100)

        Async usage::

            async with USACClient(app_token="your-token") as client:
                rows = await client.aget("abcd-1234", limit=100)

        With query builder::

            from usac_data import Form471
            query = Form471.query().where(funding_year=2024).select("frn", "entity_name")
            rows = client.get(Form471.dataset_id, query=query)

        Paginated iteration::

            async for batch in client.apaginate("abcd-1234"):
                process(batch)
    """

    def __init__(
        self,
        app_token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.page_size = page_size
        self.max_retries = max_retries

        headers: dict[str, str] = {"Accept": "application/json"}
        if app_token:
            headers["X-App-Token"] = app_token

        self._sync_client = httpx.Client(
            base_url=BASE_URL,
            headers=headers,
            timeout=timeout,
        )
        self._async_client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=headers,
            timeout=timeout,
        )

    # -- Lifecycle --

    def __enter__(self) -> USACClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> USACClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._async_client.aclose()

    def close(self) -> None:
        self._sync_client.close()

    # -- Core fetch with retries --

    def _build_params(
        self,
        query: SoQLBuilder | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, str]:
        params = query.to_params() if query else {}

        params["$limit"] = str(limit or self.page_size)
        if offset:
            params["$offset"] = str(offset)
        return params

    def _fetch_sync(
        self,
        dataset_id: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._sync_client.get(f"/{dataset_id}.json", params=params)
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                wait = RETRY_BACKOFF * (2**attempt)
                logger.warning(
                    "Retry %d/%d for %s (wait %.1fs): %s",
                    attempt + 1,
                    self.max_retries,
                    dataset_id,
                    wait,
                    exc,
                )
                time.sleep(wait)
        raise USACRetryError(dataset_id, self.max_retries) from last_exc

    async def _fetch_async(
        self,
        dataset_id: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = await self._async_client.get(f"/{dataset_id}.json", params=params)
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                wait = RETRY_BACKOFF * (2**attempt)
                logger.warning(
                    "Retry %d/%d for %s (wait %.1fs): %s",
                    attempt + 1,
                    self.max_retries,
                    dataset_id,
                    wait,
                    exc,
                )
                await asyncio.sleep(wait)
        raise USACRetryError(dataset_id, self.max_retries) from last_exc

    # -- Public API --

    def get(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch rows from a USAC dataset (sync).

        Args:
            dataset_id: Socrata 4x4 dataset identifier (e.g. "abcd-1234").
            query: Optional SoQL query builder.
            limit: Max rows to return. Defaults to page_size.
            offset: Row offset for manual pagination.

        Returns:
            List of row dicts.
        """
        params = self._build_params(query, limit, offset)
        return self._fetch_sync(dataset_id, params)

    async def aget(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch rows from a USAC dataset (async). See get() for args."""
        params = self._build_params(query, limit, offset)
        return await self._fetch_async(dataset_id, params)

    async def apaginate(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Async generator that auto-paginates through all results.

        Yields batches of rows (page_size each) until exhausted.
        """
        offset = 0
        while True:
            params = self._build_params(query, limit=self.page_size, offset=offset)
            batch = await self._fetch_async(dataset_id, params)
            if not batch:
                break
            yield batch
            if len(batch) < self.page_size:
                break
            offset += self.page_size

    def paginate(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
    ) -> list[dict[str, Any]]:
        """Sync fetch of ALL rows, auto-paginating. Returns complete list.

        Warning: large datasets may use significant memory.
        """
        all_rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            params = self._build_params(query, limit=self.page_size, offset=offset)
            batch = self._fetch_sync(dataset_id, params)
            if not batch:
                break
            all_rows.extend(batch)
            if len(batch) < self.page_size:
                break
            offset += self.page_size
        return all_rows

    def count(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
    ) -> int:
        """Return total row count for a dataset/query (sync)."""
        q = (query.copy() if query else SoQLBuilder()).select("count(*) as count")
        result = self._fetch_sync(dataset_id, q.to_params())
        return int(result[0]["count"]) if result else 0

    async def acount(
        self,
        dataset_id: str,
        query: SoQLBuilder | None = None,
    ) -> int:
        """Return total row count for a dataset/query (async)."""
        q = (query.copy() if query else SoQLBuilder()).select("count(*) as count")
        result = await self._fetch_async(dataset_id, q.to_params())
        return int(result[0]["count"]) if result else 0
