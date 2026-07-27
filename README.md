# usac-data

Python client for [USAC E-Rate Open Data](https://opendata.usac.org/) (Socrata SODA API).

Provides typed dataset definitions, a fluent SoQL query builder, automatic pagination, and high-level helpers for common E-Rate data queries.

## Install

```bash
pip install usac-data
```

Requires Python 3.11+. Versions before 0.1.6 were never published to PyPI; to
install one of those, use a tag-pinned git URL instead:

```bash
pip install "usac-data @ git+https://github.com/sgentzen/usac-data@v0.1.5"
```

## Quick start

```python
from usac_data import USACClient, Form471, C2BudgetTool

client = USACClient(app_token="optional-socrata-app-token")

# Simple query
rows = client.get(Form471.dataset_id, query=Form471.for_year(2024).limit(10))

# C2 budget with remaining funds in Virginia
from usac_data import c2_budget_remaining_query
dataset_id, query = c2_budget_remaining_query(min_remaining=5000, state="VA")
results = client.get(dataset_id, query=query)

# Async with full pagination
import asyncio

async def main():
    async with USACClient() as client:
        async for batch in client.apaginate(C2BudgetTool.dataset_id):
            print(f"Got {len(batch)} rows")

asyncio.run(main())
```

## Query builder

```python
from usac_data import SoQLBuilder

q = (
    SoQLBuilder()
    .select("entity_name", "frn", "total_authorized_disbursement")
    .where(funding_year=2024, frn_status="Funded")
    .where_raw("total_authorized_disbursement > 10000")
    .order_by("total_authorized_disbursement DESC")
    .limit(100)
)
```

## Datasets

| Class | Dataset | Grain (one row per) | Description |
|-------|---------|---------------------|-------------|
| `Form470` | `jp7a-89nd` | form version | Competitive bidding filings and their status |
| `Form471` | `qdmp-ygft` | FRN | FRN-level funding status |
| `FRNLineItems` | `hbj5-2bpj` | line item | Form 471 line-item detail: product, quantity, cost |
| `RecipientCommitments` | `avi8-svp9` | recipient per line item | Recipient detail and committed amounts |
| `Disbursements` | `jpiu-tj8h` | invoice line | Invoices and authorized disbursements actually paid |
| `C2BudgetTool` | `6brt-5pbv` | entity | Category 2 five-year budget balances |
| `Consultants` | `x5px-esft` | consultant per application | Consultant associations per application |
| `EntityInfo` | `7i5i-83qf` | entity | School/library demographics and details |

Each dataset class exposes field names as class attributes and convenience query methods.

The grain column matters more than it looks. The recurring mistake with these
feeds is querying the right dataset at the wrong grain: comparing a committed
amount against `Disbursements` without aggregating by FRN first, or counting
`Form470` rows as if they were filings. Check the grain before you aggregate.

USAC's Open Data refreshes once daily. Issuing the same query repeatedly within
a day returns identical data and costs USAC money, so cache results on your side
rather than polling.

### Column naming differs between datasets

These feeds do not agree on column names, and the two failure modes are different.
Check the class docstring before writing a filter.

- `FRNLineItems` uses **`ben`**. It has no `billed_entity_number` and no
  `chosen_category_of_service`; filtering on either returns HTTP 400
  `query.soql.no-such-column`, a hard failure.
- `Form470` uses **`ben`**, matching `Form471` and `FRNLineItems`.
- `RecipientCommitments` uses **`billed_entity_number`**. The post-discount
  committed amount is `post_discount_extended_eligible_line_item_costs` (there is
  no `total_authorized_disbursement`), and the discount percentage is `dis_pct`,
  not `discount_pct_c2`. Reading an absent field returns `None` silently, because
  Socrata omits absent fields from row JSON rather than rejecting the request.
- `Disbursements` carries **both**: `billed_entity_number` and, separately,
  `billed_entity_number_applicant_invoice` for the BEAR (applicant) invoice.

```python
from usac_data import USACClient, FRNLineItems, RecipientCommitments

with USACClient() as client:
    items = client.get(
        FRNLineItems.dataset_id,
        query=FRNLineItems.for_ben_year("123881", 2024),
    )
    commitments = client.get(
        RecipientCommitments.dataset_id,
        query=RecipientCommitments.for_ben_year("123881", 2024),
    )
```

### Form 470 rows are versions, not filings

`Form470` is application-grain, but a filing modified after certification
appears twice, as `form_version='Original'` and `form_version='Current'`,
identical in every other field. Counting rows overstates filings. Every filing
has an `Original` row, so `originals_only()` is the filter that makes a row
count mean what you expect:

```python
from usac_data import USACClient, Form470

with USACClient() as client:
    filings = client.get(
        Form470.dataset_id,
        query=Form470.for_ben_year(143174, 2025).where(form_version="Original"),
    )
```

`f470_status` never disagrees between the two versions of a filing, so status
questions are safe either way. Reach for the `Current` row when you need the
revised value of some other field. Note that one applicant can legitimately file
several distinct Form 470s in a funding year, so `(ben, funding_year)` is not a
unique key even after collapsing versions. Also, `f470_number` is a Socrata
`url` column, so it deserialises as a nested object rather than a string.

### Querying disbursements by FRN

`Disbursements` is line-level, so aggregate by `funding_request_number` before
comparing against a committed amount. `inv_line_item_status` is uniformly
`SENT TO USAC` and carries no signal; use `approved_inv_line_amt`. Because FRN
lists are usually long, `for_frns()` returns one query per batch:

```python
from usac_data import USACClient, Disbursements

with USACClient() as client:
    rows = [
        row
        for query in Disbursements.for_frns(frns)
        for row in client.get(Disbursements.dataset_id, query=query)
    ]
```

## Helpers

- `c2_budget_remaining_query()` - entities with unspent C2 budget
- `entities_without_consultant_query()` - filings with no consultant
- `frn_history_query()` - entity FRN history across years
- `consultant_portfolio_query()` - entities served by a consultant

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
