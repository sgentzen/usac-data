"""Tests for dataset definitions."""

from __future__ import annotations

import pytest

from usac_data.datasets import (
    C2BudgetTool,
    Consultants,
    DatasetMeta,
    Disbursements,
    EntityInfo,
    Form470,
    Form471,
    FRNLineItems,
    RecipientCommitments,
)
from usac_data.datasets.form471 import FRNStatus, ServiceType
from usac_data.query import SoQLBuilder


def _in_clause_values(builder: SoQLBuilder) -> list[str]:
    """Pull the quoted values out of a single ``field IN (...)`` $where clause."""
    where = builder.to_params()["$where"]
    inner = where[where.index("(") + 1 : where.rindex(")")]
    return [part.strip().strip("'") for part in inner.split(",")]


class TestDatasetMeta:
    def test_query_returns_builder(self) -> None:
        q = DatasetMeta.query()
        assert q.to_params() == {}


class TestPackageExports:
    def test_dataset_classes_are_importable_from_root(self) -> None:
        import usac_data

        for cls in (Disbursements, Form470):
            assert getattr(usac_data, cls.__name__) is cls
            assert cls.__name__ in usac_data.__all__

    def test_dataset_ids_are_unique(self) -> None:
        # Two classes pointing at one dataset means one of them is querying the
        # wrong grain, which fails silently rather than erroring.
        classes = [
            C2BudgetTool,
            Consultants,
            Disbursements,
            EntityInfo,
            Form470,
            Form471,
            FRNLineItems,
            RecipientCommitments,
        ]
        ids = [c.dataset_id for c in classes]
        assert len(ids) == len(set(ids))


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


class TestForm470:
    def test_dataset_id(self) -> None:
        assert Form470.dataset_id == "jp7a-89nd"

    def test_is_application_grain_not_line_item(self) -> None:
        # jt8s-3q52 is the line-item sibling: one row per service request, so a
        # single form yields many rows. This class is deliberately the
        # application-grain dataset, one row per Form 470.
        assert Form470.dataset_id != "jt8s-3q52"

    def test_applicant_column_is_ben(self) -> None:
        # Matches Form471/FRNLineItems, not RecipientCommitments.
        assert Form470.ben == "ben"
        assert not hasattr(Form470, "billed_entity_number")

    def test_has_no_consultant_column(self) -> None:
        # jp7a-89nd carries no consultant column at all. The sibling jt8s-3q52
        # has consulting_firm_data as a composite string, which silently matches
        # nothing when filtered by CRN. Join through Consultants instead.
        for absent in (
            "consulting_firm_data",
            "consultant_registration_number",
            "consultant_name",
            "crn_data",
        ):
            assert not hasattr(Form470, absent), absent

    def test_for_ben(self) -> None:
        params = Form470.for_ben("143174").to_params()
        assert params["$where"] == "ben='143174'"

    def test_for_year(self) -> None:
        params = Form470.for_year(2025).to_params()
        assert params["$where"] == "funding_year='2025'"

    def test_for_ben_year(self) -> None:
        params = Form470.for_ben_year("143174", 2025).to_params()
        assert "ben='143174'" in params["$where"]
        assert "funding_year='2025'" in params["$where"]

    def test_for_ben_escapes_quotes(self) -> None:
        params = Form470.for_ben("14'3174").to_params()
        assert params["$where"] == "ben='14''3174'"

    def test_lifecycle_field_attributes(self) -> None:
        assert Form470.application_number == "application_number"
        assert Form470.f470_status == "f470_status"
        assert Form470.allowable_contract_date == "allowable_contract_date"
        assert Form470.certified_datetime == "certified_datetime"

    def test_f470_number_is_declared(self) -> None:
        # Socrata type is `url`, so this deserialises as a nested object rather
        # than a string. The docstring records the trap; the field still exists.
        assert Form470.f470_number == "f470_number"

    def test_originals_only(self) -> None:
        # The dataset carries one row per form VERSION, not per form: a form
        # modified after certification has both an Original and a Current row.
        # Filtering to Original is what collapses it to one row per filing.
        params = Form470.originals_only().to_params()
        assert params["$where"] == "form_version='Original'"

    def test_originals_only_composes_with_ben_year(self) -> None:
        params = Form470.for_ben_year(143174, 2025).where(form_version="Original")
        where = params.to_params()["$where"]
        assert "ben='143174'" in where
        assert "funding_year='2025'" in where
        assert "form_version='Original'" in where


class TestDisbursements:
    def test_dataset_id(self) -> None:
        assert Disbursements.dataset_id == "jpiu-tj8h"

    def test_amount_field_is_approved_line_amount(self) -> None:
        # inv_line_item_status is uniformly "SENT TO USAC" and carries no
        # signal, so approved_inv_line_amt is the field that matters.
        assert Disbursements.approved_inv_line_amt == "approved_inv_line_amt"
        assert not hasattr(Disbursements, "total_authorized_disbursement")

    def test_for_frns_returns_one_builder_per_batch(self) -> None:
        frns = [str(n) for n in range(180)]
        batches = Disbursements.for_frns(frns)
        assert len(batches) == 3

    def test_for_frns_default_batch_size_is_80(self) -> None:
        frns = [str(n) for n in range(81)]
        first, second = Disbursements.for_frns(frns)
        assert _in_clause_values(first) == [str(n) for n in range(80)]
        assert _in_clause_values(second) == ["80"]

    def test_for_frns_builds_in_clause(self) -> None:
        params = Disbursements.for_frns(["2199001234", "2199005678"])[0].to_params()
        assert params["$where"] == (
            "funding_request_number IN ('2199001234', '2199005678')"
        )

    def test_for_frns_respects_custom_batch_size(self) -> None:
        batches = Disbursements.for_frns([str(n) for n in range(10)], batch_size=4)
        assert len(batches) == 3

    def test_for_frns_empty_returns_no_batches(self) -> None:
        # An empty IN () clause is a SoQL syntax error, so emit nothing rather
        # than a query guaranteed to 400.
        assert Disbursements.for_frns([]) == []

    def test_for_frns_rejects_non_positive_batch_size(self) -> None:
        for bad in (0, -1):
            with pytest.raises(ValueError):
                Disbursements.for_frns(["123"], batch_size=bad)

    def test_for_frns_escapes_quotes(self) -> None:
        params = Disbursements.for_frns(["21'99"])[0].to_params()
        assert params["$where"] == "funding_request_number IN ('21''99')"
