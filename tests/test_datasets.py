"""Tests for dataset definitions."""

from __future__ import annotations

import pytest

from usac_data.datasets import C2BudgetTool, Consultants, DatasetMeta, EntityInfo, Form471
from usac_data.datasets.form471 import FRNStatus, ServiceType


class TestDatasetMeta:
    def test_query_returns_builder(self) -> None:
        q = DatasetMeta.query()
        assert q.to_params() == {}


class TestForm471:
    def test_dataset_id(self) -> None:
        assert Form471.dataset_id == "qdmp-ygft"

    def test_for_year(self) -> None:
        params = Form471.for_year(2024).to_params()
        assert params["$where"] == "funding_year='2024'"

    def test_funded_only(self) -> None:
        params = Form471.funded_only().to_params()
        assert "Funded" in params["$where"]
        assert "form_471_frn_status_name" in params["$where"]

    def test_field_attributes(self) -> None:
        assert Form471.ben == "ben"
        assert Form471.organization_name == "organization_name"
        assert Form471.funding_request_number == "funding_request_number"

    def test_frn_status_enum(self) -> None:
        assert FRNStatus.FUNDED == "Funded"
        assert FRNStatus.DENIED == "Denied"

    def test_service_type_enum(self) -> None:
        assert ServiceType.INTERNET_ACCESS == "Internet Access"
        assert ServiceType.INTERNAL_CONNECTIONS == "Internal Connections"


class TestC2BudgetTool:
    def test_dataset_id(self) -> None:
        assert C2BudgetTool.dataset_id == "6brt-5pbv"

    def test_with_remaining(self) -> None:
        params = C2BudgetTool.with_remaining(5000).to_params()
        assert "available_c2_budget_amount > 5000" in params["$where"]

    def test_with_remaining_default(self) -> None:
        params = C2BudgetTool.with_remaining().to_params()
        assert "available_c2_budget_amount > 0" in params["$where"]

    def test_with_remaining_rejects_string(self) -> None:
        with pytest.raises(TypeError, match="must be a number"):
            C2BudgetTool.with_remaining("0 OR 1=1")  # type: ignore[arg-type]


class TestConsultants:
    def test_dataset_id(self) -> None:
        assert Consultants.dataset_id == "x5px-esft"

    def test_for_consultant(self) -> None:
        params = Consultants.for_consultant("Acme").to_params()
        assert "LIKE" in params["$where"]
        assert "%Acme%" in params["$where"]
        assert "cnslt_name" in params["$where"]


class TestEntityInfo:
    def test_dataset_id(self) -> None:
        assert EntityInfo.dataset_id == "7i5i-83qf"

    def test_in_state(self) -> None:
        params = EntityInfo.in_state("va").to_params()
        assert "VA" in params["$where"]
        assert "physical_state" in params["$where"]
