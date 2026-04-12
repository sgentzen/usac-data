"""USAC Consultants dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class Consultants(DatasetMeta):
    """Consultant associations on Form 471 filings.

    Maps consultants to the applications and entities they assist.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Form-471-Consultants/x5px-esft

    Note: This dataset has NO ``ben``/``entity_number`` column. The entity
    is identified by ``epc_organization_id``. Use ``organization_name``
    for cross-dataset matching.
    """

    dataset_id = "x5px-esft"
    name = "Form 471 Consultants"
    description = "Consultant associations on Form 471 filings"

    # -- Known fields --
    epc_organization_id = "epc_organization_id"
    organization_name = "organization_name"
    funding_year = "funding_year"
    cnslt_name = "cnslt_name"
    cnslt_epc_organization_id = "cnslt_epc_organization_id"

    @classmethod
    def for_consultant(cls, name: str) -> SoQLBuilder:
        """Query applications associated with a consultant (partial match)."""
        return SoQLBuilder().where_like("cnslt_name", f"%{name}%")
