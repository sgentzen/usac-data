"""USAC Form 471 (FCC Form 471) dataset."""

from __future__ import annotations

from enum import StrEnum

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class FRNStatus(StrEnum):
    """Known FRN line item statuses."""

    FUNDED = "Funded"
    PENDING = "Pending"
    DENIED = "Denied"
    CANCELLED = "Cancelled"
    COMMITTED = "Committed"


class Category(StrEnum):
    C1 = "Category 1"
    C2 = "Category 2"


class Form471(DatasetMeta):
    """Form 471 line item dataset.

    Contains FRN-level detail for all E-Rate applications.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-FCC-Form-471-Line-Items/avi8-svp9
    """

    dataset_id = "avi8-svp9"
    name = "Form 471"
    description = "E-Rate Form 471 FRN line items"

    # -- Known fields (not exhaustive, add as discovered) --
    application_number = "application_number"
    frn = "frn"
    frn_status = "frn_status"
    funding_year = "funding_year"
    category_of_service = "category_of_service"
    entity_name = "entity_name"
    entity_number = "entity_number"
    service_type = "service_type"
    total_monthly_cost = "total_monthly_cost"
    total_eligible_recurring_costs = "total_eligible_recurring_costs"
    total_eligible_one_time_costs = "total_eligible_one_time_costs"
    total_authorized_disbursement = "total_authorized_disbursement"
    consultant_name = "consultant_name"
    establishing_fcc_form470 = "establishing_fcc_form470"
    award_date = "award_date"
    expiration_date = "expiration_date"
    narrative = "narrative"

    @classmethod
    def for_year(cls, year: int) -> SoQLBuilder:
        """Convenience: query filtered to a funding year."""
        return SoQLBuilder().where(funding_year=year)

    @classmethod
    def funded_only(cls) -> SoQLBuilder:
        """Convenience: query filtered to funded FRNs."""
        return SoQLBuilder().where(frn_status=FRNStatus.FUNDED)
