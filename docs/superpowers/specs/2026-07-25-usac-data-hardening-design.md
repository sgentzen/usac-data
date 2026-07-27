# usac-data hardening and consolidation

**Date:** 2026-07-25
**Status:** Design approved, pending implementation plan
**Target versions:** 0.1.7 (correctness), 0.2.0 (consolidation and polish)

## Context

usac-data is the shared Socrata/SODA layer for the E-Rate portfolio. Consumers:

- **erate-prospector** depends on `usac-data @ git+...@v0.1.4`.
- **erate-shepherd** imports `USACClient`, `Form471`, `Consultants` and
  `SoQLBuilder` in `src/erate_shepherd/source.py`.
- **erate-filing-assistant** is mid-migration onto the package; 0.1.5 added the
  two dataset definitions that were blocking it.

At v0.1.6 the package is 1,825 lines with 109 tests at 98 percent coverage,
ruff clean repository-wide and mypy strict clean on `src/`. The problems are at
the edges rather than in the core, and two of them are behavioural bugs.

An audit on 2026-07-25 produced the findings below. Each was reproduced rather
than inferred.

### Overtaken by PRs #4 to #7

The audit ran against a snapshot at `c4437bf`. While it was in progress, PRs #4
through #7 landed on `master` and released v0.1.6, resolving four findings
before this spec was written. They are recorded here so the plan is not read as
describing the current state:

- **CI now runs.** `a6fa523` changed the workflow trigger from `main` to
  `master`. The first execution in the project's history was on 2026-07-25;
  ten runs now exist and PRs are gated.
- **The package is on PyPI.** `c79bf6d` added a release workflow publishing via
  Trusted Publishing, and 0.1.6 is live. `pip install usac-data` works, so the
  README instruction needs no correction.
- **Lint already covers the repository.** The workflow runs `ruff check .`, and
  `7470d9f` aligned the PR template to match.
- **Actions are on current runtimes.** `2a73762` moved to `checkout@v7` and
  `setup-python@v7`.

What survives is everything below: both behavioural bugs, the remaining
verification gaps, drift protection, and the whole consolidation track.

## Goals

1. Close the verification gaps CI still has: `tests/` is neither type-checked
   nor covered by the matrix's newest interpreter, and nothing enforces
   coverage.
2. Fix two bugs that make the library do something other than what the caller
   asked for.
3. Detect USAC schema and dataset drift before consumers do.
4. Pull USAC domain knowledge that consumers have hand-rolled back into the
   package that owns the datasets.

## Non-goals

- **SECURITY.md, a docs site, or a deprecation policy.** The package is on PyPI
  as of 0.1.6, but it has no known external users, so it is still governed as an
  internal library. Breaking changes stay cheap because every caller is
  in-house. Revisit if outside consumers appear.
- **A caching layer.** erate-filing-assistant's SQLite `SodaCache` stays local.
- **Implementing rate limiting.** The docstring that claims it is corrected, not
  made true.
- **A `gfac-g858` dataset class.** See the finding below: it no longer exists and
  its fields now live in `qdmp-ygft`.
- **Classes for the remaining uncovered datasets.** PR 4 adds `Form470`
  (`jp7a-89nd`) and `Disbursements` (`jpiu-tj8h`). The other ten, including
  the rest of the Form 470 family and the Form 471 sibling tables, stay a
  tracked follow-up.

## Findings

### CI runs, but does not check everything it should

The trigger is fixed and the workflow is green, so the remaining gaps are narrow
but real:

- **`tests/` is not type-checked.** The workflow runs `mypy src/`. Running mypy
  over `tests/` surfaces four `comparison-overlap` errors in
  `tests/test_datasets.py` (lines 44, 45, 48, 49), where `StrEnum` members are
  compared to string literals. Nothing catches these today.
- **The matrix stops at 3.13** while the development environment runs 3.14.
- **Nothing enforces coverage.** `pytest-cov` is used locally but is not
  declared in the `dev` extra, so a coverage regression is invisible in CI.

