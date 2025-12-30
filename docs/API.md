# API Reference

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
    - [Users API](#users-api)
    - [Portfolio API](#portfolio-api)
    - [Market Data API](#market-data-api)
    - [AI API](#ai-api)
    - [Blockchain API](#blockchain-api)
    - [Admin API](#admin-api)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Overview

QuantumNest provides a comprehensive RESTful API built with FastAPI. The API follows REST principles and returns JSON responses.

**API Version**: 1.0.0  
**Protocol**: HTTP/HTTPS  
**Format**: JSON  
**Authentication**: JWT Bearer Token

## Authentication

### JWT Bearer Token

All protected endpoints require a valid JWT token in the Authorization header.

```http
Authorization: Bearer <your_access_token>
```

### Obtaining a Token

```bash
POST /users/login
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=yourpassword
```

**Response:**

```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "user_id": 1,
    "username": "john_doe",
    "email": "user@example.com",
    "role": "user"
}
```

### Token Expiration

| Token Type    | Expiration | Renewable |
| ------------- | ---------- | --------- |
| Access Token  | 30 minutes | No        |
| Refresh Token | 7 days     | Yes       |

## Base URL

| Environment     | Base URL                             |
| --------------- | ------------------------------------ |
| **Development** | `http://localhost:8000`              |
| **Staging**     | `https://staging-api.quantumnest.io` |
| **Production**  | `https://api.quantumnest.io`         |

## Endpoints

### Users API

#### Create User

```http
POST /users/
```

**Request Body:**

| Name     | Type   | Required? | Default | Description         | Example            |
| -------- | ------ | --------- | ------- | ------------------- | ------------------ |
| username | string | Yes       | -       | Unique username     | "john_doe"         |
| email    | string | Yes       | -       | Valid email address | "john@example.com" |
| password | string | Yes       | -       | Min 8 characters    | "SecureP@ss123"    |
| role     | string | No        | "user"  | User role           | "user"             |

**Example Request:**

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecureP@ss123"
  }'
```

**Example Response:**

```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2025-04-01T10:30:00Z"
}
```

#### Get User

```http
GET /users/{user_id}
```

| Method | Path               | Description    | Query/Body params       | Auth required | Example request |
| ------ | ------------------ | -------------- | ----------------------- | ------------- | --------------- |
| GET    | `/users/{user_id}` | Get user by ID | Path: user_id (integer) | Yes           | `GET /users/1`  |

**Example Response:**

```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "last_login": "2025-04-01T10:30:00Z",
    "created_at": "2025-04-01T10:30:00Z"
}
```

#### Update User

```http
PUT /users/{user_id}
```

**Request Parameters:**

| Name     | Type   | Required? | Default | Description  | Example            |
| -------- | ------ | --------- | ------- | ------------ | ------------------ |
| username | string | No        | -       | New username | "jane_doe"         |
| email    | string | No        | -       | New email    | "jane@example.com" |
| password | string | No        | -       | New password | "NewP@ss456"       |

#### Delete User

```http
DELETE /users/{user_id}
```

**Response:** `204 No Content`

#### Login

```http
POST /users/login
```

**Request:**

```
email=user@example.com&password=yourpassword
```

**Response:** See [Authentication](#authentication)

### Portfolio API

#### Create Portfolio

```http
POST /portfolio/
```

| Name        | Type   | Required? | Default | Description           | Example                   |
| ----------- | ------ | --------- | ------- | --------------------- | ------------------------- |
| name        | string | Yes       | -       | Portfolio name        | "Growth Portfolio"        |
| description | string | No        | ""      | Portfolio description | "High-growth tech stocks" |

**Example Request:**

```bash
curl -X POST http://localhost:8000/portfolio/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Growth Portfolio",
    "description": "High-growth tech stocks"
  }'
```

**Example Response:**

```json
{
    "id": 1,
    "name": "Growth Portfolio",
    "description": "High-growth tech stocks",
    "owner_id": 1,
    "created_at": "2025-04-01T10:30:00Z"
}
```

#### List Portfolios

```http
GET /portfolio/
```

**Query Parameters:**

| Name  | Type    | Required? | Default | Description           | Example |
| ----- | ------- | --------- | ------- | --------------------- | ------- |
| skip  | integer | No        | 0       | Records to skip       | 10      |
| limit | integer | No        | 100     | Max records to return | 50      |

**Example Response:**

```json
[
    {
        "id": 1,
        "name": "Growth Portfolio",
        "description": "High-growth tech stocks",
        "owner_id": 1,
        "created_at": "2025-04-01T10:30:00Z"
    }
]
```

#### Get Portfolio

```http
GET /portfolio/{portfolio_id}
```

**Example Response:**

```json
{
    "id": 1,
    "name": "Growth Portfolio",
    "description": "High-growth tech stocks",
    "owner_id": 1,
    "assets": [
        {
            "id": 1,
            "asset_id": 1,
            "quantity": 10.0,
            "purchase_price": 150.0,
            "purchase_date": "2025-03-15T00:00:00Z"
        }
    ],
    "created_at": "2025-04-01T10:30:00Z"
}
```

#### Add Asset to Portfolio

```http
POST /portfolio/assets/
```

| Name           | Type    | Required? | Default | Description             | Example      |
| -------------- | ------- | --------- | ------- | ----------------------- | ------------ |
| portfolio_id   | integer | Yes       | -       | Portfolio ID            | 1            |
| asset_id       | integer | Yes       | -       | Asset ID                | 1            |
| quantity       | number  | Yes       | -       | Number of shares/tokens | 10.5         |
| purchase_price | number  | Yes       | -       | Purchase price per unit | 150.00       |
| purchase_date  | string  | No        | now     | ISO date string         | "2025-04-01" |

#### Get Portfolio Performance

```http
GET /portfolio/performance/{portfolio_id}
```

**Query Parameters:**

| Name   | Type   | Required? | Default | Description | Example                |
| ------ | ------ | --------- | ------- | ----------- | ---------------------- |
| period | string | No        | "1m"    | Time period | "1m", "3m", "6m", "1y" |

**Example Response:**

```json
{
    "portfolio_id": 1,
    "period": "1m",
    "start_value": 100000.0,
    "end_value": 110000.0,
    "return_percentage": 10.0,
    "benchmark_return": 8.5,
    "alpha": 1.5,
    "beta": 0.95,
    "sharpe_ratio": 1.2,
    "volatility": 12.5,
    "max_drawdown": -5.2,
    "data_points": [
        { "date": "2025-03-01", "value": 100000 },
        { "date": "2025-03-15", "value": 105000 },
        { "date": "2025-04-01", "value": 110000 }
    ]
}
```

### Market Data API

#### Get Market Data

```http
GET /market/data/{symbol}
```

| Name     | Type   | Required? | Default | Description   | Example                 |
| -------- | ------ | --------- | ------- | ------------- | ----------------------- |
| symbol   | string | Yes       | -       | Asset symbol  | "AAPL"                  |
| interval | string | No        | "1d"    | Data interval | "1m", "5m", "1h", "1d"  |
| period   | string | No        | "1mo"   | Time period   | "1d", "5d", "1mo", "1y" |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/market/data/AAPL?period=1mo&interval=1d" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Real-time Quote

```http
GET /market/quote/{symbol}
```

**Example Response:**

```json
{
    "symbol": "AAPL",
    "price": 178.5,
    "change": 2.3,
    "change_percent": 1.31,
    "volume": 52000000,
    "timestamp": "2025-04-01T15:30:00Z"
}
```

### AI API

#### Get AI Models

```http
GET /ai/models/
```

| Method | Path                    | Description        | Query/Body params | Auth required | Example request                   |
| ------ | ----------------------- | ------------------ | ----------------- | ------------- | --------------------------------- |
| GET    | `/ai/models/`           | List all AI models | skip, limit       | Yes           | `GET /ai/models/?skip=0&limit=10` |
| GET    | `/ai/models/{model_id}` | Get specific model | Path: model_id    | Yes           | `GET /ai/models/1`                |

**Example Response:**

```json
[
    {
        "id": 1,
        "name": "LSTM Price Predictor",
        "type": "lstm",
        "version": "1.0.0",
        "accuracy": 0.85,
        "status": "active"
    }
]
```

#### Predict Asset Price

```http
POST /ai/predict/asset/{asset_symbol}
```

| Name         | Type    | Required? | Default | Description      | Example         |
| ------------ | ------- | --------- | ------- | ---------------- | --------------- |
| asset_symbol | string  | Yes       | -       | Asset to predict | "AAPL"          |
| days_ahead   | integer | No        | 5       | Days to predict  | 5               |
| model_type   | string  | No        | "lstm"  | Model to use     | "lstm", "garch" |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/ai/predict/asset/AAPL?days_ahead=5&model_type=lstm" \
  -H "Authorization: Bearer $TOKEN"
```

**Example Response:**

```json
{
    "task_id": "abc123-def456",
    "status": "PENDING",
    "message": "Prediction task for AAPL submitted successfully",
    "check_status_endpoint": "/ai/tasks/abc123-def456"
}
```

#### Get Task Status

```http
GET /ai/tasks/{task_id}
```

**Example Response (Pending):**

```json
{
    "task_id": "abc123-def456",
    "status": "PENDING",
    "task_type": "asset_price_prediction",
    "created_at": "2025-04-01T10:30:00Z"
}
```

**Example Response (Complete):**

```json
{
    "task_id": "abc123-def456",
    "status": "SUCCESS",
    "task_type": "asset_price_prediction",
    "created_at": "2025-04-01T10:30:00Z",
    "result": {
        "symbol": "AAPL",
        "predictions": [179.5, 180.2, 181.0, 182.5, 183.2],
        "confidence": 0.85,
        "model": "lstm"
    }
}
```

#### Sentiment Analysis

```http
POST /ai/sentiment/asset/{asset_symbol}
```

| Name         | Type   | Required? | Default | Description  | Example             |
| ------------ | ------ | --------- | ------- | ------------ | ------------------- |
| asset_symbol | string | Yes       | -       | Asset symbol | "TSLA"              |
| sources      | array  | No        | null    | Data sources | ["news", "twitter"] |

#### Portfolio Optimization

```http
POST /ai/optimize/portfolio/{portfolio_id}
```

| Name           | Type    | Required? | Default | Description              | Example               |
| -------------- | ------- | --------- | ------- | ------------------------ | --------------------- |
| portfolio_id   | integer | Yes       | -       | Portfolio ID             | 1                     |
| risk_tolerance | number  | No        | 0.5     | Risk level (0-1)         | 0.5                   |
| constraints    | object  | No        | {}      | Optimization constraints | {"max_position": 0.3} |

#### Portfolio Risk Analysis

```http
POST /ai/risk/portfolio/{portfolio_id}
```

**Example Response:**

```json
{
    "task_id": "xyz789-abc123",
    "status": "PENDING",
    "message": "Portfolio risk analysis task submitted successfully"
}
```

### Blockchain API

#### Get Token Balance

```http
GET /blockchain/balance/{address}
```

| Name    | Type   | Required? | Default    | Description        | Example                                     |
| ------- | ------ | --------- | ---------- | ------------------ | ------------------------------------------- |
| address | string | Yes       | -          | Wallet address     | "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb" |
| network | string | No        | "ethereum" | Blockchain network | "ethereum", "polygon"                       |

#### Deploy Tokenized Asset

```http
POST /blockchain/deploy-asset
```

| Name           | Type   | Required? | Default | Description           | Example             |
| -------------- | ------ | --------- | ------- | --------------------- | ------------------- |
| name           | string | Yes       | -       | Token name            | "Apple Stock Token" |
| symbol         | string | Yes       | -       | Token symbol          | "AAPL-T"            |
| asset_symbol   | string | Yes       | -       | Underlying asset      | "AAPL"              |
| initial_supply | number | Yes       | -       | Initial token supply  | 1000000             |
| asset_value    | number | Yes       | -       | Initial value (cents) | 15000               |

#### Get Asset Details

```http
GET /blockchain/asset/{contract_address}
```

**Example Response:**

```json
{
    "contract_address": "0x...",
    "asset_symbol": "AAPL",
    "asset_name": "Apple Inc.",
    "asset_type": "stock",
    "asset_value": 15000,
    "trading_enabled": true,
    "total_supply": 1000000
}
```

### Admin API

#### Get System Stats

```http
GET /admin/stats
```

**Auth Required:** Admin role

**Example Response:**

```json
{
    "total_users": 1234,
    "total_portfolios": 567,
    "total_assets": 89,
    "total_transactions": 45678,
    "system_uptime": 345600
}
```

## Response Formats

### Success Response

```json
{
    "id": 1,
    "name": "Resource Name",
    "created_at": "2025-04-01T10:30:00Z"
}
```

### Error Response

```json
{
    "detail": "Error message describing what went wrong"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning               | Description                             |
| ---- | --------------------- | --------------------------------------- |
| 200  | OK                    | Request successful                      |
| 201  | Created               | Resource created successfully           |
| 204  | No Content            | Request successful, no content returned |
| 400  | Bad Request           | Invalid request parameters              |
| 401  | Unauthorized          | Authentication required                 |
| 403  | Forbidden             | Insufficient permissions                |
| 404  | Not Found             | Resource not found                      |
| 422  | Unprocessable Entity  | Validation error                        |
| 429  | Too Many Requests     | Rate limit exceeded                     |
| 500  | Internal Server Error | Server error                            |

### Error Response Format

```json
{
    "detail": "Detailed error message",
    "type": "error_type",
    "code": "ERROR_CODE"
}
```

**Example:**

```json
{
    "detail": "Portfolio not found",
    "type": "not_found",
    "code": "PORTFOLIO_NOT_FOUND"
}
```

## Rate Limiting

| Limit Type       | Value        | Window   |
| ---------------- | ------------ | -------- |
| **Per User**     | 100 requests | 1 minute |
| **Burst**        | 200 requests | 1 minute |
| **AI Endpoints** | 20 requests  | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1680345600
```

### Rate Limit Exceeded

**Response:** `429 Too Many Requests`

```json
{
    "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## Webhooks (Coming Soon)

Subscribe to events for real-time updates:

- Portfolio value changes
- AI prediction completions
- Blockchain transactions
- Risk alerts

## SDK Support

Official SDKs available for:

- Python: `pip install quantumnest-sdk`
- JavaScript/TypeScript: `npm install @quantumnest/sdk`
- Go: `go get github.com/quantumnest/sdk-go`

---

**Interactive API Documentation**: http://localhost:8000/docs  
**Alternative Documentation**: http://localhost:8000/redoc
