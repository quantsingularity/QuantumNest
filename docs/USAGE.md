# Usage Guide

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [CLI Usage](#cli-usage)
- [Library Usage](#library-usage)
- [Common Workflows](#common-workflows)
- [Web Interface](#web-interface)
- [API Integration](#api-integration)

## Overview

QuantumNest can be used in three primary ways:

1. **Web Interface** - User-friendly dashboard for portfolio management
2. **REST API** - Programmatic access for integrations
3. **CLI Tools** - Command-line scripts and utilities

## Getting Started

### Starting the Application

```bash
# Start all services
./run_quantumnest.sh

# Or start individual components
cd code/backend && uvicorn app.main:app --reload  # Backend API
cd web-frontend && npm run dev  # Web frontend
```

### Access Points

| Service                  | URL                         | Description            |
| ------------------------ | --------------------------- | ---------------------- |
| **Web Dashboard**        | http://localhost:3000       | Main user interface    |
| **API Backend**          | http://localhost:8000       | REST API endpoints     |
| **API Docs**             | http://localhost:8000/docs  | Interactive Swagger UI |
| **Alternative API Docs** | http://localhost:8000/redoc | ReDoc documentation    |

## CLI Usage

### Environment Management

```bash
# Check environment status
./scripts/env_manager.sh status

# Generate environment templates
./scripts/env_manager.sh template

# Validate environment files
./scripts/env_manager.sh validate
```

### Build and Deploy

```bash
# Build all components
./scripts/build.sh

# Run all tests
./scripts/run_all_tests.sh

# Check dependencies
./scripts/dependency_checker.sh
```

### Log Management

```bash
# View aggregated logs
./scripts/log_aggregator.sh collect

# Watch logs in real-time
./scripts/log_aggregator.sh watch

# Search logs
./scripts/log_aggregator.sh search "error"

# Analyze logs for issues
./scripts/log_aggregator.sh analyze
```

## Library Usage

### Python Backend API Usage

#### Authentication

```python
from app.auth.authentication import create_access_token, verify_password
from datetime import timedelta

# Create JWT token
token_data = {"sub": "user@example.com", "id": 1, "role": "user"}
access_token = create_access_token(
    data=token_data,
    expires_delta=timedelta(minutes=30)
)

# Verify password
is_valid = verify_password("plain_password", "hashed_password")
```

#### Portfolio Management

```python
from app.services.portfolio_service import PortfolioService
from app.db.database import get_db

# Initialize service
db = next(get_db())
portfolio_service = PortfolioService(db)

# Create portfolio
portfolio = portfolio_service.create_portfolio(
    user_id=1,
    name="My Investment Portfolio",
    description="Diversified tech stocks"
)

# Add asset to portfolio
asset = portfolio_service.add_asset(
    portfolio_id=portfolio.id,
    asset_symbol="AAPL",
    quantity=10,
    purchase_price=150.00
)

# Get portfolio performance
performance = portfolio_service.get_performance(
    portfolio_id=portfolio.id,
    period="1m"
)
```

#### AI Model Integration

```python
from app.ai.lstm_model import LSTMPredictor
from app.ai.portfolio_optimizer import PortfolioOptimizer
import numpy as np

# Price prediction
predictor = LSTMPredictor()
predictor.load_model("models/lstm_price_predictor.h5")

historical_data = np.array([...])  # Your historical price data
predictions = predictor.predict(historical_data, days_ahead=5)

print(f"Predicted prices: {predictions}")

# Portfolio optimization
optimizer = PortfolioOptimizer()
optimal_weights = optimizer.optimize(
    returns=returns_data,
    risk_tolerance=0.5,
    constraints={"max_position": 0.3}
)

print(f"Optimal allocation: {optimal_weights}")
```

#### Sentiment Analysis

```python
from app.ai.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Analyze market sentiment
sentiment = analyzer.analyze_asset_sentiment(
    asset_symbol="TSLA",
    sources=["news", "twitter", "reddit"]
)

print(f"Overall sentiment: {sentiment['score']}")
print(f"Sentiment label: {sentiment['label']}")
```

### Blockchain Integration

```python
from app.services.blockchain_service import BlockchainService
from web3 import Web3

# Initialize blockchain service
blockchain = BlockchainService(
    rpc_url="https://mainnet.infura.io/v3/YOUR-PROJECT-ID",
    private_key="YOUR_PRIVATE_KEY"
)

# Deploy tokenized asset
contract_address = blockchain.deploy_tokenized_asset(
    name="Apple Stock Token",
    symbol="AAPL-T",
    initial_supply=1000000,
    asset_value=15000  # $150.00 in cents
)

# Get asset details
asset_details = blockchain.get_asset_details(contract_address)
print(f"Asset: {asset_details['assetName']}")
print(f"Value: ${asset_details['assetValue'] / 100}")
```

## Common Workflows

### Workflow 1: User Registration and Login

```bash
# Using curl
# 1. Register new user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecureP@ss123"
  }'

# 2. Login
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=user@example.com&password=SecureP@ss123"

# Response includes access_token
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "user_id": 1,
#   "username": "newuser"
# }
```

### Workflow 2: Creating and Managing Portfolios

```python
import requests

# Set up authentication
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 1. Create portfolio
response = requests.post(
    "http://localhost:8000/portfolio/",
    headers=headers,
    json={
        "name": "Growth Portfolio",
        "description": "High-growth tech stocks"
    }
)
portfolio = response.json()
portfolio_id = portfolio["id"]

# 2. Add assets
assets = [
    {"asset_id": 1, "quantity": 10, "purchase_price": 150.00},
    {"asset_id": 2, "quantity": 5, "purchase_price": 350.00},
]

for asset in assets:
    asset["portfolio_id"] = portfolio_id
    requests.post(
        "http://localhost:8000/portfolio/assets/",
        headers=headers,
        json=asset
    )

# 3. View portfolio
response = requests.get(
    f"http://localhost:8000/portfolio/{portfolio_id}",
    headers=headers
)
print(response.json())

# 4. Get performance metrics
response = requests.get(
    f"http://localhost:8000/portfolio/performance/{portfolio_id}",
    headers=headers,
    params={"period": "1m"}
)
print(response.json())
```

### Workflow 3: AI-Powered Asset Prediction

```python
import requests
import time

# 1. Submit prediction task
response = requests.post(
    "http://localhost:8000/ai/predict/asset/AAPL",
    headers=headers,
    params={
        "days_ahead": 5,
        "model_type": "lstm"
    }
)
task_data = response.json()
task_id = task_data["task_id"]

print(f"Task submitted: {task_id}")

# 2. Poll for results
while True:
    response = requests.get(
        f"http://localhost:8000/ai/tasks/{task_id}",
        headers=headers
    )
    task_status = response.json()

    if task_status["status"] == "SUCCESS":
        predictions = task_status["result"]
        print(f"Predictions: {predictions}")
        break
    elif task_status["status"] == "FAILURE":
        print(f"Task failed: {task_status.get('error')}")
        break

    print("Waiting for results...")
    time.sleep(2)
```

### Workflow 4: Portfolio Optimization

```python
# Submit optimization task
response = requests.post(
    f"http://localhost:8000/ai/optimize/portfolio/{portfolio_id}",
    headers=headers,
    json={
        "risk_tolerance": 0.5,
        "constraints": {
            "max_position": 0.3,
            "min_position": 0.05
        }
    }
)

task_id = response.json()["task_id"]

# Check optimization results
response = requests.get(
    f"http://localhost:8000/ai/tasks/{task_id}",
    headers=headers
)

if response.json()["status"] == "SUCCESS":
    optimization = response.json()["result"]
    print("Recommended allocation:")
    for asset, weight in optimization["weights"].items():
        print(f"  {asset}: {weight*100:.2f}%")
```

### Workflow 5: Market Sentiment Analysis

```python
# Request sentiment analysis
response = requests.post(
    "http://localhost:8000/ai/sentiment/asset/TSLA",
    headers=headers,
    json={
        "sources": ["news", "twitter", "reddit"]
    }
)

task_id = response.json()["task_id"]

# Get sentiment results
response = requests.get(
    f"http://localhost:8000/ai/tasks/{task_id}",
    headers=headers
)

if response.json()["status"] == "SUCCESS":
    sentiment = response.json()["result"]
    print(f"Overall sentiment score: {sentiment['overall_score']}")
    print(f"Sentiment breakdown:")
    for source, data in sentiment["breakdown"].items():
        print(f"  {source}: {data['score']}")
```

## Web Interface

### Dashboard Overview

The web dashboard provides visual access to all platform features:

1. **Home Page** (`/`)
    - Platform overview
    - Key statistics
    - Quick actions

2. **Portfolio Dashboard** (`/portfolio`)
    - Portfolio list
    - Performance charts
    - Asset allocation
    - Transaction history

3. **Market Analysis** (`/market-analysis`)
    - Real-time market data
    - Interactive charts
    - Technical indicators
    - News feed

4. **AI Recommendations** (`/recommendations`)
    - Investment suggestions
    - Risk analysis
    - Market predictions
    - Portfolio optimization tips

5. **Blockchain Explorer** (`/blockchain-explorer`)
    - Token balances
    - Transaction history
    - Smart contract interactions
    - Asset tokenization

### Navigation

```
Main Menu:
├── Dashboard       # Portfolio overview
├── Portfolio       # Detailed portfolio management
├── Market Analysis # Market data and charts
├── Recommendations # AI-powered insights
├── Blockchain      # Token and contract management
└── Settings        # User preferences
```

## API Integration

### Authentication Pattern

```python
import requests

class QuantumNestClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/users/login",
            data={"email": email, "password": password}
        )
        data = response.json()
        self.token = data["access_token"]
        return data

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_portfolios(self):
        response = requests.get(
            f"{self.base_url}/portfolio/",
            headers=self.get_headers()
        )
        return response.json()

# Usage
client = QuantumNestClient()
client.login("user@example.com", "password")
portfolios = client.get_portfolios()
```

### Batch Operations

```python
# Create multiple assets in a portfolio
def add_multiple_assets(client, portfolio_id, assets):
    results = []
    for asset in assets:
        response = requests.post(
            f"{client.base_url}/portfolio/assets/",
            headers=client.get_headers(),
            json={
                "portfolio_id": portfolio_id,
                **asset
            }
        )
        results.append(response.json())
    return results

# Usage
assets = [
    {"asset_id": 1, "quantity": 10, "purchase_price": 150.00},
    {"asset_id": 2, "quantity": 5, "purchase_price": 350.00},
    {"asset_id": 3, "quantity": 20, "purchase_price": 75.00},
]

results = add_multiple_assets(client, portfolio_id=1, assets=assets)
```

### Error Handling

```python
def safe_api_call(func):
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Details: {e.response.json()}")
        except requests.exceptions.ConnectionError:
            print("Connection error - is the server running?")
        except requests.exceptions.Timeout:
            print("Request timed out")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        return None
    return wrapper

@safe_api_call
def get_portfolio(client, portfolio_id):
    return requests.get(
        f"{client.base_url}/portfolio/{portfolio_id}",
        headers=client.get_headers()
    )
```

## Best Practices

### 1. Token Management

- Store tokens securely (environment variables, secure storage)
- Refresh tokens before expiration
- Never commit tokens to version control

### 2. API Rate Limiting

- Respect rate limits (100 requests/minute by default)
- Implement exponential backoff for retries
- Use batch operations when possible

### 3. Error Handling

- Always check response status codes
- Handle network errors gracefully
- Log errors for debugging

### 4. Performance

- Cache frequently accessed data
- Use async operations for multiple requests
- Minimize payload sizes

### 5. Security

- Always use HTTPS in production
- Validate and sanitize inputs
- Keep dependencies updated

## Next Steps

- Explore [API Reference](API.md) for complete endpoint documentation
- Check [Examples](examples/) for more code samples
- Read [Configuration Guide](CONFIGURATION.md) for customization options
- See [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues

---

**Need Help?** [Open an issue](https://github.com/abrar2030/QuantumNest/issues) or check [Troubleshooting Guide](TROUBLESHOOTING.md).
