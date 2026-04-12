"""USAC Form 471 (FCC Form 471) dataset."""

from __future__ import annotations

from enum import StrEnum

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class FRNStatus(StrEnum):
    """Known FRN status values."""

    FUNDED = "Funded"
    PENDING = "Pending"
    DENIED = "Denied"
    CANCELLED = "Cancelled"
    COMMITTED = "Committed"


class ServiceType(StrEnum):
    """Known service type values."""

    INTERNAL_CONNECTIONS = "Internal Connections"
    INTERNET_ACCESS = "Internet Access"
    DATA_TRANSMISSION = "Data Transmission and/or Internet Access"
    VOICE = "Voice"
    BASIC_MAINTENANCE = "Basic Maintenance of Internal Connections"


class Form471(DatasetMeta):
    """Form 471 FRN status dataset.

    Contains FRN-level funding status for all E-Rate applications.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-FRN-Status/qdmp-ygft
    """

    dataset_id = "qdmp-ygft"
    name = "Form 471 FRN Status"
    description = "E-Rate Form 471 FRN-level funding status"

    # -- Known fields (not exhaustive, add as discovered) --
    ben = "ben"
    organization_name = "organization_name"
    state = "state"
    funding_year = "funding_year"
    funding_request_number = "funding_request_number"
    form_471_frn_status_name = "form_471_frn_status_name"
    form_471_service_type_name = "form_471_service_type_name"
    spin_name = "spin_name"
    invoicing_mode = "invoicing_mode"
    funding_commitment_request = "funding_commitment_request"
    total_pre_discount_costs = "total_pre_discount_costs"
    dis_pct = "dis_pct"
    application_number = "application_number"
    fcdl_letter_date = "fcdl_letter_date"

    @classmethod
    def for_year(cls, year: int) -> SoQLBuilder:
        """Convenience: query filtered to a funding year."""
        return SoQLBuilder().where(funding_year=year)

    @classmethod
    def funded_only(cls) -> SoQLBuilder:
        """Convenience: query filtered to funded FRNs."""
        return SoQLBuilder().where(form_471_frn_status_name=FRNStatus.FUNDED)
