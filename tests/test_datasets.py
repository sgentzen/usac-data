"""Tests for dataset definitions."""

from __future__ import annotations

import pytest

from usac_data.datasets import (
    C2BudgetTool,
    Consultants,
    DatasetMeta,
    EntityInfo,
    Form471,
    FRNLineItems,
    RecipientCommitments,
)
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

    def test_with_remaining_rejects_injection(self) -> None:
        # min_remaining is interpolated raw into the SoQL WHERE clause (Socrata
        # has no bind params), so a non-numeric argument must be rejected rather
        # than smuggled into the query.
        with pytest.raises(ValueError):
            C2BudgetTool.with_remaining("0 OR 1=1")  # type: ignore[arg-type]

    def test_with_remaining_rejects_non_finite(self) -> None:
        # nan/inf coerce fine but yield an always-false comparison and silently
        # empty results, so reject them rather than build a misleading query.
        for bad in ("nan", "inf", float("nan"), float("inf")):
            with pytest.raises(ValueError):
                C2BudgetTool.with_remaining(bad)  # type: ignore[arg-type]


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


class TestFRNLineItems:
    def test_dataset_id(self) -> None:
        assert FRNLineItems.dataset_id == "hbj5-2bpj"

    def test_is_not_form471(self) -> None:
        # These are different datasets at different granularities. Conflating
        # them queries the wrong data, so pin that they never converge.
        assert FRNLineItems.dataset_id != Form471.dataset_id

    def test_applicant_column_is_ben(self) -> None:
        # This dataset has no billed_entity_number column; filtering on it
        # returns HTTP 400 no-such-column rather than an empty result.
        assert FRNLineItems.ben == "ben"
        assert not hasattr(FRNLineItems, "billed_entity_number")

    def test_has_no_service_provider_or_status_fields(self) -> None:
        # Absent upstream. Guards against re-adding them from a sibling dataset.
        for absent in (
            "billed_entity_number",
            "chosen_category_of_service",
            "spin_name",
            "spin_number",
            "form_471_frn_status_name",
            "org_state",
        ):
            assert not hasattr(FRNLineItems, absent), absent

    def test_for_ben(self) -> None:
        params = FRNLineItems.for_ben("123456").to_params()
        assert params["$where"] == "ben='123456'"

    def test_for_ben_year(self) -> None:
        params = FRNLineItems.for_ben_year("123456", 2024).to_params()
        assert "ben='123456'" in params["$where"]
        assert "funding_year='2024'" in params["$where"]

    def test_for_ben_escapes_quotes(self) -> None:
        params = FRNLineItems.for_ben("12'3456").to_params()
        assert params["$where"] == "ben='12''3456'"


class TestRecipientCommitments:
    def test_dataset_id(self) -> None:
        assert RecipientCommitments.dataset_id == "avi8-svp9"

    def test_applicant_column_is_billed_entity_number(self) -> None:
        # Opposite convention to FRNLineItems, which uses ben.
        assert RecipientCommitments.billed_entity_number == "billed_entity_number"
        assert not hasattr(RecipientCommitments, "ben")

    def test_post_discount_amount_field_name(self) -> None:
        # There is no total_authorized_disbursement column here; reading it
        # yields None silently because Socrata omits absent fields from rows.
        assert (
            RecipientCommitments.post_discount_extended_eligible_line_item_costs
            == "post_discount_extended_eligible_line_item_costs"
        )
        assert not hasattr(RecipientCommitments, "total_authorized_disbursement")

    def test_discount_pct_field_name(self) -> None:
        assert RecipientCommitments.dis_pct == "dis_pct"
        assert not hasattr(RecipientCommitments, "discount_pct_c2")

    def test_for_ben_year(self) -> None:
        params = RecipientCommitments.for_ben_year("123456", "2024").to_params()
        assert "billed_entity_number='123456'" in params["$where"]
        assert "funding_year='2024'" in params["$where"]

    def test_category_two_only(self) -> None:
        params = RecipientCommitments.category_two_only().to_params()
        assert params["$where"] == "chosen_category_of_service='Category2'"
