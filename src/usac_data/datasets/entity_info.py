"""USAC Entity Information dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class EntityInfo(DatasetMeta):
    """School and library entity demographics dataset.

    Contains entity details including location, type, and discount rate.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Entity-Information/hbj5-2bpj
    """

    dataset_id = "hbj5-2bpj"
    name = "Entity Information"
    description = "School/library demographics and details"

    # -- Known fields --
    entity_number = "entity_number"
    entity_name = "entity_name"
    entity_type = "entity_type"
    state = "state"
    city = "city"
    zip_code = "zip_code"
    county = "county"
    discount_rate = "discount_rate"
    urban_rural_status = "urban_rural_status"
    total_enrollment = "total_enrollment"
    nslp_eligible = "nslp_eligible"

    @classmethod
    def in_state(cls, state: str) -> SoQLBuilder:
        """Query entities in a given state."""
        return SoQLBuilder().where_raw(
            f"upper(state)='{state.upper().replace(chr(39), chr(39)*2)}'"
        )
