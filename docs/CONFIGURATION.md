# Configuration Guide

## Table of Contents

- [Overview](#overview)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Component Configuration](#component-configuration)
- [Security Configuration](#security-configuration)

## Overview

QuantumNest uses environment variables and configuration files for customization. All sensitive data should be stored in `.env` files (never committed to git).

## Environment Variables

### Core Configuration

| Option        | Type    | Default           | Description                   | Where to set (env/file) |
| ------------- | ------- | ----------------- | ----------------------------- | ----------------------- |
| `ENVIRONMENT` | string  | "development"     | Deployment environment        | .env                    |
| `DEBUG`       | boolean | false             | Enable debug mode             | .env                    |
| `SECRET_KEY`  | string  | _generated_       | JWT secret key (min 32 chars) | .env (required)         |
| `API_KEY`     | string  | "default-api-key" | API authentication key        | .env                    |
| `HOST`        | string  | "0.0.0.0"         | API host address              | .env                    |
| `PORT`        | integer | 8000              | API port number               | .env                    |

### Database Configuration

| Option                  | Type    | Default                      | Description                | Where to set (env/file) |
| ----------------------- | ------- | ---------------------------- | -------------------------- | ----------------------- |
| `DATABASE_URL`          | string  | "sqlite:///./quantumnest.db" | Database connection string | .env (required)         |
| `DATABASE_POOL_SIZE`    | integer | 10                           | Connection pool size       | .env                    |
| `DATABASE_MAX_OVERFLOW` | integer | 20                           | Max pool overflow          | .env                    |
| `DATABASE_POOL_TIMEOUT` | integer | 30                           | Pool timeout (seconds)     | .env                    |

**PostgreSQL Example:**

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/quantumnest
```

### Redis Configuration

| Option           | Type    | Default                    | Description             | Where to set (env/file) |
| ---------------- | ------- | -------------------------- | ----------------------- | ----------------------- |
| `REDIS_URL`      | string  | "redis://localhost:6379/0" | Redis connection string | .env                    |
| `REDIS_HOST`     | string  | "localhost"                | Redis host              | .env                    |
| `REDIS_PORT`     | integer | 6379                       | Redis port              | .env                    |
| `REDIS_PASSWORD` | string  | null                       | Redis password          | .env                    |
| `REDIS_DB`       | integer | 0                          | Redis database number   | .env                    |

### Celery Configuration

| Option                  | Type   | Default                    | Description        | Where to set (env/file) |
| ----------------------- | ------ | -------------------------- | ------------------ | ----------------------- |
| `CELERY_BROKER_URL`     | string | "redis://localhost:6379/0" | Message broker URL | .env                    |
| `CELERY_RESULT_BACKEND` | string | "redis://localhost:6379/0" | Result storage URL | .env                    |
| `CELERY_TIMEZONE`       | string | "UTC"                      | Celery timezone    | .env                    |

### Authentication & Security

| Option                        | Type    | Default | Description               | Where to set (env/file) |
| ----------------------------- | ------- | ------- | ------------------------- | ----------------------- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | 30      | JWT token expiration      | .env                    |
| `PASSWORD_MIN_LENGTH`         | integer | 8       | Minimum password length   | .env                    |
| `MAX_LOGIN_ATTEMPTS`          | integer | 5       | Max failed login attempts | .env                    |
| `LOCKOUT_DURATION_MINUTES`    | integer | 30      | Account lockout duration  | .env                    |
| `ENABLE_TWO_FACTOR_AUTH`      | boolean | false   | Enable 2FA                | .env                    |

### AI & ML Configuration

| Option                  | Type    | Default    | Description                  | Where to set (env/file) |
| ----------------------- | ------- | ---------- | ---------------------------- | ----------------------- |
| `AI_MODELS_DIR`         | string  | "./models" | AI models directory          | .env                    |
| `AI_PREDICTION_TIMEOUT` | integer | 30         | Prediction timeout (seconds) | .env                    |
| `OPENAI_API_KEY`        | string  | null       | OpenAI API key               | .env                    |
| `HUGGINGFACE_API_KEY`   | string  | null       | HuggingFace API key          | .env                    |

### Financial Data APIs

| Option                  | Type    | Default | Description           | Where to set (env/file) |
| ----------------------- | ------- | ------- | --------------------- | ----------------------- |
| `ALPHA_VANTAGE_API_KEY` | string  | null    | Alpha Vantage API key | .env                    |
| `YAHOO_FINANCE_ENABLED` | boolean | true    | Enable Yahoo Finance  | .env                    |
| `QUANDL_API_KEY`        | string  | null    | Quandl API key        | .env                    |
| `IEX_CLOUD_API_KEY`     | string  | null    | IEX Cloud API key     | .env                    |

### Blockchain Configuration

| Option             | Type   | Default                            | Description           | Where to set (env/file) |
| ------------------ | ------ | ---------------------------------- | --------------------- | ----------------------- |
| `ETHEREUM_RPC_URL` | string | "http://localhost:8545"            | Ethereum RPC endpoint | .env                    |
| `POLYGON_RPC_URL`  | string | "https://polygon-rpc.com"          | Polygon RPC endpoint  | .env                    |
| `BSC_RPC_URL`      | string | "https://bsc-dataseed.binance.org" | BSC RPC endpoint      | .env                    |
| `PRIVATE_KEY`      | string | null                               | Wallet private key    | .env (sensitive!)       |

### CORS Configuration

| Option                   | Type    | Default | Description          | Where to set (env/file) |
| ------------------------ | ------- | ------- | -------------------- | ----------------------- |
| `CORS_ORIGINS`           | array   | ["*"]   | Allowed origins      | .env                    |
| `CORS_ALLOW_CREDENTIALS` | boolean | true    | Allow credentials    | .env                    |
| `CORS_ALLOW_METHODS`     | array   | ["*"]   | Allowed HTTP methods | .env                    |

### Rate Limiting

| Option                           | Type    | Default | Description          | Where to set (env/file) |
| -------------------------------- | ------- | ------- | -------------------- | ----------------------- |
| `RATE_LIMIT_ENABLED`             | boolean | true    | Enable rate limiting | .env                    |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | integer | 100     | Requests per minute  | .env                    |
| `RATE_LIMIT_BURST`               | integer | 200     | Burst limit          | .env                    |

### Logging & Monitoring

| Option               | Type    | Default | Description               | Where to set (env/file) |
| -------------------- | ------- | ------- | ------------------------- | ----------------------- |
| `LOG_LEVEL`          | string  | "INFO"  | Logging level             | .env                    |
| `LOG_FILE`           | string  | null    | Log file path             | .env                    |
| `SENTRY_DSN`         | string  | null    | Sentry error tracking     | .env                    |
| `PROMETHEUS_ENABLED` | boolean | false   | Enable Prometheus metrics | .env                    |

## Configuration Files

### Backend (.env)

```bash
# Core
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-min-32-characters-long
API_KEY=your-api-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/quantumnest

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI APIs
OPENAI_API_KEY=sk-...
ALPHA_VANTAGE_API_KEY=your-key

# Blockchain
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
PRIVATE_KEY=your-private-key

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
PASSWORD_MIN_LENGTH=8
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_CHAIN_ID=1
NEXT_PUBLIC_NETWORK_NAME=mainnet
```

### Blockchain (.env)

```bash
PRIVATE_KEY=your-private-key
INFURA_PROJECT_ID=your-infura-project-id
ETHERSCAN_API_KEY=your-etherscan-api-key
GOERLI_RPC_URL=https://goerli.infura.io/v3/YOUR-PROJECT-ID
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
```

## Component Configuration

### Backend API

Configuration file: `code/backend/app/core/config.py`

Customize settings by subclassing `Settings`:

```python
from app.core.config import Settings

class CustomSettings(Settings):
    PROJECT_NAME = "My QuantumNest"
    MAX_LOGIN_ATTEMPTS = 3
```

### Frontend

Configuration file: `web-frontend/next.config.js`

```javascript
module.exports = {
    env: {
        API_URL: process.env.NEXT_PUBLIC_API_URL,
    },
    // ... other config
};
```

## Security Configuration

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Generate strong `SECRET_KEY` (32+ characters)
- [ ] Use HTTPS URLs for all external services
- [ ] Enable rate limiting
- [ ] Configure proper CORS origins (not "\*")
- [ ] Use environment-specific database credentials
- [ ] Enable Sentry error tracking
- [ ] Set up proper logging
- [ ] Never commit `.env` files to git

### Generating Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

## Environment-Specific Configuration

### Development

```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite:///./quantumnest_dev.db
CORS_ORIGINS=*
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/quantumnest
CORS_ORIGINS=https://staging.quantumnest.io
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/quantumnest
CORS_ORIGINS=https://quantumnest.io,https://www.quantumnest.io
RATE_LIMIT_ENABLED=true
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://...@sentry.io/...
```

## Validation

Validate configuration:

```bash
./scripts/env_manager.sh validate
```

## Troubleshooting

### Missing Environment Variables

**Error**: `KeyError: 'SECRET_KEY'`

**Solution**: Ensure `.env` file exists and contains required variables:

```bash
cp .env.example .env
# Edit .env with your values
```

### Database Connection Failed

**Error**: `Database connection error`

**Solution**: Verify DATABASE_URL format and credentials:

```bash
# PostgreSQL format
DATABASE_URL=postgresql://username:password@host:port/database

# SQLite format (development)
DATABASE_URL=sqlite:///./quantumnest.db
```

### Invalid SECRET_KEY

**Error**: `SECRET_KEY must be at least 32 characters long`

**Solution**: Generate a new key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

**See Also:**

- [Installation Guide](INSTALLATION.md)
- [Security Best Practices](../SECURITY.md)
- [Environment Manager Script](CLI.md#env_managersh)
