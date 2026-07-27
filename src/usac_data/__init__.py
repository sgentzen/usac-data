"""Python client for USAC E-Rate Open Data (Socrata SODA API)."""

__version__ = "0.2.0"

from usac_data.client import USACClient
from usac_data.datasets import (
    C2BudgetTool,
    Consultants,
    DatasetMeta,
    Disbursements,
    EntityInfo,
    Form470,
    Form471,
    FRNLineItems,
    RecipientCommitments,
)
from usac_data.exceptions import USACError, USACRetryError
from usac_data.helpers import (
    c2_budget_remaining_query,
    consultant_portfolio_query,
    entities_without_consultant_query,
    frn_history_query,
)
from usac_data.query import SoQLBuilder

__all__ = [
    "__version__",
    "C2BudgetTool",
    "Consultants",
    "DatasetMeta",
    "Disbursements",
    "EntityInfo",
    "FRNLineItems",
    "Form470",
    "Form471",
    "RecipientCommitments",
    "SoQLBuilder",
    "USACClient",
    "USACError",
    "USACRetryError",
    "c2_budget_remaining_query",
    "consultant_portfolio_query",
    "entities_without_consultant_query",
    "frn_history_query",
]
