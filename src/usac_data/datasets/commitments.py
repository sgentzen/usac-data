"""USAC recipient details and commitments dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class RecipientCommitments(DatasetMeta):
    """Recipient-level detail and funding commitments.

    One row per recipient per line item, carrying the recipient entity, the
    chosen category of service, and pre- and post-discount committed amounts.
    This is the dataset to use for "what was actually committed", as opposed to
    :class:`~usac_data.datasets.FRNLineItems` (requested line-item detail) or
    :class:`~usac_data.datasets.Form471` (FRN-level status).

    Dataset: https://opendata.usac.org/resource/avi8-svp9

    .. warning::
       There is no ``total_authorized_disbursement`` column here. The
       post-discount committed amount is
       ``post_discount_extended_eligible_line_item_costs``, and the discount
       percentage is ``dis_pct``, not ``discount_pct_c2``. Reading the wrong
       name yields ``None`` silently rather than an error, because Socrata omits
       absent fields from row JSON instead of rejecting the request. Field names
       below were verified against the live column metadata on 2026-07-25.
    """

    dataset_id = "avi8-svp9"
    name = "Recipient Details and Commitments"
    description = "E-Rate Recipient Details And Commitments"

    # -- Applicant (note: billed_entity_number here, unlike FRNLineItems) --
    billed_entity_number = "billed_entity_number"

    # -- Application keys --
    application_number = "application_number"
    funding_request_number = "funding_request_number"
    form_471_line_item_number = "form_471_line_item_number"
    funding_year = "funding_year"
    is_certified_in_window = "is_certified_in_window"

    # -- Recipient of service --
    ros_entity_number = "ros_entity_number"
    ros_entity_name = "ros_entity_name"
    is_school_library_independent = "is_school_library_independent"

    # -- Classification --
    chosen_category_of_service = "chosen_category_of_service"
    form_471_frn_status_name = "form_471_frn_status_name"
    form_471_status_name = "form_471_status_name"
    form_471_service_type_name = "form_471_service_type_name"
    form_471_function_name = "form_471_function_name"
    form_471_product_name = "form_471_product_name"

    # -- Costs and discount --
    # dis_pct is the discount percentage; there is no discount_pct_c2 column.
    dis_pct = "dis_pct"
    monthly_quantity = "monthly_quantity"
    months_of_service = "months_of_service"
    monthly_recurring_unit_eligible_costs = "monthly_recurring_unit_eligible_costs"
    monthly_recur_ineligible_cost = "monthly_recur_ineligible_cost"
    one_time_eligible_costs = "one_time_eligible_costs"
    one_time_ineligible_cost = "one_time_ineligible_cost"
    total_eligible_one_time_costs = "total_eligible_one_time_costs"
    total_eligible_recurring_costs = "total_eligible_recurring_costs"
    total_monthly_cost = "total_monthly_cost"
    total_monthly_eligible_recurring_costs = "total_monthly_eligible_recurring_costs"
    total_one_time_cost = "total_one_time_cost"
    pre_discount_extended_eligible_line_item_costs = (
        "pre_discount_extended_eligible_line_item_costs"
    )
    # The post-discount committed amount. NOT total_authorized_disbursement.
    post_discount_extended_eligible_line_item_costs = (
        "post_discount_extended_eligible_line_item_costs"
    )
    post_discount_applicant_share = "post_discount_applicant_share"

    @classmethod
    def for_year(cls, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a funding year."""
        return SoQLBuilder().where(funding_year=year)

    @classmethod
    def for_ben(cls, ben: int | str) -> SoQLBuilder:
        """Convenience: query filtered to a billed entity number."""
        return SoQLBuilder().where(billed_entity_number=ben)

    @classmethod
    def for_ben_year(cls, ben: int | str, year: int | str) -> SoQLBuilder:
        """Convenience: query filtered to one applicant in one funding year."""
        return SoQLBuilder().where(billed_entity_number=ben, funding_year=year)

    @classmethod
    def category_two_only(cls) -> SoQLBuilder:
        """Convenience: query filtered to Category 2 line items."""
        return SoQLBuilder().where(chosen_category_of_service="Category2")
