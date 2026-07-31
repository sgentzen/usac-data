"""Tests for SoQLBuilder."""

from __future__ import annotations

import pytest

from usac_data.query import _AGGREGATE_FUNCTIONS, SoQLBuilder


class TestSoQLBuilder:
    def test_empty_builder(self) -> None:
        params = SoQLBuilder().to_params()
        assert params == {}

    def test_select(self) -> None:
        params = SoQLBuilder().select("a", "b").to_params()
        assert params["$select"] == "a,b"

    def test_where_kwargs(self) -> None:
        params = SoQLBuilder().where(funding_year=2024).to_params()
        assert params["$where"] == "funding_year='2024'"

    def test_where_none(self) -> None:
        params = SoQLBuilder().where(name=None).to_params()
        assert params["$where"] == "name IS NULL"

    def test_where_escapes_quotes(self) -> None:
        params = SoQLBuilder().where(name="O'Brien").to_params()
        assert params["$where"] == "name='O''Brien'"

    def test_where_raw(self) -> None:
        params = SoQLBuilder().where_raw("cost > 100").to_params()
        assert params["$where"] == "cost > 100"

    def test_where_combined(self) -> None:
        params = (
            SoQLBuilder()
            .where(year=2024)
            .where_raw("cost > 100")
            .to_params()
        )
        assert " AND " in params["$where"]
        assert "year='2024'" in params["$where"]
        assert "cost > 100" in params["$where"]

    def test_where_in(self) -> None:
        params = SoQLBuilder().where_in("year", [2023, 2024]).to_params()
        assert params["$where"] == "year IN ('2023', '2024')"

    def test_where_in_escapes(self) -> None:
        params = SoQLBuilder().where_in("name", ["O'Brien"]).to_params()
        assert params["$where"] == "name IN ('O''Brien')"

    def test_where_between(self) -> None:
        params = SoQLBuilder().where_between("cost", 100, 500).to_params()
        assert params["$where"] == "cost BETWEEN '100' AND '500'"

    def test_where_between_escapes(self) -> None:
        params = SoQLBuilder().where_between("name", "O'A", "O'Z").to_params()
        assert params["$where"] == "name BETWEEN 'O''A' AND 'O''Z'"

    def test_where_like(self) -> None:
        params = SoQLBuilder().where_like("name", "%test%").to_params()
        assert params["$where"] == "name LIKE '%test%'"

    def test_where_like_escapes(self) -> None:
        params = SoQLBuilder().where_like("name", "O'%").to_params()
        assert params["$where"] == "name LIKE 'O''%'"

    def test_full_text(self) -> None:
        params = SoQLBuilder().full_text("school").to_params()
        assert params["$q"] == "school"

    def test_order_by(self) -> None:
        params = SoQLBuilder().order_by("name", "year DESC").to_params()
        assert params["$order"] == "name,year DESC"

    def test_group_by(self) -> None:
        params = SoQLBuilder().group_by("state").to_params()
        assert params["$group"] == "state"

    def test_having(self) -> None:
        params = SoQLBuilder().group_by("state").having("count(*) > 5").to_params()
        assert params["$having"] == "count(*) > 5"

    def test_limit(self) -> None:
        params = SoQLBuilder().limit(50).to_params()
        assert params["$limit"] == "50"

    def test_offset(self) -> None:
        params = SoQLBuilder().offset(100).to_params()
        assert params["$offset"] == "100"

    def test_chaining(self) -> None:
        params = (
            SoQLBuilder()
            .select("a", "b")
            .where(year=2024)
            .order_by("a DESC")
            .limit(10)
            .to_params()
        )
        assert params["$select"] == "a,b"
        assert params["$where"] == "year='2024'"
        assert params["$order"] == "a DESC"
        assert params["$limit"] == "10"

    def test_invalid_field_in_where(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.where(**{"1=1) OR (1=1": "x"})

    def test_invalid_field_in_where_in(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.where_in("bad field!", [1])

    def test_invalid_field_in_where_between(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.where_between("bad;field", 1, 10)

    def test_invalid_field_in_where_like(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.where_like("bad field", "%x%")

    def test_invalid_field_in_order_by(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            builder.order_by("bad;field DESC")

    def test_invalid_field_in_group_by(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.group_by("bad field")

    def test_valid_order_with_direction(self) -> None:
        params = SoQLBuilder().order_by("name ASC", "year DESC").to_params()
        assert params["$order"] == "name ASC,year DESC"

    # The order/select patterns spell their character classes lowercase-only and
    # rely on re.IGNORECASE to accept uppercase. Dropping that flag would still
    # leave the patterns looking correct, so these pin the behaviour down.
    def test_order_by_accepts_uppercase_field(self) -> None:
        params = SoQLBuilder().order_by("Name DESC").to_params()
        assert params["$order"] == "Name DESC"

    def test_select_accepts_uppercase_field(self) -> None:
        params = SoQLBuilder().select("MyField").to_params()
        assert params["$select"] == "MyField"

    def test_where_accepts_uppercase_field(self) -> None:
        params = SoQLBuilder().where(Funding_Year=2024).to_params()
        assert params["$where"] == "Funding_Year='2024'"

    # re.ASCII is what stops Unicode case-folding from smuggling a non-ASCII
    # character past an identifier guard. U+212A and U+017F fold onto ASCII
    # "k" and "s", so without re.ASCII they pass as leading characters.
    @pytest.mark.parametrize("bad", ["Kelvin", "ſum", "café"])
    def test_order_by_rejects_non_ascii(self, bad: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            builder.order_by(bad)

    @pytest.mark.parametrize("bad", ["Kelvin", "ſum", "café"])
    def test_field_rejects_non_ascii(self, bad: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.group_by(bad)

    # The separator before the sort direction is a literal space, " +". \s would
    # admit a non-breaking space (it is Unicode-aware without re.ASCII) and, even
    # under re.ASCII, would still admit \n, \r, \t, \v and \f.
    def test_order_by_rejects_non_ascii_whitespace(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            builder.order_by("name DESC")

    # ASCII control whitespace is the other half of the separator guard: re.ASCII
    # narrows \s but does not exclude \n, \r, \t, \v or \f, so the patterns spell
    # the separator as a literal space instead.
    @pytest.mark.parametrize("sep", ["\n", "\r", "\t", "\v", "\f"])
    def test_order_by_rejects_control_whitespace_separator(self, sep: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            builder.order_by(f"name{sep}DESC")

    @pytest.mark.parametrize("sep", ["\n", "\r", "\t", "\v", "\f"])
    def test_select_rejects_control_whitespace_around_as(self, sep: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(f"count(*){sep}as{sep}x")

    # The two separator positions are pinned independently. A failure in the
    # first one masks the second, so a revert of just "as +" would otherwise
    # slip past the suite.
    @pytest.mark.parametrize("sep", ["\n", "\r", "\t", "\v", "\f"])
    def test_select_rejects_control_whitespace_before_as(self, sep: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(f"sum(a){sep}as b")

    @pytest.mark.parametrize("sep", ["\n", "\r", "\t", "\v", "\f"])
    def test_select_rejects_control_whitespace_after_as(self, sep: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(f"sum(a) as{sep}b")

    def test_select_rejects_non_ascii_whitespace_around_as(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select("count(*) as x")

    # "$" matches before a trailing newline; "\Z" does not.
    def test_field_rejects_trailing_newline(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            builder.group_by("name\n")

    def test_order_by_rejects_trailing_newline(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            builder.order_by("name\n")

    def test_select_aggregate(self) -> None:
        params = SoQLBuilder().select("count(*) as count").to_params()
        assert params["$select"] == "count(*) as count"

    def test_select_aggregate_over_column(self) -> None:
        params = SoQLBuilder().select("sum(total_authorized) as total").to_params()
        assert params["$select"] == "sum(total_authorized) as total"

    def test_invalid_select(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select("1=1; DROP TABLE")

    @pytest.mark.parametrize(
        "expression",
        [
            "sum(1) OR 1=1 --(x)",  # trailing clause smuggled after the call
            "a(x) as y, evil(z)",   # second expression smuggled after an alias
            "a(b),c(d)",            # comma-separated sub-expressions
            "evil(x)",              # function outside the allowlist
            "sum(a + b)",           # arbitrary expression as the argument
            "sum(a, b)",            # multiple arguments
            "count(*) as count; --",
            "sum((select x))",
            "sum(count(a))",        # nested call
            "sum()",                # empty argument, accepted before
            "count()",              # empty argument, accepted before
            "date_trunc_y(d)",      # real SoQL, but not an aggregate
            "upper(name)",          # real SoQL, but not an aggregate
            "entity_name as name",  # alias is aggregate-only
        ],
    )
    def test_select_rejects_smuggled_expressions(self, expression: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(expression)

    @pytest.mark.parametrize(
        "expression",
        ["ben\n", "count(*) as count\n", "ben\nevil", "sum(a)\n"],
    )
    def test_select_rejects_newlines(self, expression: str) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(expression)

    # count(*) is the only star form SoQL accepts; the rest take a column.
    def test_select_rejects_star_for_non_count_aggregates(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select("sum(*)")

    @pytest.mark.parametrize(
        "expression",
        [
            "count(*)",
            "count(*) as n",
            "count(ben)",
            "sum(total_authorized) as total",
            "avg(cost)",
            "min(cost) as cheapest",
            "MAX(Cost) AS Highest",
            "count_distinct(ben) as distinct_bens",
            "count_distinct(funding_request_number) as recipient_frn_count",
            "COUNT_DISTINCT(Ben) AS N",
        ],
    )
    def test_select_accepts_allowlisted_aggregates(self, expression: str) -> None:
        params = SoQLBuilder().select(expression).to_params()
        assert params["$select"] == expression

    # count_distinct is the one allowlisted name that has another as a prefix,
    # so both spellings have to keep validating independently of each other.
    def test_select_accepts_count_and_count_distinct_over_the_same_column(
        self,
    ) -> None:
        params = (
            SoQLBuilder()
            .select("count(frn) as frns", "count_distinct(frn) as distinct_frns")
            .to_params()
        )
        assert params["$select"] == "count(frn) as frns,count_distinct(frn) as distinct_frns"

    # SoQL documents these, but they are deliberately off the allowlist. They
    # are reachable through select_raw(), so this pins the narrower choice
    # rather than an oversight.
    @pytest.mark.parametrize(
        "expression",
        [
            "median(cost)",
            "stddev_pop(cost) as sd",
            "stddev_samp(cost)",
        ],
    )
    def test_select_rejects_aggregates_outside_the_allowlist(
        self, expression: str,
    ) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select(expression)

    # "count_distinct" is not a licence for any count_* name.
    def test_select_rejects_other_count_prefixed_functions(self) -> None:
        builder = SoQLBuilder()
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            builder.select("count_evil(ben)")

    # Pinned so that widening $select is a deliberate two-file edit rather than
    # a one-line append to the tuple.
    def test_aggregate_allowlist_is_pinned(self) -> None:
        assert set(_AGGREGATE_FUNCTIONS) == {
            "count_distinct", "count", "sum", "avg", "min", "max",
        }

    # Ordering inside the tuple is load-bearing, not cosmetic: the names are
    # joined into one regex alternation, and "count" is a prefix of
    # "count_distinct". Python's re does backtrack out of a shorter alternative,
    # so both orders happen to match today — this pins the order the module
    # comment prescribes, so the guard never comes to depend on that backtrack.
    def test_count_distinct_precedes_count_in_the_allowlist(self) -> None:
        functions = list(_AGGREGATE_FUNCTIONS)
        assert functions.index("count_distinct") < functions.index("count")

    def test_select_raw_bypasses_validation(self) -> None:
        params = SoQLBuilder().select_raw("date_trunc_ym(funding_date) as month").to_params()
        assert params["$select"] == "date_trunc_ym(funding_date) as month"

    # The documented migration for the aggregates left off the allowlist, so
    # the rejection tests above describe a narrowing rather than a dead end.
    @pytest.mark.parametrize(
        "expression",
        ["median(cost)", "stddev_pop(cost) as sd", "stddev_samp(cost)"],
    )
    def test_select_raw_reaches_non_allowlisted_aggregates(
        self, expression: str,
    ) -> None:
        params = SoQLBuilder().select_raw(expression).to_params()
        assert params["$select"] == expression

    def test_select_raw_combines_with_select(self) -> None:
        params = (
            SoQLBuilder()
            .select("ben")
            .select_raw("date_trunc_y(funding_date) as yr")
            .to_params()
        )
        assert params["$select"] == "ben,date_trunc_y(funding_date) as yr"

    def test_copy(self) -> None:
        original = SoQLBuilder().where(year=2024)
        copied = original.copy().where(state="VA")

        orig_params = original.to_params()
        copy_params = copied.to_params()

        assert "state" not in orig_params["$where"]
        assert "state" in copy_params["$where"]
