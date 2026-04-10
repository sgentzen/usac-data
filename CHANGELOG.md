# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `USACClient` with sync/async support, pagination, retries, and app token auth
- `SoQLBuilder` fluent query builder for Socrata SoQL
- Dataset definitions: `Form471`, `C2BudgetTool`, `Consultants`, `EntityInfo`
- Helper functions: `c2_budget_remaining_query`, `entities_without_consultant_query`, `frn_history_query`, `consultant_portfolio_query`
- Custom exceptions: `USACError`, `USACRetryError`