The historical point still worth recording: CI first executed on 2026-07-25,
after five releases whose changelog entries claimed green tests, lint and types.
Those claims described a local machine. The lesson generalises beyond this
repository, and is why the drift work below assumes nothing is verified until a
scheduled job proves it.

### `.limit(n)` on a builder is silently discarded

`client.py:131` overwrites whatever the builder set:

```python
_build_params(Form471.for_year(2024).limit(10))
# -> {'$where': "funding_year='2024'", '$limit': '10000'}
```

This is the README quick-start example. It asks for ten rows and fetches ten
thousand.

### `count()` corrupts a query that already selects

`client.py:304` appends to the existing `$select` rather than replacing it, and
carries `$limit`, `$order` and `$offset` into the count request:

```python
SoQLBuilder().select("ben", "state").where(funding_year=2024)
# count() sends $select=ben,state,count(*) as count
```

### The client advertises rate limiting it does not have

`client.py:1`: "Low-level SODA API transport with pagination, retries, and rate
limiting." There is no rate limiting anywhere in the module.

### Live source check, 2026-07-25

A full check was run against the live catalogue and column metadata. Findings
below are verified, not inferred from the release notes alone.

**No field drift.** All 132 fields declared across the six dataset classes still
exist in live column metadata. Nothing usac-data declares has been renamed or
removed.

**`gfac-g858` was absorbed, not lost.** The "Skinny/Lite Deadline" view returns
404 and is absent from the catalogue, as is the older Post-Commitment tool
`xzxx-in68`. Its schema moved into `qdmp-ygft`, which now carries
`original_form_486_deadline`, `extension_request_for_invoicing`,
`last_date_to_invoice`, `f486_case_status`, `service_delivery_deadline`,
`invoicing_ready`, `spac_filed`, `remaining_extension_count` and `form_486_no`.
Only `frn_remaining_amount` and `expired_frn` did not survive the move, matching
erate-shepherd's `source.py:30-32` exactly. A new E-Rate Post-Commitment
Deadline Tool was announced on 2026-07-22 but has no tabular asset, so there is
nothing to add a class for.

**Release notes, cross-checked against live schemas:**

| Date | Announced | Verified |
| --- | --- | --- |
| 2026-07-22 | New Post-Commitment Deadline Tool | No tabular asset exists |
| 2026-07-17 | `original_form_486_deadline`, `extension_request_for_invoicing` added to FRN Status | Both present in `qdmp-ygft` |
| 2026-06-17 | `fcc_form_498_filed_with_uei` added to Entity Info | Present in `7i5i-83qf` |
| 2026-06-03 | "Open Data updates once daily. Sending multiple API calls in a day will pull the same data, and increases the cost to USAC" | Provider request |

**Declared field coverage is thin, and thinnest where it matters.** `Form471`
declares 14 of 84 available columns and none of the nine post-commitment fields
above, which are exactly what erate-shepherd built its deadline lattice from.
`EntityInfo` declares 21 of 104, `RecipientCommitments` 30 of 67, `Consultants`
5 of 17, `C2BudgetTool` 11 of 18.

**All six `name` attributes are stale.** USAC renamed the Form 471 family to a
consistent `E-Rate Request for Discount on Services: X (FCC Form 471 and Related
Information)` scheme. The docstring dataset URLs still redirect correctly and
need no change.

**Uncovered E-Rate datasets.** The catalogue holds 74 assets, 32 of them
tabular and 18 of those E-Rate branded. usac-data covers six, leaving twelve.
Beyond `jpiu-tj8h`, it covers none of the Form 470 family (`jt8s-3q52`,
`jp7a-89nd`, `363f-22uh`, `g55z-erud`, `39tn-hjzv`), the Form 471 sibling tables
(`9s6i-myen` Basic Information, `ym44-rnhq` Connectivity, `upfy-khtr` Discount
Calculations, `tuem-agyq` Recipients of Service), `xcy2-bdid` Service Provider
Information, or `hwzi-t5nj` Supplemental Information: Annexes. All are live and
updated daily.

