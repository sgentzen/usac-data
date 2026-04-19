# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-04-19

### Changed

- `USACClient` no longer eagerly constructs both `httpx.Client` and
  `httpx.AsyncClient` on init. Each transport is created on first use, so
  sync-only callers pay no async pool overhead and vice versa. (0ed9241)
- `close()` / `aclose()` are now no-ops when the respective transport was
  never created, and null out the reference after closing to prevent silent
  reuse of a closed client. (0ed9241)

### Fixed

- Backoff expression `RETRY_BACKOFF * (2**attempt)` changed to
  `RETRY_BACKOFF * (2.0**attempt)` to resolve a mypy strict `no-any-return`
  warning that was previously suppressed. (0ed9241)

## [0.1.2] - 2026-04-18

### Changed

- Extracted `_escape_soql_literal()` helper and replaced scattered inline
  `.replace("'", "''")` escapes across `SoQLBuilder` and helper queries. (1ba96b4)
- Extracted module-level constants for SoQL parameter keys
  (`PARAM_SELECT`, `PARAM_WHERE`, `PARAM_ORDER`, `PARAM_GROUP`, `PARAM_HAVING`,
  `PARAM_LIMIT`, `PARAM_OFFSET`, `PARAM_Q`) in `usac_data.query`. (7db9179)
- Consolidated duplicated sync/async retry logging into `_log_retry()`. (764e0be)
- `SoQLBuilder.copy()` now performs an explicit shallow copy instead of
  `copy.deepcopy()`, for a small speedup on hot paths. (1ba96b4)

### Fixed

- Non-retryable `HTTPStatusError` now propagates with the original traceback
  preserved (no silent loss of the `__cause__` chain). (e1b469b)

### Added

- Expanded `USACClient` docstring documenting retry/backoff/timeout semantics
  (429 + 5xx retry policy, exponential backoff, `Retry-After` handling,
  default timeout and retry limits). (bc72378)
- New test coverage for pagination edge cases and retry exhaustion. (80024a1)

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
