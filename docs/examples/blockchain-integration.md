# Blockchain Integration Examples

## Deploying a Tokenized Asset

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Deploy tokenized asset
response = requests.post(
    f"{API_URL}/blockchain/deploy-asset",
    headers=headers,
    json={
        "name": "Apple Stock Token",
        "symbol": "AAPL-T",
        "asset_symbol": "AAPL",
        "initial_supply": 1000000,
        "asset_value": 15000  # $150.00 in cents
    }
)

contract_data = response.json()
contract_address = contract_data["contract_address"]
print(f"Contract deployed at: {contract_address}")
```

## Checking Token Balance

```python
# Get token balance
response = requests.get(
    f"{API_URL}/blockchain/balance/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    headers=headers,
    params={"network": "ethereum"}
)

balance = response.json()
print(f"Balance: {balance['balance']} tokens")
```

## Getting Asset Details

```python
# Get asset information
response = requests.get(
    f"{API_URL}/blockchain/asset/{contract_address}",
    headers=headers
)

asset = response.json()
print(f"Asset: {asset['asset_name']}")
print(f"Value: ${asset['asset_value']/100:.2f}")
print(f"Trading Enabled: {asset['trading_enabled']}")
```

See [Blockchain Features](../FEATURE_MATRIX.md#blockchain-features) for all capabilities.
