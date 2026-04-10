"""Tests for helper functions."""

from __future__ import annotations

from usac_data import (
    c2_budget_remaining_query,
    consultant_portfolio_query,
    entities_without_consultant_query,
    frn_history_query,
)
from usac_data.datasets import C2BudgetTool, Consultants, Form471


class TestC2BudgetRemainingQuery:
    def test_basic(self) -> None:
        dataset_id, query = c2_budget_remaining_query()
        assert dataset_id == C2BudgetTool.dataset_id
        params = query.to_params()
        assert "c2_budget_remaining" in params["$where"]

    def test_with_min_remaining(self) -> None:
        _, query = c2_budget_remaining_query(min_remaining=5000)
        params = query.to_params()
        assert "5000" in params["$where"]

    def test_with_state(self) -> None:
        _, query = c2_budget_remaining_query(state="va")
        params = query.to_params()
        assert "VA" in params["$where"]

    def test_order_by_remaining(self) -> None:
        _, query = c2_budget_remaining_query()
        params = query.to_params()
        assert "DESC" in params["$order"]

    def test_state_escapes_quotes(self) -> None:
        _, query = c2_budget_remaining_query(state="o'brien")
        params = query.to_params()
        assert "O''BRIEN" in params["$where"]


class TestEntitiesWithoutConsultantQuery:
    def test_basic(self) -> None:
        dataset_id, query = entities_without_consultant_query(2024)
        assert dataset_id == Form471.dataset_id
        params = query.to_params()
        assert "consultant_name IS NULL" in params["$where"]
        assert "2024" in params["$where"]

    def test_with_state(self) -> None:
        _, query = entities_without_consultant_query(2024, state="ca")
        params = query.to_params()
        assert "CA" in params["$where"]


class TestFRNHistoryQuery:
    def test_basic(self) -> None:
        dataset_id, query = frn_history_query(12345)
        assert dataset_id == Form471.dataset_id
        params = query.to_params()
        assert "12345" in params["$where"]
        assert "DESC" in params["$order"]

    def test_with_years(self) -> None:
        _, query = frn_history_query(12345, funding_years=[2023, 2024])
        params = query.to_params()
        assert "IN" in params["$where"]


class TestConsultantPortfolioQuery:
    def test_basic(self) -> None:
        dataset_id, query = consultant_portfolio_query("Acme Corp")
        assert dataset_id == Consultants.dataset_id
        params = query.to_params()
        assert "LIKE" in params["$where"]
        assert "%Acme Corp%" in params["$where"]

    def test_with_year(self) -> None:
        _, query = consultant_portfolio_query("Acme", funding_year=2024)
        params = query.to_params()
        assert "2024" in params["$where"]
