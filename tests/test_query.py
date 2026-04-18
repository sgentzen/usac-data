"""Tests for SoQLBuilder."""

from __future__ import annotations

import pytest

from usac_data.query import SoQLBuilder


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
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            SoQLBuilder().where(**{"1=1) OR (1=1": "x"})

    def test_invalid_field_in_where_in(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            SoQLBuilder().where_in("bad field!", [1])

    def test_invalid_field_in_where_between(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            SoQLBuilder().where_between("bad;field", 1, 10)

    def test_invalid_field_in_where_like(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            SoQLBuilder().where_like("bad field", "%x%")

    def test_invalid_field_in_order_by(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL order"):
            SoQLBuilder().order_by("bad;field DESC")

    def test_invalid_field_in_group_by(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL field name"):
            SoQLBuilder().group_by("bad field")

    def test_valid_order_with_direction(self) -> None:
        params = SoQLBuilder().order_by("name ASC", "year DESC").to_params()
        assert params["$order"] == "name ASC,year DESC"

    def test_select_aggregate(self) -> None:
        params = SoQLBuilder().select("count(*) as count").to_params()
        assert params["$select"] == "count(*) as count"

    def test_invalid_select(self) -> None:
        with pytest.raises(ValueError, match="Invalid SoQL select"):
            SoQLBuilder().select("1=1; DROP TABLE")

    def test_copy(self) -> None:
        original = SoQLBuilder().where(year=2024)
        copied = original.copy().where(state="VA")

        orig_params = original.to_params()
        copy_params = copied.to_params()

        assert "state" not in orig_params["$where"]
        assert "state" in copy_params["$where"]
