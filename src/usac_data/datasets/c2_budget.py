"""USAC Category 2 Budget Tool dataset."""

from __future__ import annotations

import math

from usac_data.datasets import DatasetMeta
from usac_data.query import SoQLBuilder


class C2BudgetTool(DatasetMeta):
    """Category 2 five-year budget balance dataset.

    Tracks C2 budget caps and remaining balances per entity.
    Dataset: https://opendata.usac.org/E-Rate/E-Rate-Category-2-Budget-Tool/6brt-5pbv
    """

    dataset_id = "6brt-5pbv"
    name = "C2 Budget Tool"
    description = "Category 2 five-year budget balances"

    # -- Known fields --
    ben = "ben"
    billed_entity_name = "billed_entity_name"
    applicant_type = "applicant_type"
    state = "state"
    full_time_students = "full_time_students"
    c2_budget = "c2_budget"
    funded_c2_budget_amount = "funded_c2_budget_amount"
    pending_c2_budget_amount = "pending_c2_budget_amount"
    available_c2_budget_amount = "available_c2_budget_amount"
    c2_budget_version = "c2_budget_version"
    c2_budget_cycle = "c2_budget_cycle"

    @classmethod
    def with_remaining(cls, min_remaining: float = 0) -> SoQLBuilder:
        """Query entities with at least ``min_remaining`` C2 budget left.

        ``min_remaining`` is interpolated directly into the raw SoQL ``$where``
        clause (Socrata SODA has no bind parameters), so it is coerced to
        ``float`` first. This makes the numeric constraint structural rather
        than relying on the runtime-unenforced type hint; non-numeric or
        non-finite input raises ``ValueError``. Do not remove the coercion.
        """
        amount = float(min_remaining)
        if not math.isfinite(amount):
            raise ValueError(f"min_remaining must be a finite number, got {min_remaining!r}")
        return SoQLBuilder().where_raw(
            f"available_c2_budget_amount > {amount}"
        )
