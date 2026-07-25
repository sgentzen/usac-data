# usac-data

Python client for [USAC E-Rate Open Data](https://opendata.usac.org/) (Socrata SODA API).

Provides typed dataset definitions, a fluent SoQL query builder, automatic pagination, and high-level helpers for common E-Rate data queries.

## Install

Not on PyPI yet — install from the repository:

```bash
pip install "usac-data @ git+https://github.com/sgentzen/usac-data@v0.1.5"
```

Pin to a tag as above rather than a bare branch URL. `usac_data.__version__`
lets you confirm which revision actually got installed.

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

| Class | Dataset | Description |
|-------|---------|-------------|
| `Form471` | `qdmp-ygft` | FRN-level funding status |
| `FRNLineItems` | `hbj5-2bpj` | Form 471 line-item detail: product, quantity, cost |
| `RecipientCommitments` | `avi8-svp9` | Recipient detail and committed amounts |
| `C2BudgetTool` | `6brt-5pbv` | Category 2 five-year budget balances |
| `Consultants` | `x5px-esft` | Consultant associations per application |
| `EntityInfo` | `7i5i-83qf` | School/library demographics and details |

Each dataset class exposes field names as class attributes and convenience query methods.

### Column naming differs between datasets

These feeds do not agree on column names, and the two failure modes are different.
Check the class docstring before writing a filter.

- `FRNLineItems` uses **`ben`**. It has no `billed_entity_number` and no
  `chosen_category_of_service`; filtering on either returns HTTP 400
  `query.soql.no-such-column`, a hard failure.
- `RecipientCommitments` uses **`billed_entity_number`**. The post-discount
  committed amount is `post_discount_extended_eligible_line_item_costs` (there is
  no `total_authorized_disbursement`), and the discount percentage is `dis_pct`,
  not `discount_pct_c2`. Reading an absent field returns `None` silently, because
  Socrata omits absent fields from row JSON rather than rejecting the request.

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
