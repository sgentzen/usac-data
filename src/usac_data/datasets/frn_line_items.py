"""USAC FRN line items dataset (FCC Form 471 line-item detail)."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class FRNLineItems(DatasetMeta):
    """FRN line-item detail from Form 471 applications.

    One row per line item, carrying product, function, quantity and cost
    detail. Use this rather than :class:`~usac_data.datasets.Form471` when you
    need line-item granularity; ``Form471`` (``qdmp-ygft``) is FRN-level status
    and is a different dataset.

    Dataset: https://opendata.usac.org/resource/hbj5-2bpj

    .. warning::
       This dataset identifies the applicant with ``ben``, **not**
       ``billed_entity_number``. It also has **no** ``chosen_category_of_service``
       column, and no service-provider (``spin_name``/``spin_number``) or
       FRN-status columns. Filtering on any of those returns HTTP 400
       ``query.soql.no-such-column`` rather than an empty result set, so the
       mistake surfaces as a hard failure. Field names below were verified
       against the live column metadata on 2026-07-25.
    """

    dataset_id = "hbj5-2bpj"
    name = "FRN Line Items"
    description = (
        "E-Rate Request for Discount on Services: FRN Line Items "
        "(FCC Form 471 and Related Information)"
    )

    # -- Identity and applicant (note: ben, NOT billed_entity_number) --
    ben = "ben"
    organization_name = "organization_name"
    applicant_type = "applicant_type"
    state = "state"
    cnct_email = "cnct_email"

    # -- Application keys --
    application_number = "application_number"
    funding_request_number = "funding_request_number"
    form_471_line_item_number = "form_471_line_item_number"
    funding_year = "funding_year"
    form_version = "form_version"
    is_certified_in_window = "is_certified_in_window"

    # -- Product and function --
    form_471_function_name = "form_471_function_name"
    form_471_product_name = "form_471_product_name"
    form_471_purpose_name = "form_471_purpose_name"
    form_471_manufacturer_name = "form_471_manufacturer_name"
    form_471_unit_name = "form_471_unit_name"
    model_of_equipment = "model_of_equipment"
    other_manufacturer_desc = "other_manufacturer_desc"
    lease = "lease"

    # -- Connection detail --
    connection_directly_school = "connection_directly_school"
    connection_supports_service = "connection_supports_service"
    connection_used_by = "connection_used_by"
    firewall_indicator = "firewall_indicator"
    download_speed = "download_speed"
    upload_speed = "upload_speed"
    burstable_speed = "burstable_speed"

    # -- Costs --
    price = "price"
    one_time_quantity = "one_time_quantity"
    one_time_eligible_costs = "one_time_eligible_costs"
    one_time_ineligible_cost = "one_time_ineligible_cost"
    total_one_time_cost = "total_one_time_cost"
    total_eligible_one_time_costs = "total_eligible_one_time_costs"
    monthly_quantity = "monthly_quantity"
    months_of_service = "months_of_service"
    monthly_recurring_unit_eligible_costs = "monthly_recurring_unit_eligible_costs"
    monthly_recur_ineligible_cost = "monthly_recur_ineligible_cost"
    total_monthly_cost = "total_monthly_cost"
    total_monthly_eligible_recurring_costs = "total_monthly_eligible_recurring_costs"
    total_eligible_recurring_costs = "total_eligible_recurring_costs"
    pre_discount_extended_eligible_line_item_costs = (
        "pre_discount_extended_eligible_line_item_costs"
    )

    @classmethod
    def for_year(cls, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a funding year."""
        return SoQLBuilder().where(funding_year=year)

    @classmethod
    def for_ben(cls, ben: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a billed entity number.

        Filters on ``ben``, which is this dataset's applicant column.
        """
        return SoQLBuilder().where(ben=ben)

    @classmethod
    def for_ben_year(cls, ben: int | str, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to one applicant in one funding year."""
        return SoQLBuilder().where(ben=ben, funding_year=year)
