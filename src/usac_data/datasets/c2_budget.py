"""USAC Category 2 Budget Tool dataset."""

from __future__ import annotations

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class C2BudgetTool(DatasetMeta):
    """Category 2 five-year budget balance dataset.

    Tracks C2 budget caps and remaining balances per entity.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Category-2-Budgets/7zpf-aris
    """

    dataset_id = "7zpf-aris"
    name = "C2 Budget Tool"
    description = "Category 2 five-year budget balances"

    # -- Known fields --
    entity_number = "entity_number"
    entity_name = "entity_name"
    state = "state"
    c2_budget_5yr = "c2_budget_5yr"
    c2_budget_remaining = "c2_budget_remaining"
    c2_committed = "c2_committed"
    c2_disbursed = "c2_disbursed"

    @classmethod
    def with_remaining(cls, min_remaining: float = 0) -> SoQLBuilder:
        """Query entities with at least ``min_remaining`` C2 budget left."""
        if not isinstance(min_remaining, (int, float)):
            raise TypeError(
                f"min_remaining must be a number, got {type(min_remaining).__name__}"
            )
        return SoQLBuilder().where_raw(
            f"c2_budget_remaining > {min_remaining}"
        )
