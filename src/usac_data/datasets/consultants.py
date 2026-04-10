"""USAC Consultants dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class Consultants(DatasetMeta):
    """Consultant associations per E-Rate application.

    Maps consultants to the applications and entities they assist.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Consultants/wbx6-kdai
    """

    dataset_id = "wbx6-kdai"
    name = "Consultants"
    description = "Consultant associations per application"

    # -- Known fields --
    consultant_name = "consultant_name"
    consultant_registration_number = "consultant_registration_number"
    application_number = "application_number"
    entity_number = "entity_number"
    entity_name = "entity_name"
    funding_year = "funding_year"
    state = "state"

    @classmethod
    def for_consultant(cls, name: str) -> SoQLBuilder:
        """Query applications associated with a consultant (partial match)."""
        return SoQLBuilder().where_like("consultant_name", f"%{name}%")
