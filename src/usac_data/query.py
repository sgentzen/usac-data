"""Fluent SoQL query builder for Socrata SODA API."""

from __future__ import annotations

import re
from typing import Any

_FIELD_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_ORDER_RE = re.compile(
    r"^(:id|[a-zA-Z_][a-zA-Z0-9_]*)(\s+(ASC|DESC))?$", re.IGNORECASE,
)
_SELECT_RE = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]*$"           # simple field
    r"|^[a-zA-Z_]+\(.*\)(\s+as\s+\w+)?$",  # aggregate expression
    re.IGNORECASE,
)


def _validate_field(name: str) -> str:
    """Validate that a field name contains only safe characters."""
    if not _FIELD_RE.match(name):
        raise ValueError(f"Invalid SoQL field name: {name!r}")
    return name


def _escape_soql_literal(value: Any) -> str:
    """Escape a value for use inside a SoQL single-quoted string literal."""
    return str(value).replace("'", "''")


class SoQLBuilder:
    """Builds SoQL query parameters for Socrata SODA API requests.

    Supports method chaining for a fluent interface.

    Examples::

        q = (
            SoQLBuilder()
            .select("entity_name", "frn")
            .where(funding_year=2024)
            .where_raw("total_authorized > 10000")
            .order_by("entity_name")
            .limit(500)
        )
        params = q.to_params()
        # {'$select': 'entity_name,frn', '$where': "funding_year='2024' ...", ...}
    """

    def __init__(self) -> None:
        self._select: list[str] = []
        self._where: list[str] = []
        self._order: list[str] = []
        self._group: list[str] = []
        self._having: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._q: str | None = None  # full-text search

    def copy(self) -> SoQLBuilder:
        clone = SoQLBuilder()
        clone._select = self._select[:]
        clone._where = self._where[:]
        clone._order = self._order[:]
        clone._group = self._group[:]
        clone._having = self._having[:]
        clone._limit = self._limit
        clone._offset = self._offset
        clone._q = self._q
        return clone

    def select(self, *fields: str) -> SoQLBuilder:
        """Set $select fields."""
        for f in fields:
            if not _SELECT_RE.match(f):
                raise ValueError(f"Invalid SoQL select expression: {f!r}")
        self._select.extend(fields)
        return self

    def where(self, raw: str | None = None, **kwargs: Any) -> SoQLBuilder:
        """Add $where conditions.

        Keyword args become equality filters: ``where(funding_year=2024)``
        becomes ``funding_year='2024'``.

        Warning: The ``raw`` parameter is interpolated directly into the
        query with no escaping. Never pass unsanitized user input to it.
        """
        if raw:
            self._where.append(raw)
        for field, value in kwargs.items():
            _validate_field(field)
            if value is None:
                self._where.append(f"{field} IS NULL")
            else:
                self._where.append(f"{field}='{_escape_soql_literal(value)}'")
        return self

    def where_raw(self, clause: str) -> SoQLBuilder:
        """Add a raw SoQL $where clause.

        Warning: ``clause`` is interpolated directly into the query with
        no escaping. Never pass unsanitized user input to this method.
        """
        self._where.append(clause)
        return self

    def where_in(self, field: str, values: list[Any]) -> SoQLBuilder:
        """Add field IN (...) filter."""
        _validate_field(field)
        escaped = ", ".join(f"'{_escape_soql_literal(v)}'" for v in values)
        self._where.append(f"{field} IN ({escaped})")
        return self

    def where_between(self, field: str, low: Any, high: Any) -> SoQLBuilder:
        """Add field BETWEEN low AND high filter."""
        _validate_field(field)
        self._where.append(
            f"{field} BETWEEN '{_escape_soql_literal(low)}' AND '{_escape_soql_literal(high)}'"
        )
        return self

    def where_like(self, field: str, pattern: str) -> SoQLBuilder:
        """Add field LIKE pattern filter."""
        _validate_field(field)
        self._where.append(f"{field} LIKE '{_escape_soql_literal(pattern)}'")
        return self

    def full_text(self, search: str) -> SoQLBuilder:
        """Set $q full-text search."""
        self._q = search
        return self

    def order_by(self, *fields: str) -> SoQLBuilder:
        """Set $order fields. Append ' DESC' to a field for descending."""
        for f in fields:
            if not _ORDER_RE.match(f):
                raise ValueError(f"Invalid SoQL order expression: {f!r}")
        self._order.extend(fields)
        return self

    def group_by(self, *fields: str) -> SoQLBuilder:
        """Set $group fields."""
        for f in fields:
            _validate_field(f)
        self._group.extend(fields)
        return self

    def having(self, clause: str) -> SoQLBuilder:
        """Add $having clause (requires group_by).

        Warning: ``clause`` is interpolated directly into the query with
        no escaping. Never pass unsanitized user input to this method.
        """
        self._having.append(clause)
        return self

    def limit(self, n: int) -> SoQLBuilder:
        self._limit = n
        return self

    def offset(self, n: int) -> SoQLBuilder:
        self._offset = n
        return self

    def to_params(self) -> dict[str, str]:
        """Convert to SODA API query parameters dict."""
        params: dict[str, str] = {}
        if self._select:
            params["$select"] = ",".join(self._select)
        if self._where:
            params["$where"] = " AND ".join(self._where)
        if self._order:
            params["$order"] = ",".join(self._order)
        if self._group:
            params["$group"] = ",".join(self._group)
        if self._having:
            params["$having"] = " AND ".join(self._having)
        if self._limit is not None:
            params["$limit"] = str(self._limit)
        if self._offset is not None:
            params["$offset"] = str(self._offset)
        if self._q:
            params["$q"] = self._q
        return params