The withdrawal is the strongest argument for drift protection in this list. A
dataset the portfolio depended on disappeared roughly a day after being verified
by hand, its replacement fields landed in a different dataset five days before
that, and nothing in usac-data noticed either event.

### Private API is being copied by consumers

`helpers.py` and `datasets/entity_info.py` import the private
`_escape_soql_literal` across module boundaries. erate-shepherd, unable to
import it cleanly, carries a byte-for-byte copy as `_esc()` at
`source.py:19`. The same file hard-codes `ENTITY_DATASET_ID = "7i5i-83qf"`,
duplicating `EntityInfo.dataset_id`, next to an import of usac-data.

### Domain knowledge lives in the wrong repository

erate-shepherd's `dedupe.py` is 25 lines of pure function encoding a fact about
`qdmp-ygft`: the feed carries multiple rows per FRN, and the canonical row is
latest-status-wins. It has no shepherd coupling. Any other consumer reading that
dataset rediscovers the trap the hard way.

`jpiu-tj8h` (invoices and authorised disbursements) is used by shepherd through
a hard-coded id with no dataset class anywhere.

### Version is duplicated

`pyproject.toml:7` and `src/usac_data/__init__.py:3` both carry the version.
They are in sync at 0.1.6, but they drifted once already: 0.1.5 shipped a fix
for `__version__` being stuck at 0.1.2 while pyproject had moved to 0.1.4. Now
that releases publish to PyPI automatically, a repeat would ship a wheel whose
reported version disagrees with its metadata.

### Stale artefacts

`docs/refactor-backlog.md` is fully discharged. Tasks 1 through 7 all shipped
across 0.1.2 to 0.1.4 and are recorded in CHANGELOG.md. It is now a second,
stale source of truth. Local `claude/*` branches and merged remote branches have
accumulated. A local `dist/` holds hand-built wheels that predate the release
workflow.

### Tests sleep for real

`tests/test_client.py::test_raises_retry_error_after_exhaustion` takes 3.24
seconds and the suite takes about 10, because the retry paths call the real
`time.sleep` and `asyncio.sleep`.

## Approach

Four pull requests, verification first.

The alternative of one 0.2.0 release is tempting for a package this small, but
PR 1 widens what CI actually checks, and every later PR wants to land under the
widened checks rather than beside them. Fixing the four `tests/` type errors
after adding two hundred lines of new tests is worse than fixing them first.

## PR 1: close the CI gaps

No source changes. Test-only and configuration-only.

**`.github/workflows/ci.yml`**

- Type-check step becomes `mypy src/ tests/`.
- Matrix adds `"3.14"`.

The trigger and the `ruff check .` scope are already correct as of `a6fa523`
and need no change.

**`tests/test_datasets.py`**

Fix the four `comparison-overlap` errors by comparing `FRNStatus.FUNDED.value`
against the string literal rather than the member. The runtime assertion is
unchanged; `StrEnum` members already equal their values.

**`tests/test_client.py`**

Patch `time.sleep` and `asyncio.sleep` in the retry tests. Retry timing is
already asserted through `_retry_wait` unit tests, so the integration tests need
only prove the loop runs the right number of times.

**`pyproject.toml`**

- Add `pytest-cov>=5` to the `dev` extra. It is currently used locally but
  undeclared.
- Add to `[tool.pytest.ini_options]`:
  `addopts = "--cov=usac_data --cov-report=term-missing --cov-fail-under=95"`.
  Coverage today is 98 percent, so 95 is a floor with headroom rather than a
  ratchet.
- Add the `3.14` classifier.

**Acceptance**

- CI is green on 3.11, 3.12, 3.13 and 3.14.
- `mypy src/ tests/` reports no errors.
- `ruff check .` passes.
- The suite completes in under three seconds locally, down from about ten.

## PR 2: correctness (release 0.1.7)

### Limit precedence

