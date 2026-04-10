"""USAC dataset definitions.

Each dataset class maps to a Socrata dataset on opendata.usac.org and
exposes field names as class attributes plus convenience query methods.
"""

from __future__ import annotations

from usac_data.query import SoQLBuilder


class DatasetMeta:
    """Base class for USAC dataset definitions.

    Subclasses must set ``dataset_id``, ``name``, and ``description``
    as class attributes.
    """

    dataset_id: str
    name: str
    description: str

    @classmethod
    def query(cls) -> SoQLBuilder:
        """Return a fresh SoQLBuilder for this dataset."""
        return SoQLBuilder()


from usac_data.datasets.c2_budget import C2BudgetTool  # noqa: E402
from usac_data.datasets.consultants import Consultants  # noqa: E402
from usac_data.datasets.entity_info import EntityInfo  # noqa: E402
from usac_data.datasets.form471 import Form471  # noqa: E402

__all__ = [
    "C2BudgetTool",
    "Consultants",
    "DatasetMeta",
    "EntityInfo",
    "Form471",
]
