# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-16

### Fixed

- `SoQLBuilder.order_by()` now accepts the Socrata `:id` system column. The
  previous `_ORDER_RE` regex rejected `:id`, which caused every paginated
  query (which defaults to `$order=:id` for stable pagination) to fail with
  `ValueError("Invalid SoQL order expression: ':id'")` before any HTTP
  request was made. (9fd6758)
- Dataset IDs and field names updated to match current USAC endpoints. (42eb66a)

### Added

- `usac_data.__version__` is now exposed so downstream consumers (and pip) can
  detect stale installs when pinning to a git URL.

## [0.1.0] - 2026-04-10

### Added

- `USACClient` with sync/async support, pagination, retries, and app token auth
- `SoQLBuilder` fluent query builder for Socrata SoQL
- Dataset definitions: `Form471`, `C2BudgetTool`, `Consultants`, `EntityInfo`
- Helper functions: `c2_budget_remaining_query`, `entities_without_consultant_query`, `frn_history_query`, `consultant_portfolio_query`
- Custom exceptions: `USACError`, `USACRetryError`