`_build_params` stops clobbering the builder. Precedence, highest first:

1. An explicit `limit=` argument to `get()`/`aget()`.
2. The builder's `.limit()`.
3. `self.page_size`.

```python
if limit is not None:
    params[PARAM_LIMIT] = str(limit)
elif PARAM_LIMIT not in params:
    params[PARAM_LIMIT] = str(self.page_size)
```

Offset follows the same shape: the signature changes to `offset: int | None =
None`, an explicit argument wins, and the builder's `$offset` is otherwise
preserved. An explicit `offset=0` now emits `$offset=0` where it was previously
dropped as falsy, which Socrata treats identically, so the signature change is
compatible for existing callers.

### Pagination honours a builder limit as a cap

`paginate()` and `apaginate()` currently force `page_size` per page and ignore
any builder limit. They will continue to page at `page_size`, but treat a
builder `.limit(n)` as a total cap: each request asks for
`min(page_size, remaining)`, and iteration stops once `n` rows have been
yielded. A builder `.offset(m)` becomes the starting offset that pagination
advances from, rather than being applied to every page.

### `count()` stops mutating the caller's query

Add a public method to `SoQLBuilder`:

```python
def filters_only(self) -> SoQLBuilder:
    """Return a copy carrying only the row filters ($where and $q).

    Select, order, group, having, limit and offset are dropped. Used to
    derive an aggregate query from a query written to return rows.
    """
```

`count()` and `acount()` become
`(query.filters_only() if query else SoQLBuilder()).select("count(*) as count")`.

Dropping `$group` is deliberate. A grouped `count(*)` returns one row per group,
so the existing `result[0]["count"]` would silently report the first group's
count as the total. `count()` documents that it counts matching rows and ignores
grouping.

### Documentation corrections

Remove "and rate limiting" from the `client.py` module docstring.

The README needs no other edit here. Its install section became true when 0.1.6
went to PyPI, and the quick-start becomes true once the limit bug is fixed:
`Form471.for_year(2024).limit(10)` will do what the example already claims.

### Single-source the version

