# CLI Reference

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Global Options](#global-options)
- [Commands](#commands)
- [Script Usage](#script-usage)
- [Examples](#examples)

## Overview

QuantumNest provides several command-line scripts for development, deployment, and maintenance tasks.

## Installation

CLI scripts are included in the repository:

```bash
git clone https://github.com/quantsingularity/QuantumNest.git
cd QuantumNest
chmod +x scripts/*.sh
```

## Global Options

Most scripts support these common options:

| Option      | Description             | Example                 |
| ----------- | ----------------------- | ----------------------- |
| `--help`    | Show help message       | `./script.sh --help`    |
| `--verbose` | Enable verbose output   | `./script.sh --verbose` |
| `--dry-run` | Show what would be done | `./script.sh --dry-run` |

## Commands

### Setup and Environment

| Command                    | Arguments                                           | Description                  | Example                           |
| -------------------------- | --------------------------------------------------- | ---------------------------- | --------------------------------- |
| `setup_quantumnest_env.sh` | None                                                | Initial environment setup    | `./setup_quantumnest_env.sh`      |
| `run_quantumnest.sh`       | None                                                | Start all services           | `./run_quantumnest.sh`            |
| `env_manager.sh`           | `status\|template\|sync\|backup\|restore\|validate` | Manage environment variables | `./scripts/env_manager.sh status` |

#### setup_quantumnest_env.sh

**Description**: Automated environment setup for QuantumNest

**Usage:**

```bash
./setup_quantumnest_env.sh
```

**What it does:**

- Checks system dependencies (Node.js, Python, Docker)
- Creates Python virtual environment
- Installs backend dependencies
- Installs frontend dependencies
- Installs blockchain dependencies
- Generates environment files
- Initializes databases

**Example Output:**

```
🚀 QuantumNest Environment Setup
================================

✓ Checking dependencies...
  ✓ Node.js v18.0.0 found
  ✓ Python 3.10.0 found
  ✓ Docker 20.10.0 found

✓ Setting up backend...
  ✓ Created virtual environment
  ✓ Installed 87 packages

✓ Setting up frontend...
  ✓ Installed 245 packages

Setup complete! Run ./run_quantumnest.sh to start.
```

#### run_quantumnest.sh

**Description**: Start all QuantumNest services

**Usage:**

```bash
./run_quantumnest.sh [options]
```

**Options:**

- `--backend-only` - Start only backend API
- `--frontend-only` - Start only frontend
- `--no-celery` - Skip Celery worker

**Example:**

```bash
# Start all services
./run_quantumnest.sh

# Start only backend
./run_quantumnest.sh --backend-only
```

#### env_manager.sh

**Description**: Manage environment variables across components

**Usage:**

```bash
./scripts/env_manager.sh [COMMAND] [OPTIONS]
```

**Commands:**

| Command               | Description                   | Example                                     |
| --------------------- | ----------------------------- | ------------------------------------------- |
| `status`              | Check environment file status | `./scripts/env_manager.sh status`           |
| `template`            | Generate template .env files  | `./scripts/env_manager.sh template`         |
| `sync`                | Synchronize common variables  | `./scripts/env_manager.sh sync`             |
| `backup`              | Backup all environment files  | `./scripts/env_manager.sh backup`           |
| `restore [TIMESTAMP]` | Restore from backup           | `./scripts/env_manager.sh restore 20250401` |
| `validate`            | Validate environment files    | `./scripts/env_manager.sh validate`         |

**Example:**

```bash
# Check status
./scripts/env_manager.sh status

# Output:
# Component: backend
#   Status: ✓ .env file exists
#   Variables: 42 defined
#
# Component: frontend
#   Status: ✗ .env file missing
#   Variables: 0 defined

# Generate templates
./scripts/env_manager.sh template

# Validate configuration
./scripts/env_manager.sh validate
```

### Build and Test

| Command                 | Arguments     | Description          | Example                              |
| ----------------------- | ------------- | -------------------- | ------------------------------------ |
| `build.sh`              | None          | Build all components | `./scripts/build.sh`                 |
| `run_all_tests.sh`      | `[component]` | Run test suites      | `./scripts/run_all_tests.sh backend` |
| `lint-all.sh`           | None          | Run linters          | `./scripts/lint-all.sh`              |
| `dependency_checker.sh` | None          | Check dependencies   | `./scripts/dependency_checker.sh`    |

#### build.sh

**Description**: Build all QuantumNest components

**Usage:**

```bash
./scripts/build.sh [options]
```

**Options:**

- `--clean` - Clean before building
- `--production` - Production build
- `--component=NAME` - Build specific component

**Example:**

```bash
# Build all
./scripts/build.sh

# Clean build
./scripts/build.sh --clean

# Build frontend only
./scripts/build.sh --component=frontend
```

#### run_all_tests.sh

**Description**: Execute all test suites

**Usage:**

```bash
./scripts/run_all_tests.sh [component]
```

**Arguments:**

- `backend` - Run backend tests only
- `frontend` - Run frontend tests only
- `blockchain` - Run smart contract tests only

**Example:**

```bash
# Run all tests
./scripts/run_all_tests.sh

# Run backend tests only
./scripts/run_all_tests.sh backend

# Output:
# ================================
# Running Backend Tests
# ================================
#
# test_user_creation.py ✓
# test_portfolio_api.py ✓
# test_ai_models.py ✓
#
# 87 tests passed, 0 failed
```

#### lint-all.sh

**Description**: Run code linters for all components

**Usage:**

```bash
./scripts/lint-all.sh [options]
```

**Options:**

- `--fix` - Automatically fix issues
- `--strict` - Fail on warnings

**Example:**

```bash
# Check all code
./scripts/lint-all.sh

# Fix issues automatically
./scripts/lint-all.sh --fix
```

#### dependency_checker.sh

**Description**: Check and report on dependencies

**Usage:**

```bash
./scripts/dependency_checker.sh [options]
```

**Options:**

- `--update` - Check for updates
- `--security` - Security vulnerability scan
- `--report` - Generate detailed report

**Example:**

```bash
# Check dependencies
./scripts/dependency_checker.sh

# Check for security vulnerabilities
./scripts/dependency_checker.sh --security

# Output:
# Checking backend dependencies...
#   ✓ fastapi 0.104.1 (latest: 0.105.0)
#   ⚠ requests 2.28.0 (security update available: 2.31.0)
#   ✓ sqlalchemy 2.0.21 (latest)
#
# Security Issues Found: 1
# Recommendation: Update requests package
```

### Logging and Monitoring

| Command             | Arguments                                | Description | Example                             |
| ------------------- | ---------------------------------------- | ----------- | ----------------------------------- |
| `log_aggregator.sh` | `collect\|watch\|clean\|search\|analyze` | Manage logs | `./scripts/log_aggregator.sh watch` |

#### log_aggregator.sh

**Description**: Collect and analyze logs from all components

**Usage:**

```bash
./scripts/log_aggregator.sh [COMMAND] [OPTIONS]
```

**Commands:**

| Command         | Description                      | Example                                      |
| --------------- | -------------------------------- | -------------------------------------------- |
| `collect`       | Collect logs from all components | `./scripts/log_aggregator.sh collect`        |
| `watch`         | Watch logs in real-time          | `./scripts/log_aggregator.sh watch`          |
| `clean`         | Clean old log files              | `./scripts/log_aggregator.sh clean`          |
| `search [term]` | Search across all logs           | `./scripts/log_aggregator.sh search "error"` |
| `analyze`       | Analyze logs for issues          | `./scripts/log_aggregator.sh analyze`        |

**Example:**

```bash
# Collect all logs
./scripts/log_aggregator.sh collect

# Watch logs in real-time
./scripts/log_aggregator.sh watch

# Search for errors
./scripts/log_aggregator.sh search "error"

# Output:
# Searching for 'error' in logs...
#
# backend/app.log:
#   2025-04-01 10:30:15 ERROR - Database connection failed
#   2025-04-01 10:31:20 ERROR - Timeout in AI prediction
#
# frontend/console.log:
#   2025-04-01 10:32:05 ERROR - Failed to fetch portfolio data
#
# Found 3 occurrences

# Analyze logs
./scripts/log_aggregator.sh analyze

# Output:
# Log Analysis Summary
# ====================
# Total Errors: 15
# Total Warnings: 42
#
# Top Errors:
#   1. Database timeout (8 occurrences)
#   2. API rate limit (4 occurrences)
#   3. Invalid token (3 occurrences)
```

## Script Usage

### Development Workflow

```bash
# 1. Initial setup
./setup_quantumnest_env.sh

# 2. Start development
./run_quantumnest.sh

# 3. Run tests during development
./scripts/run_all_tests.sh

# 4. Check code quality
./scripts/lint-all.sh --fix

# 5. View logs
./scripts/log_aggregator.sh watch
```

### Deployment Workflow

```bash
# 1. Validate environment
./scripts/env_manager.sh validate

# 2. Check dependencies
./scripts/dependency_checker.sh --security

# 3. Run tests
./scripts/run_all_tests.sh

# 4. Build for production
./scripts/build.sh --production

# 5. Backup environment
./scripts/env_manager.sh backup
```

### Maintenance Workflow

```bash
# 1. Check system status
./scripts/dependency_checker.sh

# 2. Analyze logs for issues
./scripts/log_aggregator.sh analyze

# 3. Clean old logs
./scripts/log_aggregator.sh clean

# 4. Update dependencies (if needed)
./scripts/dependency_checker.sh --update
```

## Examples

### Example 1: Fresh Installation

```bash
# Clone and setup
git clone https://github.com/quantsingularity/QuantumNest.git
cd QuantumNest
./setup_quantumnest_env.sh

# Start application
./run_quantumnest.sh

# In another terminal, verify services
curl http://localhost:8000/health
curl http://localhost:3000
```

### Example 2: Running Tests Before Deployment

```bash
# Validate environment
./scripts/env_manager.sh validate

# Check for security issues
./scripts/dependency_checker.sh --security

# Run all tests
./scripts/run_all_tests.sh

# If all pass, build
./scripts/build.sh --production
```

### Example 3: Debugging Issues

```bash
# Search logs for errors
./scripts/log_aggregator.sh search "error"

# Watch logs in real-time
./scripts/log_aggregator.sh watch

# Analyze patterns
./scripts/log_aggregator.sh analyze
```

### Example 4: Environment Management

```bash
# Backup current environment
./scripts/env_manager.sh backup

# Make changes to .env files
vim code/backend/.env

# Validate changes
./scripts/env_manager.sh validate

# If issues, restore backup
./scripts/env_manager.sh restore 20250401_103000
```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/*.sh
```

### Python Virtual Environment Not Found

```bash
cd code/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Script Fails with "Command Not Found"

Ensure you're running from repository root:

```bash
cd /path/to/QuantumNest
./scripts/script_name.sh
```

---

**See Also:**

- [Installation Guide](INSTALLATION.md)
- [Configuration](CONFIGURATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)
