# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Form470` (`jp7a-89nd`), covering E-Rate competitive bidding filings at
  application grain, with `for_ben()`, `for_year()`, `for_ben_year()` and
  `originals_only()`. Chosen over the line-level sibling `jt8s-3q52` because
  the consuming question is whether an applicant filed for a funding year, not
  what services they requested.

  The class docstring records three traps found against live data: rows are one
  per form **version**, not per filing, so a form revised after certification
  appears as both `Original` and `Current` and a naive row count overstates
  filings (283,990 rows for 249,759 distinct applications as at 2026-07-26);
  `f470_number` is a Socrata `url` column and deserialises as a nested object,
  not a string; and there is no consultant column, so consultant questions must
  join through `Consultants` rather than filtering the sibling dataset's
  composite `consulting_firm_data` string, which silently matches nothing.

- `Disbursements` (`jpiu-tj8h`), covering invoices and authorized disbursements
  (FCC Forms 472 and 474), with a batching `for_frns()` helper. Records that
  rows are line-level and must be aggregated by `funding_request_number`, that
  `inv_line_item_status` is uniformly `SENT TO USAC` and carries no signal so
  `approved_inv_line_amt` is the field that matters, and that
  `consultant_registration_number` is frequently null so consultant-keyed
  queries under-report.

- A grain column in the README dataset table, and README sections on the
  Form 470 version duplication and on querying disbursements by FRN.

### Changed

- Dataset coverage is now 8 of the 18 E-Rate datasets USAC publishes. The
  remaining ten are tracked in the hardening spec.

