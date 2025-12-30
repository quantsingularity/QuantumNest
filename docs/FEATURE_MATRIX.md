# Feature Matrix

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [AI & Machine Learning Features](#ai--machine-learning-features)
- [Blockchain Features](#blockchain-features)
- [API Features](#api-features)
- [Infrastructure Features](#infrastructure-features)

## Overview

This document provides a comprehensive feature matrix for QuantumNest platform.

## Core Features

| Feature                     | Short description                       | Module / File                       | CLI flag / API              | Example (path)                                                       | Notes                  |
| --------------------------- | --------------------------------------- | ----------------------------------- | --------------------------- | -------------------------------------------------------------------- | ---------------------- |
| **User Authentication**     | JWT-based secure authentication         | `code/backend/app/auth/`            | `POST /users/login`         | [examples/auth-example.md](examples/auth-example.md)                 | Supports Bearer tokens |
| **Portfolio Management**    | Create and manage investment portfolios | `code/backend/app/api/portfolio.py` | `POST /portfolio/`          | [examples/portfolio-management.md](examples/portfolio-management.md) | Real-time tracking     |
| **Market Data Integration** | Real-time and historical market data    | `code/backend/app/api/market.py`    | `GET /market/data/{symbol}` | [examples/market-data.md](examples/market-data.md)                   | Multiple data sources  |
| **Web Dashboard**           | Modern responsive web interface         | `web-frontend/src/`                 | -                           | -                                                                    | Next.js/TypeScript     |
| **Mobile App**              | Full-featured mobile application        | `mobile-frontend/src/`              | -                           | -                                                                    | React Native           |

## AI & Machine Learning Features

| Feature                    | Short description                      | Module / File                                  | CLI flag / API                                            | Example (path)                                                       | Notes                    |
| -------------------------- | -------------------------------------- | ---------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------ |
| **LSTM Price Prediction**  | Time series price forecasting          | `code/backend/app/ai/lstm_model.py`            | `POST /ai/predict/asset/{symbol}`                         | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Async task processing    |
| **Advanced LSTM**          | Enhanced LSTM with attention mechanism | `code/backend/app/ai/advanced_lstm_model.py`   | `POST /ai/predict/asset/` with `model_type=advanced_lstm` | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Higher accuracy          |
| **GARCH Volatility Model** | Volatility forecasting                 | `code/backend/app/ai/garch_model.py`           | `POST /ai/predict/asset/` with `model_type=garch`         | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Risk assessment          |
| **Sentiment Analysis**     | NLP-based market sentiment             | `code/backend/app/ai/sentiment_analyzer.py`    | `POST /ai/sentiment/asset/{symbol}`                       | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Multi-source analysis    |
| **Portfolio Optimization** | AI-powered portfolio allocation        | `code/backend/app/ai/portfolio_optimizer.py`   | `POST /ai/optimize/portfolio/{id}`                        | [examples/portfolio-management.md](examples/portfolio-management.md) | Risk-adjusted returns    |
| **Anomaly Detection**      | Unusual pattern identification         | `code/backend/app/ai/anomaly_detection.py`     | Available in portfolio analysis                           | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Real-time alerts         |
| **Risk Profiler**          | User risk tolerance assessment         | `code/backend/app/ai/risk_profiler.py`         | `POST /ai/risk/portfolio/{id}`                            | [examples/portfolio-management.md](examples/portfolio-management.md) | Personalized             |
| **Recommendation Engine**  | Personalized investment suggestions    | `code/backend/app/ai/recommendation_engine.py` | `POST /ai/recommendations/market`                         | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | ML-based                 |
| **Financial Advisor**      | AI financial advisory                  | `code/backend/app/ai/financial_advisor.py`     | Available via recommendations API                         | [examples/ai-model-usage.md](examples/ai-model-usage.md)             | Context-aware            |
| **Fraud Detection**        | Transaction anomaly detection          | `code/backend/app/ai/fraud_detection.py`       | Automatic on transactions                                 | -                                                                    | Security feature         |
| **PCA Analyzer**           | Principal component analysis           | `code/backend/app/ai/pca_analyzer.py`          | Available in portfolio analytics                          | [examples/portfolio-management.md](examples/portfolio-management.md) | Dimensionality reduction |

## Blockchain Features

| Feature                        | Short description             | Module / File                                     | CLI flag / API                  | Example (path)                                                           | Notes                     |
| ------------------------------ | ----------------------------- | ------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------ | ------------------------- |
| **Tokenized Assets**           | ERC-20 tokenization of assets | `code/blockchain/contracts/TokenizedAsset.sol`    | `POST /blockchain/deploy-asset` | [examples/blockchain-integration.md](examples/blockchain-integration.md) | Fractional ownership      |
| **Portfolio Manager Contract** | On-chain portfolio management | `code/blockchain/contracts/PortfolioManager.sol`  | Available via blockchain API    | [examples/blockchain-integration.md](examples/blockchain-integration.md) | Smart contract automation |
| **Trading Platform**           | Decentralized trading         | `code/blockchain/contracts/TradingPlatform.sol`   | Available via blockchain API    | [examples/blockchain-integration.md](examples/blockchain-integration.md) | DEX integration           |
| **DeFi Integration**           | DeFi protocol connectivity    | `code/blockchain/contracts/DeFiIntegration.sol`   | Available via blockchain API    | [examples/blockchain-integration.md](examples/blockchain-integration.md) | Yield farming support     |
| **Multi-Chain Support**        | Ethereum, Polygon, BSC        | `code/backend/app/services/blockchain_service.py` | `network` parameter in APIs     | [examples/blockchain-integration.md](examples/blockchain-integration.md) | Cross-chain compatible    |
| **Wallet Integration**         | MetaMask and Web3 support     | `web-frontend/src/utils/web3.ts`                  | -                               | -                                                                        | Browser extension         |

## API Features

| Feature                   | Short description             | Module / File                               | CLI flag / API                | Example (path)                                           | Notes                |
| ------------------------- | ----------------------------- | ------------------------------------------- | ----------------------------- | -------------------------------------------------------- | -------------------- |
| **REST API**              | FastAPI-based REST endpoints  | `code/backend/app/main.py`                  | All `/api/*` endpoints        | [API.md](API.md)                                         | OpenAPI/Swagger      |
| **JWT Authentication**    | Secure token-based auth       | `code/backend/app/auth/authentication.py`   | `POST /users/login`           | [examples/auth-example.md](examples/auth-example.md)     | 30-minute expiry     |
| **Rate Limiting**         | Request throttling            | `code/backend/app/middleware/rate_limit.py` | Automatic                     | -                                                        | 100 req/min default  |
| **CORS Support**          | Cross-origin resource sharing | `code/backend/app/main.py`                  | Configured via `CORS_ORIGINS` | [CONFIGURATION.md](CONFIGURATION.md)                     | Customizable origins |
| **Async Task Processing** | Celery background tasks       | `code/backend/app/workers/`                 | All `/ai/*` endpoints         | [examples/ai-model-usage.md](examples/ai-model-usage.md) | Redis-backed         |
| **WebSocket Support**     | Real-time data streaming      | `code/backend/app/api/websocket.py`         | `ws://localhost:8000/ws`      | -                                                        | Live updates         |
| **API Documentation**     | Interactive Swagger UI        | Auto-generated                              | `/docs`, `/redoc`             | -                                                        | OpenAPI 3.0          |

## Infrastructure Features

| Feature                     | Short description           | Module / File                              | CLI flag / API                | Example (path)                     | Notes                  |
| --------------------------- | --------------------------- | ------------------------------------------ | ----------------------------- | ---------------------------------- | ---------------------- |
| **Docker Containerization** | Containerized deployment    | `Dockerfile`, `docker-compose.yml`         | `docker-compose up`           | [INSTALLATION.md](INSTALLATION.md) | Production-ready       |
| **Kubernetes Support**      | K8s orchestration           | `infrastructure/kubernetes/`               | `kubectl apply -f`            | -                                  | Scalable deployment    |
| **Terraform IaC**           | Infrastructure as Code      | `infrastructure/terraform/`                | `terraform apply`             | -                                  | Multi-cloud support    |
| **Ansible Automation**      | Configuration management    | `infrastructure/ansible/`                  | `ansible-playbook`            | -                                  | Automated provisioning |
| **CI/CD Pipeline**          | GitHub Actions automation   | `.github/workflows/`                       | Automatic on push             | -                                  | Test + deploy          |
| **Monitoring**              | Prometheus + Grafana        | `infrastructure/monitoring/`               | -                             | -                                  | Metrics and alerts     |
| **Logging**                 | Centralized log aggregation | `infrastructure/monitoring/elasticsearch/` | `./scripts/log_aggregator.sh` | [CLI.md](CLI.md)                   | ELK stack              |
| **Backup & Recovery**       | Automated backups           | `infrastructure/backup-recovery/`          | -                             | -                                  | Database + K8s         |
| **Security Policies**       | IAM and network policies    | `infrastructure/security/`                 | -                             | -                                  | Zero-trust model       |
