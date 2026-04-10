# usac-data

Python client for [USAC E-Rate Open Data](https://opendata.usac.org/) (Socrata SODA API).

Provides typed dataset definitions, a fluent SoQL query builder, automatic pagination, and high-level helpers for common E-Rate data queries.

## Install

```bash
pip install usac-data
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

| Class | Description |
|-------|-------------|
| `Form471` | FRN line items from E-Rate applications |
| `C2BudgetTool` | Category 2 five-year budget balances |
| `Consultants` | Consultant associations per application |
| `EntityInfo` | School/library demographics and details |

Each dataset class exposes field names as class attributes and convenience query methods.

## Helpers

- `c2_budget_remaining_query()` - entities with unspent C2 budget
- `entities_without_consultant_query()` - filings with no consultant
- `frn_history_query()` - entity FRN history across years
- `consultant_portfolio_query()` - entities served by a consultant

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/
mypy src/
```

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
