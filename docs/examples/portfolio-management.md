# Portfolio Management Examples

## Creating a Portfolio

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create portfolio
response = requests.post(
    f"{API_URL}/portfolio/",
    headers=headers,
    json={
        "name": "Growth Portfolio",
        "description": "High-growth tech stocks"
    }
)

portfolio = response.json()
portfolio_id = portfolio["id"]
print(f"Created portfolio: {portfolio_id}")
```

## Adding Assets

```python
# Add multiple assets
assets = [
    {"asset_id": 1, "quantity": 10, "purchase_price": 150.00},
    {"asset_id": 2, "quantity": 5, "purchase_price": 350.00},
    {"asset_id": 3, "quantity": 20, "purchase_price": 75.00},
]

for asset in assets:
    asset["portfolio_id"] = portfolio_id
    response = requests.post(
        f"{API_URL}/portfolio/assets/",
        headers=headers,
        json=asset
    )
    print(f"Added asset: {response.json()}")
```

## Viewing Performance

```python
# Get performance metrics
response = requests.get(
    f"{API_URL}/portfolio/performance/{portfolio_id}",
    headers=headers,
    params={"period": "1m"}
)

performance = response.json()
print(f"Return: {performance['return_percentage']}%")
print(f"Sharpe Ratio: {performance['sharpe_ratio']}")
print(f"Max Drawdown: {performance['max_drawdown']}%")
```

See [Usage Guide](../USAGE.md) for more workflows.
