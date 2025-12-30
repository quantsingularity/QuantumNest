# Installation Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Options](#installation-options)
- [Quick Start](#quick-start)
- [Manual Installation](#manual-installation)
- [Docker Installation](#docker-installation)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Verification](#verification)
- [Next Steps](#next-steps)

## Prerequisites

Before installing QuantumNest, ensure your system meets the following requirements:

| Requirement    | Minimum Version | Recommended Version | Notes                    |
| -------------- | --------------- | ------------------- | ------------------------ |
| **Node.js**    | 14.0            | 18.0+               | Required for frontend    |
| **Python**     | 3.8             | 3.10+               | Required for backend     |
| **Docker**     | 20.10           | Latest              | Optional but recommended |
| **PostgreSQL** | 12.0            | 14.0+               | Or use Docker            |
| **Redis**      | 6.0             | Latest              | For caching and Celery   |
| **Git**        | 2.0+            | Latest              | For cloning repository   |

### Additional Requirements

- **For Blockchain Development**: MetaMask or compatible Ethereum wallet
- **For AI Models**: CUDA-compatible GPU (optional, improves performance)
- **Disk Space**: Minimum 5GB free space
- **Memory**: Minimum 8GB RAM (16GB recommended)

## Installation Options

| OS / Platform              | Recommended Install Command  | Notes                           |
| -------------------------- | ---------------------------- | ------------------------------- |
| **Linux (Ubuntu/Debian)**  | `./setup_quantumnest_env.sh` | Automated setup script          |
| **macOS**                  | `./setup_quantumnest_env.sh` | Requires Homebrew               |
| **Windows**                | Use WSL2 + setup script      | Native Windows support limited  |
| **Docker (All Platforms)** | `docker-compose up`          | Recommended for production      |
| **Cloud (AWS/GCP/Azure)**  | Terraform scripts available  | See `infrastructure/terraform/` |

## Quick Start

The fastest way to get started with QuantumNest:

```bash
# 1. Clone the repository
git clone https://github.com/abrar2030/QuantumNest.git
cd QuantumNest

# 2. Run the automated setup script
chmod +x setup_quantumnest_env.sh
./setup_quantumnest_env.sh

# 3. Start the application
./run_quantumnest.sh

# 4. Access the application
# Web Frontend: http://localhost:3000
# API Backend: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

The setup script will:

- Check for required dependencies
- Install missing dependencies (with your permission)
- Set up Python virtual environment
- Install Python packages
- Install Node.js packages for frontend and blockchain
- Configure environment variables
- Initialize databases

## Manual Installation

If you prefer manual installation or the setup script fails:

### Step 1: Clone Repository

```bash
git clone https://github.com/abrar2030/QuantumNest.git
cd QuantumNest
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd code/backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m alembic upgrade head
```

### Step 3: Web Frontend Setup

```bash
# Navigate to web frontend directory
cd ../../web-frontend

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Step 4: Blockchain Setup

```bash
# Navigate to blockchain directory
cd ../code/blockchain

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your blockchain configuration

# Compile smart contracts
npx hardhat compile
```

### Step 5: Start Services

```bash
# Terminal 1 - Start Backend
cd code/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Start Frontend
cd web-frontend
npm run dev

# Terminal 3 - Start Celery Worker (for AI tasks)
cd code/backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 4 - Start Redis (if not using Docker)
redis-server
```

## Docker Installation

Docker provides the easiest way to run QuantumNest with all dependencies:

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/abrar2030/QuantumNest.git
cd QuantumNest

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Individual Containers

```bash
# Build backend image
docker build -t quantumnest-backend -f code/backend/Dockerfile .

# Build frontend image
docker build -t quantumnest-frontend -f web-frontend/Dockerfile .

# Run containers
docker run -d --name qn-backend -p 8000:8000 quantumnest-backend
docker run -d --name qn-frontend -p 3000:3000 quantumnest-frontend
```

### Docker Services

The Docker Compose setup includes:

- **Backend API** (port 8000)
- **Web Frontend** (port 3000)
- **PostgreSQL Database** (port 5432)
- **Redis Cache** (port 6379)
- **Celery Worker** (background tasks)

## Platform-Specific Instructions

### Ubuntu/Debian Linux

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv nodejs npm \
                    postgresql postgresql-contrib redis-server git curl

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Follow Quick Start instructions
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 node postgresql redis git

# Start services
brew services start postgresql
brew services start redis

# Follow Quick Start instructions
```

### Windows (WSL2)

```bash
# Install WSL2 and Ubuntu from Microsoft Store
# Open Ubuntu terminal

# Update packages
sudo apt update && sudo apt upgrade -y

# Follow Ubuntu installation instructions above
```

## Verification

After installation, verify that all components are working:

### 1. Check Backend API

```bash
curl http://localhost:8000/health
# Expected output: {"status":"healthy"}
```

### 2. Check Frontend

Open browser and navigate to:

```
http://localhost:3000
```

You should see the QuantumNest landing page.

### 3. Check API Documentation

```
http://localhost:8000/docs
```

Interactive Swagger UI should load with all API endpoints.

### 4. Run Tests

```bash
# Backend tests
cd code/backend
source venv/bin/activate
pytest

# Frontend tests
cd web-frontend
npm test
```

### 5. Check Database Connection

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# List databases
\l

# You should see quantumnest database
```

## Next Steps

After successful installation:

1. **Configure Environment Variables**: Review and update `.env` files
    - See [Configuration Guide](CONFIGURATION.md)

2. **Set Up Blockchain Wallet**:
    - Install MetaMask browser extension
    - Configure for testnet (Goerli)

3. **Explore the API**:
    - Read [API Documentation](API.md)
    - Try example requests in [Examples](examples/)

4. **Read Usage Guide**:
    - See [Usage Guide](USAGE.md) for common workflows

5. **Deploy Smart Contracts** (for development):
    ```bash
    cd code/blockchain
    npx hardhat run scripts/deploy.js --network goerli
    ```

## Troubleshooting

### Common Issues

**Port Already in Use**

```bash
# Find process using port
lsof -i :8000  # or :3000

# Kill process
kill -9 <PID>
```

**Python Virtual Environment Not Found**

```bash
# Ensure you're in the correct directory
cd code/backend

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Node Module Installation Fails**

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Database Connection Error**

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS

# Reset database (WARNING: deletes all data)
dropdb quantumnest
createdb quantumnest
```

For more troubleshooting help, see [Troubleshooting Guide](TROUBLESHOOTING.md).

## Updating QuantumNest

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update backend dependencies
cd code/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd ../../web-frontend
npm install

# Run database migrations
cd ../code/backend
alembic upgrade head

# Restart services
```

## Uninstallation

To remove QuantumNest:

```bash
# Stop all services
docker-compose down  # if using Docker

# Remove repository
cd ..
rm -rf QuantumNest

# Remove Docker volumes (optional)
docker volume prune

# Remove databases (optional)
dropdb quantumnest
```

---

**Need Help?** See [Troubleshooting Guide](TROUBLESHOOTING.md) or [open an issue](https://github.com/abrar2030/QuantumNest/issues).
