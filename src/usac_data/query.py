"""Fluent SoQL query builder for Socrata SODA API."""

from __future__ import annotations

import re
from typing import Any

# These three patterns are the guard between caller input and generated SoQL,
# so every flag here is load-bearing:
#
# re.ASCII pins \w to [A-Za-z0-9_] and confines IGNORECASE case-folding to
# ASCII. Without it both are Unicode-aware, and the old Unicode-mode patterns
# really did leak: under Unicode IGNORECASE, [a-zA-Z_] matched U+212A KELVIN
# SIGN and U+017F LATIN SMALL LETTER LONG S (both case-fold onto ASCII
# letters), and \s matched U+00A0 and U+2028 as the separator before ASC/DESC.
#
# The separator before ASC/DESC and around AS is a literal space, [ ]+, not \s+.
# Even under re.ASCII, \s admits \n, \r, \t, \v and \f, so "name\nDESC" and
# "count(*)\tas\tx" would pass. Nothing downstream splits on those (httpx
# percent-encodes query parameters), but tolerating control characters while
# rejecting U+00A0 is an inconsistency not worth carrying in a guard pattern.
# This constrains the separator only: _SELECT_RE's aggregate branch still
# accepts an unvalidated \(.*\) body, so "count(a\tb)" is a separate hole.
#
# \Z rather than $, because $ also matches just before a trailing newline, so
# "name\n" would otherwise pass as a field name.
#
# The IGNORECASE patterns spell their classes lowercase-only: under IGNORECASE
# the a-z and A-Z ranges are redundant, which is what Sonar's S5869 flags.
# Uppercase input still matches, so tests cover that explicitly.
_FIELD_RE = re.compile(r"^[a-zA-Z_]\w*\Z", re.ASCII)  # no IGNORECASE: spell both cases
_ORDER_RE = re.compile(
    r"^(:id|[a-z_]\w*)([ ]+(asc|desc))?\Z", re.IGNORECASE | re.ASCII,
)
_SELECT_RE = re.compile(
    r"^[a-z_]\w*\Z"                             # simple field
    r"|^[a-z_]+\(.*\)([ ]+as[ ]+\w+)?\Z",       # aggregate expression
    re.IGNORECASE | re.ASCII,
)

# Socrata SODA API query parameter keys
PARAM_SELECT = "$select"
PARAM_WHERE = "$where"
PARAM_ORDER = "$order"
PARAM_GROUP = "$group"
PARAM_HAVING = "$having"
PARAM_LIMIT = "$limit"
PARAM_OFFSET = "$offset"
PARAM_Q = "$q"


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
            params[PARAM_SELECT] = ",".join(self._select)
        if self._where:
            params[PARAM_WHERE] = " AND ".join(self._where)
        if self._order:
            params[PARAM_ORDER] = ",".join(self._order)
        if self._group:
            params[PARAM_GROUP] = ",".join(self._group)
        if self._having:
            params[PARAM_HAVING] = " AND ".join(self._having)
        if self._limit is not None:
            params[PARAM_LIMIT] = str(self._limit)
        if self._offset is not None:
            params[PARAM_OFFSET] = str(self._offset)
        if self._q:
            params[PARAM_Q] = self._q
        return params