- `USACClient` now drives its retries with [tenacity](https://tenacity.readthedocs.io/)
  instead of a hand-rolled loop duplicated across `_fetch_sync` and
  `_fetch_async`. New runtime dependency: `tenacity>=8.3`.

  The retry contract is unchanged: retry on 429 and 5xx plus transport errors,
  raise immediately on any other 4xx, honour `Retry-After` on 429 (falling back
  to 30s), exponential backoff of `RETRY_BACKOFF * 2 ** attempt` otherwise, and
  raise `USACRetryError` chained to the last failure once `max_retries`
  attempts are used up. The warning line logged before each wait keeps its
  existing format.

  Two behavioural differences, both on paths that were doing nothing useful:

  - The old loop slept once more *after* the final failed attempt before giving
    up, so a run with `max_retries=3` waited 1s, 2s and then a pointless 4s
    before raising. Tenacity does not sleep when it has no attempt left, so
    `USACRetryError` is now raised as soon as the last attempt fails. The final
    "Retry 3/3" warning that accompanied that dead wait is gone with it.
  - `max_retries=0` used to skip the request loop entirely and raise
    `USACRetryError` without ever calling USAC. It now makes one attempt and
    returns the rows if that attempt succeeds.

- Development and CI now use [uv](https://docs.astral.sh/uv/). `uv.lock` is
  committed and CI installs from it with `uv sync --locked`, so every job runs
  the exact versions recorded there instead of re-resolving. Contributors run
  `uv sync --all-extras`; regenerate the lock with `uv lock` after changing
  dependencies. Release builds use `uv build`, and both workflows now pin
  third-party actions to full commit SHAs and grant permissions per job.

  Dev tooling floors moved up accordingly: `pytest>=9.0`, `pytest-asyncio>=1.3`,
  `pytest-httpx>=0.35`, `ruff>=0.16` and `mypy>=2.0`. These are dev-only extras
  and do not constrain consumers. The runtime floors are unchanged, and the
  build backend is now bounded at `hatchling>=1.27,<2`.

### Security

- The SoQL identifier validators in `query.py` are now ASCII-anchored
  (`re.ASCII`), closing a Unicode case-folding bypass. `\w` and `\s` are
  Unicode-aware by default, so under `re.IGNORECASE` the old patterns accepted
  characters that case-fold onto ASCII letters, including U+212A KELVIN SIGN
  and U+017F LATIN SMALL LETTER LONG S, as leading characters of a field name
  or order clause, and accepted non-ASCII whitespace such as U+00A0 as the
  separator before `ASC`/`DESC`. The patterns also anchor with `\Z` rather than
  `$`, which matched before a trailing newline and let `"name\n"` pass as a
  field name.

  The separator before `ASC`/`DESC` in an `$order` clause, and the one around
  the `AS` in a `$select` aggregate expression, is now a literal space rather
  than `\s+`. `re.ASCII` narrows `\s` to ASCII whitespace but that still admits
  `\n`, `\r`, `\t`, `\v` and `\f`, so `order_by("name\nDESC")` and
  `select("count(*)\tas\tx")` were accepted while the U+00A0 equivalents were
  rejected. Nothing downstream splits on those characters (httpx
  percent-encodes query parameters), so this closes an inconsistency in the
  guard rather than an exploitable hole.

  This is a narrowing only. Field names containing non-ASCII characters are now
  rejected, which no USAC dataset uses, as is ASCII control whitespace used as
  an identifier separator. A single space, as in `"name DESC"` and
  `"count(*) as n"`, is unaffected.

## [0.1.6] - 2026-07-25

First release published to PyPI. Versions 0.1.0–0.1.5 exist only as git tags.

### Added

- Release workflow (`.github/workflows/release.yml`) publishing to PyPI via
  Trusted Publishing, so no PyPI API token is stored in the repository. It runs
  only on a **published GitHub Release**, not on tag push — publishing is
  irreversible (a version number cannot be reused, even after deletion), so it
  requires a deliberate action rather than happening as a side effect of
  tagging. Build and publish are separate jobs; only the publish job holds
  `id-token: write`.

  The workflow fails the build if the release tag, `pyproject.toml` and
  `__version__` disagree. That is a guard against a drift this project has
  already had once: `__version__` sat at `0.1.2` while `pyproject.toml` had
  moved to `0.1.4` (fixed in 0.1.5). Shipping that would have put a wheel on
  PyPI reporting a version different from its tag, uncorrectable in place.

  The one-time setup this depends on — a Trusted Publisher registered on PyPI
  and a `pypi` repository environment — is in place as of this release. See
  `docs/releasing.md`.

- `docs/releasing.md` documenting the setup, the release procedure, and how to
  verify a build locally.

### Fixed

- CI never ran. `.github/workflows/ci.yml` triggered on `branches: [main]`, but
  this repository's default branch is `master`, so neither the `push` nor the
  `pull_request` trigger ever matched. The workflow had zero recorded runs since
  the repo was created — every release through 0.1.5, and PRs #1–#3, merged with
  no automated lint, type check, or test run. Both triggers now name `master`.
- CI lint step widened from `ruff check src/` to `ruff check .`, so `tests/` is
  linted too. The project had two conflicting conventions — `docs/refactor-backlog.md`
  verified with `ruff check .` while CI, `CONTRIBUTING.md` and `README.md` used
  `ruff check src/`, meaning test code was never linted anywhere. All four now
  say `ruff check .`. `tests/` is already clean under it, so this adds coverage
  without requiring fixes.

### Documentation

- `README.md`'s `pip install usac-data` now actually works. Through 0.1.5 the
  README advertised it while the package had never been published (the name
  404'd on PyPI), so the command failed for anyone following the README. It is
  correct as of this release; the git-URL install is kept alongside it for
  earlier versions, which remain unpublished.

## [0.1.5] - 2026-07-25

### Added

- `FRNLineItems` dataset (`hbj5-2bpj`), the FCC Form 471 line-item detail feed:
  product, function, quantity and cost per line item. This is a different dataset
  from `Form471` (`qdmp-ygft`), which is FRN-level status. Field names were
  verified against the live column metadata rather than inferred.
- `RecipientCommitments` dataset (`avi8-svp9`), recipient-level detail and
  committed amounts, including the chosen category of service and pre- and
  post-discount line-item costs.

Both carry `for_ben()`, `for_year()` and `for_ben_year()` helpers;
`RecipientCommitments` also has `category_two_only()`.

### Fixed

- `__version__` in `usac_data/__init__.py` was stuck at `0.1.2` while
  `pyproject.toml` had moved to `0.1.4`. Both now read `0.1.5`.

### Notes on the two new datasets

They disagree with each other, and with `Form471`, on column naming. The classes
document this and the tests pin it, because getting it wrong fails in two
different ways:

- `FRNLineItems` identifies the applicant as `ben`. It has **no**
  `billed_entity_number` and **no** `chosen_category_of_service` column.
  Filtering on either returns HTTP 400 `query.soql.no-such-column`, a hard
  failure. It also carries no service-provider (`spin_name`, `spin_number`) or
  FRN-status columns.
- `RecipientCommitments` identifies the applicant as `billed_entity_number`. It
  has **no** `total_authorized_disbursement` column; the post-discount committed
  amount is `post_discount_extended_eligible_line_item_costs`, and the discount
  percentage is `dis_pct`, not `discount_pct_c2`. Reading an absent field here
  yields `None` silently, because Socrata omits absent fields from row JSON
  instead of rejecting the request.

## [0.1.4] - 2026-06-20

### Security

- `C2BudgetTool.with_remaining()` now coerces `min_remaining` to `float` before
  interpolating it into the raw SoQL `$where` clause. The value is built into the
  query string unescaped (Socrata SODA has no bind parameters), so a non-numeric
  argument such as `"0 OR 1=1"` could otherwise be smuggled into the query. The
  coercion makes the numeric constraint structural rather than relying on the
  (runtime-unenforced) type hint; non-numeric or non-finite (`nan`/`inf`) input
  now raises `ValueError`. This replaces the `isinstance` guard that was briefly
  removed during a refactor.

### Removed

- Dropped the non-functional `state` parameter from
  `entities_without_consultant_query()`. The Form 471 Consultants dataset has no
  `state` column, so the filter produced a query that the API rejects. Match
  against `EntityInfo` by `organization_name` for state-level filtering.

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
