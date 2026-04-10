"""Tests for USACClient."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from usac_data import SoQLBuilder, USACClient
from usac_data.client import BASE_URL
from usac_data.exceptions import USACRetryError

DATASET_ID = "test-1234"
ENDPOINT = f"{BASE_URL}/{DATASET_ID}.json"


class TestUSACClientSync:
    def test_get_basic(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[{"frn": "1001"}])
        rows = client.get(DATASET_ID, limit=10)
        assert rows == [{"frn": "1001"}]

    def test_get_with_query(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[{"frn": "1001"}])
        query = SoQLBuilder().where(funding_year=2024)
        rows = client.get(DATASET_ID, query=query)
        assert rows == [{"frn": "1001"}]

        request = httpx_mock.get_requests()[0]
        assert "where" in str(request.url)

    def test_get_sends_app_token(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=[])
        client = USACClient(app_token="my-token")
        client.get(DATASET_ID)

        request = httpx_mock.get_requests()[0]
        assert request.headers["X-App-Token"] == "my-token"

    def test_get_no_token(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=[])
        client = USACClient()
        client.get(DATASET_ID)

        request = httpx_mock.get_requests()[0]
        assert "X-App-Token" not in request.headers

    def test_retry_on_server_error(
        self, httpx_mock: HTTPXMock, client: USACClient
    ) -> None:
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(json=[{"ok": True}])

        rows = client.get(DATASET_ID)
        assert rows == [{"ok": True}]
        assert len(httpx_mock.get_requests()) == 2

    def test_no_retry_on_client_error(
        self, httpx_mock: HTTPXMock, client: USACClient
    ) -> None:
        httpx_mock.add_response(status_code=400)

        with pytest.raises(httpx.HTTPStatusError):
            client.get(DATASET_ID)
        assert len(httpx_mock.get_requests()) == 1

    def test_raises_retry_error_after_exhaustion(
        self, httpx_mock: HTTPXMock
    ) -> None:
        client = USACClient(max_retries=2)
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(status_code=500)

        with pytest.raises(USACRetryError) as exc_info:
            client.get(DATASET_ID)
        assert exc_info.value.dataset_id == DATASET_ID
        assert exc_info.value.attempts == 2

    def test_paginate_sync(self, httpx_mock: HTTPXMock) -> None:
        client = USACClient(page_size=2)
        httpx_mock.add_response(json=[{"a": 1}, {"b": 2}])
        httpx_mock.add_response(json=[{"c": 3}])

        all_rows = client.paginate(DATASET_ID)
        assert len(all_rows) == 3
        assert len(httpx_mock.get_requests()) == 2

    def test_paginate_empty(self, httpx_mock: HTTPXMock) -> None:
        client = USACClient(page_size=2)
        httpx_mock.add_response(json=[])

        all_rows = client.paginate(DATASET_ID)
        assert all_rows == []

    def test_count(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[{"count": "42"}])
        result = client.count(DATASET_ID)
        assert result == 42

    def test_count_empty(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[])
        result = client.count(DATASET_ID)
        assert result == 0


class TestUSACClientAsync:
    async def test_aget(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[{"frn": "1001"}])
        rows = await client.aget(DATASET_ID)
        assert rows == [{"frn": "1001"}]

    async def test_apaginate(self, httpx_mock: HTTPXMock) -> None:
        client = USACClient(page_size=2)
        httpx_mock.add_response(json=[{"a": 1}, {"b": 2}])
        httpx_mock.add_response(json=[{"c": 3}])

        batches = []
        async for batch in client.apaginate(DATASET_ID):
            batches.append(batch)
        assert len(batches) == 2
        assert sum(len(b) for b in batches) == 3

    async def test_acount(self, httpx_mock: HTTPXMock, client: USACClient) -> None:
        httpx_mock.add_response(json=[{"count": "10"}])
        result = await client.acount(DATASET_ID)
        assert result == 10

    async def test_async_context_manager(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=[])
        async with USACClient() as client:
            await client.aget(DATASET_ID)


class TestSyncContextManager:
    def test_sync_context_manager(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=[])
        with USACClient() as client:
            client.get(DATASET_ID)


class TestBuildParams:
    def test_defaults(self, client: USACClient) -> None:
        params = client._build_params()
        assert params["$limit"] == "10000"
        assert "$offset" not in params

    def test_with_query(self, client: USACClient) -> None:
        query = SoQLBuilder().where(year=2024)
        params = client._build_params(query=query)
        assert "$where" in params

    def test_with_offset(self, client: USACClient) -> None:
        params = client._build_params(offset=100)
        assert params["$offset"] == "100"

    def test_custom_limit(self, client: USACClient) -> None:
        params = client._build_params(limit=50)
        assert params["$limit"] == "50"
