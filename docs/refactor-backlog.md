# Refactor Backlog

**Milestone:** Code quality: refactor & efficiency sweep
**Priority:** High
**Scope:** Non-functional cleanup — DRY, constants, minor perf. No behavior changes, no new features.

Source: planning session 2026-04-18. Intended to be imported into vibe-dash when the MCP is available.

Each task should land as an independent PR. All changes must preserve behavior (pytest, mypy strict, ruff all green).

---

## Task 1 — Extract SoQL parameter-key constants

**Files:** `src/usac_data/query.py` (lines 155-174), `src/usac_data/client.py` (lines 112-118)

The SoQL `$`-prefixed keys (`$limit`, `$offset`, `$order`, `$select`, `$where`, `$group`, `$having`, `$q`) appear 3+ times across these files. Per the global "no repeated string literals 3+ times" rule, extract module-level constants (e.g. `PARAM_LIMIT = "$limit"`) in `query.py` and reuse from `client.py`.

**Acceptance:** No more raw `"$..."` literals in `to_params()` or `_build_params()`. Tests unchanged.

---

## Task 2 — Centralize SoQL single-quote escaping

**Files:**
- `src/usac_data/query.py` (lines 83, 99, 106-107, 114)
- `src/usac_data/helpers.py` (lines 25, 50)
- `src/usac_data/datasets/entity_info.py` (line 50)

`str(value).replace("'", "''")` is duplicated ~6 times, plus one `chr(39)` variant in `query.py:99` used to dodge a lint rule. Extract a single `_escape_soql_literal(value: Any) -> str` helper in `query.py`, export it for the helpers/datasets modules to reuse, and drop the `chr(39)` hack.

**Acceptance:** One helper, all call sites routed through it. Test `where(x="o'brien")` produces identical output.

---

## Task 3 — DRY the retry loop in `_fetch_sync` / `_fetch_async`

**File:** `src/usac_data/client.py` (lines 139-199)

`_fetch_sync` and `_fetch_async` duplicate a 30-line retry loop verbatim. The only real differences are the HTTP call (sync vs `await`) and the sleep. Extract a helper `_compute_retry_wait(exc, attempt) -> float` that absorbs the repeated ternary at lines 154-158 / 185-189, and factor the shared "warn + sleep" log line. The two fetch methods stay as thin wrappers — full unification requires an async bridge and isn't worth the complexity.

**Acceptance:** Retry-after logic identical (429 with and without `Retry-After`, 5xx backoff, transport-error backoff). All existing retry tests pass.

---

## Task 4 — Replace `copy.deepcopy` in `SoQLBuilder.copy()`

**File:** `src/usac_data/query.py` (lines 56-57)

State is only `list[str]` plus scalars. `deepcopy` is overkill. Replace with an explicit shallow copy of the six lists and the scalar fields. Drop the `import copy` if unused after the change.

**Acceptance:** `q.copy()` still produces an independent builder — mutating the copy does not affect the original. Covered by existing test; add one if missing.

---

## Task 5 — Lazy-instantiate the unused httpx client

**File:** `src/usac_data/client.py` (lines 70-79)

Today `USACClient.__init__` eagerly creates both `httpx.Client` and `httpx.AsyncClient`. Sync-only callers pay connection-pool setup for the async client, and vice versa. Convert `_sync_client` and `_async_client` to lazy properties (or cached attributes instantiated on first use). `close()` / `aclose()` must continue to no-op when the respective client was never created.

**Acceptance:** Public API unchanged. Creating a `USACClient` and immediately calling `close()` doesn't construct the async client. All existing tests pass.

---

## Task 6 — Drop redundant `isinstance` runtime check — ⚠️ WON'T FIX (security)

**File:** `src/usac_data/datasets/c2_budget.py` (lines 36-39)

~~Classmethod validates `isinstance(min_remaining, (int, float))` despite a `float` type hint and the project's mypy-strict config. Belt-and-suspenders at best; noise at worst. Remove the check.~~

**Reconsidered — do NOT remove the runtime check.** `min_remaining` is interpolated
*raw and unescaped* into the SoQL `$where` clause, and Socrata has no bind
parameters, so the value is a trust boundary. The type hint is **not**
runtime-enforced (mypy strict only checks call sites that mypy actually sees;
callers passing `Any` / untyped data bypass it entirely). Removing the guard
reintroduced a SoQL-injection path (`with_remaining("0 OR 1=1")`).

**Resolution:** Replaced the `isinstance` guard with `float(min_remaining)`
coercion — same protection, but structural (the interpolated value is provably
numeric) so it can't be "cleaned up" again. Regression test:
`test_with_remaining_rejects_injection`. Shipped in 0.1.4.

---

## Task 7 — Consolidate `state.upper()` escape in helpers

**File:** `src/usac_data/helpers.py` (lines 25, 50)

Once Task 2 lands, `state.upper().replace("'", "''")` collapses to `_escape_soql_literal(state.upper())`. Can bundle into the Task 2 PR rather than shipping separately — track here so it isn't lost if Task 2 gets scoped down.

**Acceptance:** All helper query builders route through the shared escape helper.

---

## Out of scope (explicitly)

- **Adding a sync-paginate generator.** `paginate()` materializes the full result; an `iter_paginate()` would be a new API surface, not a refactor.
- **Session/connection-pool caching beyond lazy init.** `httpx.Client` already pools connections internally.
- **Parameterized queries.** Socrata SODA does not support bind parameters; string building with centralized escaping is the correct approach.

## Verification (applies to every task)

```
uv run pytest
uv run mypy src/
uv run ruff check .
```

Plus a manual spot-check that a query with single quotes round-trips identically pre- and post-change.
