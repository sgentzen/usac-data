"""USAC Entity Information dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder, _escape_soql_literal


class EntityInfo(DatasetMeta):
    """School and library entity demographics dataset.

    Contains entity details including location, type, and discount rate.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Entity-Information/7i5i-83qf
    """

    dataset_id = "7i5i-83qf"
    name = "Entity Information"
    description = "School/library demographics and details"

    # -- Known fields --
    entity_number = "entity_number"
    entity_name = "entity_name"
    entity_type = "entity_type"
    parent_entity_number = "parent_entity_number"
    parent_entity_name = "parent_entity_name"
    physical_address = "physical_address"
    physical_city = "physical_city"
    physical_state = "physical_state"
    physical_zipcode = "physical_zipcode"
    physical_county = "physical_county"
    phone_number = "phone_number"
    website_url = "website_url"
    category_one_discount_rate = "category_one_discount_rate"
    category_two_discount_rate = "category_two_discount_rate"
    number_of_nslp_students = "number_of_nslp_students"
    number_of_full_time_students = "number_of_full_time_students"
    community_eligibility_program_cep = "community_eligibility_program_cep"
    cep_percentage = "cep_percentage"
    nces_public_state_code = "nces_public_state_code"
    nces_public_district_code = "nces_public_district_code"
    nces_public_building_code = "nces_public_building_code"

    @classmethod
    def in_state(cls, state: str) -> SoQLBuilder:
        """Query entities in a given state.

        Note: This dataset uses ``physical_state`` rather than ``state``.
        """
        return SoQLBuilder().where_raw(
            f"upper(physical_state)='{_escape_soql_literal(state.upper())}'"
        )