`pyproject.toml` drops the literal `version` and gains:

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
path = "src/usac_data/__init__.py"
```

`__version__` in `__init__.py` becomes the single source. A test asserts
`importlib.metadata.version("usac-data") == usac_data.__version__`, so the
drift that produced the 0.1.5 fix cannot recur silently.

### Removals

- Delete `docs/refactor-backlog.md`. Its content is discharged and recorded in
  CHANGELOG.md 0.1.2 through 0.1.4. The one judgement worth keeping, Task 6's
  reasoning about why `with_remaining` coerces to float, already lives in the
  `C2BudgetTool.with_remaining` docstring and the 0.1.4 changelog entry.
- Delete the stale local `dist/` wheels. They are gitignored and local only, and
  releases now build from the workflow added in `c79bf6d`.
- Run the `worktree-cleanup` skill over the accumulated `claude/*` branches
  rather than hard-coding a delete list here, so merge status is verified at the
  time rather than assumed.

### Acceptance

- `client.get(id, Form471.for_year(2024).limit(10))` issues `$limit=10`.
- `client.get(id, q.limit(10), limit=5)` issues `$limit=5`.
- `count()` on a query with a `$select` issues `$select=count(*) as count` and
  no `$order`, `$limit` or `$offset`.
- `paginate(id, q.limit(25))` with `page_size=10` yields 25 rows in three
  requests, the last asking for 5.
- Regression tests for each of the above.
- CHANGELOG 0.1.7 entry under **Fixed**, calling the limit and count changes out
  as behavioural.

## PR 3: drift protection

### Declared-field introspection

Add to `DatasetMeta`:

```python
@classmethod
def fields(cls) -> dict[str, str]:
    """Return declared Socrata field names, keyed by attribute name.

    Excludes the dataset metadata attributes (dataset_id, name,
    description), callables and dunders.
    """
```

This has value beyond the drift test: it is what any consumer needs to build a
`$select` of everything known.

### Live test suite

`tests/test_live_drift.py`, every test marked `@pytest.mark.live`:

- Register the marker in `pyproject.toml` and add `-m "not live"` to `addopts`,
  so normal CI stays offline and fast.
- For each `DatasetMeta` subclass, GET
  `https://opendata.usac.org/api/views/{dataset_id}.json`.
- Assert the response is 200. A 404 means the dataset has been withdrawn, which
  is exactly the `gfac-g858` failure.
- Collect `{c["fieldName"] for c in body["columns"]}` and assert every declared
  field is present.
- Report all missing fields for a dataset in one assertion message rather than
  failing on the first, so a rename sweep is visible in a single run.
- Print live columns that no class declares as informational output without
  failing. The subset relation stays the pass condition, because USAC adding
  columns is not a breakage, but the additions need to be visible: the
  2026-07-17 arrival of `original_form_486_deadline` in `qdmp-ygft` is precisely
  the event a silent subset check would have hidden.
- Compare each class's `name` against the live asset name and report a mismatch
  as informational, not a failure. All six are stale today.

Verified endpoint shape on 2026-07-25: `/api/views/jpiu-tj8h.json` returns `id`,
`name` and a `columns` array of 37 entries, each with `fieldName`.

### Scheduled workflow

`.github/workflows/drift.yml`:

- `schedule: cron: "0 15 * * 1"` plus `workflow_dispatch`. Weekly rather than
  daily is deliberate: USAC has asked callers not to over-poll, and a schema
  change that sits undetected for at most a week is not the failure mode worth
  optimising against.
- Single Python version. Runs `pytest -m live`.
- `permissions: issues: write`.
- On failure, search open issues labelled `drift`. If none exists, open one
  titled `Drift: usac-data dataset schema check failed`, with the failing
  assertion output in the body. If one is already open, do not duplicate it.

### Acceptance

- `pytest` locally runs no network tests.
- `pytest -m live` passes today against all six declared datasets.
- A deliberately broken field name in a scratch branch produces exactly one
  issue, and a second run does not open a duplicate.

## PR 4: consolidation and polish (release 0.2.0)

### Public escape helper

`_escape_soql_literal` becomes `escape_soql_literal`, exported from
`usac_data`. The private name stays as a module-level alias so nothing breaks
mid-flight. `helpers.py` and `datasets/entity_info.py` switch to the public
name.

### `usac_data.dedupe`

Move erate-shepherd's `canonical_frn_rows` across unchanged, typed as
`list[dict[str, Any]] -> dict[str, dict[str, Any]]`, exported from the package
root. The docstring keeps the explanation of the trap: `qdmp-ygft` carries
multiple rows per FRN, rows with an FCDL date outrank rows without one, decided
statuses outrank `Pending`, and ties keep the first row seen.

Tests cover each rank dimension and the tie rule.

### `Disbursements` dataset

`jpiu-tj8h`, "E-Rate Invoices and Authorized Disbursements (FCC Forms 472 and
474)". Field names taken from live column metadata read on 2026-07-25, not
inferred.

The class documents what shepherd learned in production:

- Records are line-level. Aggregate by `funding_request_number`.
- `inv_line_item_status` is uniformly `SENT TO USAC` and carries no signal. Use
  `approved_inv_line_amt`.
- `consultant_registration_number` is often null, so query by FRN rather than by
  consultant.
- `invoice_type` distinguishes Service Provider (SPI) from Applicant (BEAR).

A `for_frns(frns)` helper batches, since the FRN list is typically long;
shepherd uses a batch size of 80.

### `Form470` dataset

`jp7a-89nd`, "E-Rate Open Competitive Bidding: Basic Information (FCC Form 470
and Related Information)". 70 columns, verified live on 2026-07-25.

**Why this dataset and not `jt8s-3q52`.** Both describe Form 470 filings.
`jp7a-89nd` is application-level. `jt8s-3q52` is line-level, one row per service
request, so a single form yields many rows and any "did they file?" question
needs a dedupe first. The consuming question is whether a client filed for a
funding year, so application grain is correct.

**Correction, verified 2026-07-26.** Application grain is not one row per Form
470, as this spec originally stated, and `(ben, funding_year)` is not a unique
key. The grain is one row per form *version*: a filing modified after
certification appears twice, as `form_version='Original'` and
`form_version='Current'`, identical in every other field. The dataset holds
283,990 rows for 249,759 distinct `application_number` values (249,761
`Original`, 34,229 `Current`), so roughly one filing in seven has been revised
and a naive row count overstates filings. An applicant can also file several
distinct Form 470s in one funding year.

Every filing has an `Original` row, so a `form_version='Original'` filter is
what makes a row count mean "filings". `f470_status` never disagrees between
the two versions of a filing, checked across the whole dataset, so status
questions are safe either way. The class gains an `originals_only()` method and
records this in its docstring.

Live check against BEN 143174 (a real erate-shepherd client) returned nine rows
across eight applications spanning funding years 2018 to 2025, with
`f470_status` values `Certified` and `Canceled`. The earlier "five rows"
observation predates the duplicate-version finding.

Declared fields cover the filing lifecycle (`application_number`, `f470_number`,
`funding_year`, `f470_status`, `allowable_contract_date`, `certified_datetime`,
`created_datetime`, `last_modified_datetime`), the applicant (`ben`,
`billed_entity_name`, `applicant_type`, `organization_type`,
`billed_entity_state`, `number_of_eligible_entities`) and the service
description (`category_one_description`, `category_two_description`,
`rfp_identifier`, `statewide_state`). Contact and authorised-person blocks are
declared but flagged in the docstring as personal data.

Convenience methods `for_ben`, `for_year` and `for_ben_year`, matching the
existing dataset classes.

**Two traps the docstring must record:**

- `f470_number` is a Socrata `url` column, so it deserialises as a nested
  object, not a string. Reading it as text yields a dict.
- The sibling `jt8s-3q52` carries `consulting_firm_data` as a composite string,
  `{e2e Exchange, LLC|16043595|315-422-7608|erate@erateexchange.com}`, so
  filtering it by consultant registration number silently returns nothing. This
  is the same trap `gfac-g858`'s `crn_data` had. `jp7a-89nd` has no consultant
  column at all, which is cleaner: join through `Consultants` (`x5px-esft`)
  instead.

Also note the applicant-key inconsistency this adds to: `Form470`, `Form471` and
`FRNLineItems` use `ben`, while `RecipientCommitments` and `jt8s-3q52` use
`billed_entity_number`. The README section on column naming gains `Form470`.

### `Form471` post-commitment fields

Add the nine post-commitment columns that arrived in `qdmp-ygft` when
`gfac-g858` was withdrawn: `original_form_486_deadline`,
`extension_request_for_invoicing`, `last_date_to_invoice`, `f486_case_status`,
`service_delivery_deadline`, `invoicing_ready`, `spac_filed`,
`remaining_extension_count` and `form_486_no`.

This is the highest-value addition in the PR. It is what erate-shepherd's
deadline lattice reads, and declaring it here means the next consumer does not
have to discover that FRN Status quietly became the post-commitment source.

The class docstring records that `frn_remaining_amount` and `expired_frn` did
**not** survive the move: remaining amount must be derived as committed less
disbursed, and expiry from the last date to invoice.

### Refresh stale dataset names

All six `name` attributes predate USAC's rename of the Form 471 family. Update
them to the live asset names. The docstring URLs still redirect and stay as they
are.

### Document the once-daily update cadence

USAC's 2026-06-03 release note asks callers not to poll more than once a day,
since the data refreshes daily and extra calls cost them money. Record this in
the `USACClient` docstring and the README. usac-data has no caching layer and is
not gaining one here, but consumers should not learn this from a support email.

### `iter_paginate()`

The sync generator matching `apaginate()`. `paginate()` is reimplemented as
`list(client.iter_paginate(...))` and keeps its existing signature and memory
warning.

### Dataset classes as arguments

`get`, `aget`, `count`, `acount`, `paginate`, `iter_paginate` and `apaginate`
accept `str | type[DatasetMeta]`, resolved through a small
`_resolve_dataset_id`. `client.get(Form471, query=q)` becomes valid alongside
the existing `client.get(Form471.dataset_id, query=q)`.

### Documentation

README gains `Disbursements` and `Form470` rows in the dataset table, `Form470`
in the existing column-naming section, a short section on `canonical_frn_rows`
explaining the duplicate-row trap, the dataset-class call form, and the
once-daily polling note. CHANGELOG gains a 0.2.0 entry.

The dataset table also gains a column distinguishing the grain of each dataset
(application, FRN, line item, recipient, entity, invoice line), because the
recurring failure across this portfolio is querying the right dataset at the
wrong grain.

### Acceptance

- `from usac_data import escape_soql_literal, canonical_frn_rows, Disbursements,
  Form470` works.
- `Form470.for_ben_year(143174, 2025)` returns the Canceled FY2025 filing
  verified during design.
- `pytest -m live` covers `Disbursements` through the same drift check as every
  other dataset.
- `paginate()` and `list(iter_paginate())` return identical results for the same
  query.
- `client.get(Form471)` and `client.get(Form471.dataset_id)` issue the same
  request.
- `pytest -m live` reports zero stale names and confirms all nine new `Form471`
  fields against live metadata.

## Testing strategy

Offline tests keep using `pytest-httpx` and stay the default. Network access is
confined to the `live` marker, which normal CI never selects.

Behavioural changes in PR 2 each get a regression test asserting the emitted
parameters, not just the return value, because the bugs are in what gets sent.

The drift suite asserts a subset relation rather than equality: USAC adding
columns is not a failure, and pinning the full column set would produce noise.

## Risks

**PR 2 changes behaviour.** Callers currently relying on `.limit()` being
ignored would start receiving fewer rows. This is a fix rather than a
regression, and the two known consumers do not set a builder limit before
paginating: shepherd's `source.py` calls `paginate()` with filter-only queries.
Verify against erate-prospector before releasing 0.1.7.

**Coverage floor as a ratchet.** Set at 95 against a current 98 so ordinary work
does not trip it. Revisit only if it starts blocking rather than catching.

**The drift check depends on USAC's metadata endpoint.** If the
`/api/views/<id>.json` shape changes, the check fails for the wrong reason. That
failure is loud and lands in an issue, which is the correct outcome for "we can
no longer tell whether the schema drifted".

## Consumer follow-ups (out of scope, tracked separately)

These are not part of this work but become possible once it lands:

- **erate-shepherd:** delete `_esc()` and `dedupe.py`, drop the hard-coded
  `ENTITY_DATASET_ID` and `DISBURSEMENT_DATASET_ID`, and import
  `escape_soql_literal`, `canonical_frn_rows`, `EntityInfo` and `Disbursements`
  from usac-data.
- **erate-filing-assistant:** two production bugs recorded in the memory graph
  under `usac-data--dataset-coverage-gap`, both still unfixed, both now
  addressable using the 0.1.5 dataset definitions.
- **erate-shepherd's `form_470` onboarding step.** Currently derived and manual.
  Once `Form470` ships it can become observed, like the `epc_association` step:
  a certified filing for the client's BEN and funding year confirms the step
  without a consultant ticking anything. That is a shepherd change, not a
  usac-data one, but it is the reason `Form470` is in scope.
- **Ten still-uncovered E-Rate datasets.** The rest of the Form 470 family
  (`jt8s-3q52`, `363f-22uh`, `g55z-erud`, `39tn-hjzv`), the Form 471 sibling
  tables (`9s6i-myen`, `ym44-rnhq`, `upfy-khtr`, `tuem-agyq`), `xcy2-bdid`
  Service Provider Information and `hwzi-t5nj` Supplemental Information:
  Annexes.
