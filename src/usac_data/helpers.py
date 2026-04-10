"""High-level E-Rate query helpers.

These combine multiple datasets and encode domain knowledge about
USAC data relationships. Import and use directly or access via USACClient.
"""

from __future__ import annotations

from usac_data.datasets.c2_budget import C2BudgetTool
from usac_data.datasets.consultants import Consultants
from usac_data.datasets.form471 import Form471
from usac_data.query import SoQLBuilder


def c2_budget_remaining_query(
    min_remaining: float = 0,
    state: str | None = None,
) -> tuple[str, SoQLBuilder]:
    """Build query for entities with unspent C2 budget.

    Returns (dataset_id, query) tuple for use with USACClient.get().
    """
    q = C2BudgetTool.with_remaining(min_remaining)
    if state:
        escaped = state.upper().replace("'", "''")
        q = q.where_raw(f"upper(state)='{escaped}'")
    q = q.order_by("c2_budget_remaining DESC")
    return C2BudgetTool.dataset_id, q


def entities_without_consultant_query(
    funding_year: int,
    state: str | None = None,
) -> tuple[str, SoQLBuilder]:
    """Build query for Form 471 filings with no consultant listed.

    Returns (dataset_id, query) tuple.
    """
    q = (
        SoQLBuilder()
        .where(funding_year=funding_year)
        .where_raw("consultant_name IS NULL")
    )
    if state:
        escaped = state.upper().replace("'", "''")
        q = q.where_raw(f"upper(state)='{escaped}'")
    return Form471.dataset_id, q


def frn_history_query(
    entity_number: int,
    funding_years: list[int] | None = None,
) -> tuple[str, SoQLBuilder]:
    """Build query for an entity's FRN filing history.

    Returns (dataset_id, query) tuple.
    """
    q = SoQLBuilder().where(entity_number=entity_number)
    if funding_years:
        q = q.where_in("funding_year", funding_years)
    q = q.order_by("funding_year DESC", "frn")
    return Form471.dataset_id, q


def consultant_portfolio_query(
    consultant_name: str,
    funding_year: int | None = None,
) -> tuple[str, SoQLBuilder]:
    """Build query for all entities served by a consultant.

    Returns (dataset_id, query) tuple.
    """
    q = SoQLBuilder().where_like("consultant_name", f"%{consultant_name}%")
    if funding_year:
        q = q.where(funding_year=funding_year)
    return Consultants.dataset_id, q
