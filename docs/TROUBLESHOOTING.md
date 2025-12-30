# Troubleshooting Guide

## Table of Contents

- [Common Issues](#common-issues)
- [Installation Problems](#installation-problems)
- [Runtime Errors](#runtime-errors)
- [API Issues](#api-issues)
- [Database Issues](#database-issues)
- [Frontend Issues](#frontend-issues)
- [Blockchain Issues](#blockchain-issues)
- [Performance Issues](#performance-issues)

## Common Issues

### Port Already in Use

**Problem**: `Address already in use` error when starting services.

**Solution**:

```bash
# Find process using port
lsof -i :8000  # or :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=8001 uvicorn app.main:app --reload
```

### Module Not Found

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:

```bash
# Ensure virtual environment is activated
cd code/backend
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

### Database Connection Failed

**Problem**: `Connection refused` or `Database connection error`

**Solution**:

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Test connection
psql -U postgres -h localhost

# Check DATABASE_URL in .env
echo $DATABASE_URL

# Reset database
dropdb quantumnest
createdb quantumnest
alembic upgrade head
```

## Installation Problems

### Setup Script Fails

**Problem**: `./setup_quantumnest_env.sh` fails midway.

**Solution**:

```bash
# Check prerequisites
node --version  # Should be 14+
python3 --version  # Should be 3.8+
docker --version

# Run manual installation
# See INSTALLATION.md for manual steps

# Check logs
cat setup.log
```

### pip Install Fails

**Problem**: Packages fail to install.

**Solution**:

```bash
# Update pip
pip install --upgrade pip

# Install build tools
sudo apt install python3-dev build-essential  # Ubuntu
brew install python@3.10  # macOS

# Try installing problematic package individually
pip install package-name --verbose
```

### npm Install Fails

**Problem**: `npm install` fails with errors.

**Solution**:

```bash
# Clear cache
npm cache clean --force

# Delete lock file and node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try alternative package manager
pnpm install  # or yarn install
```

## Runtime Errors

### JWT Token Invalid

**Problem**: `401 Unauthorized: Could not validate credentials`

**Solution**:

```bash
# Check token hasn't expired (30 min default)
# Login again to get new token

# Verify SECRET_KEY matches between env and code
grep SECRET_KEY code/backend/.env

# Ensure Authorization header format:
# Authorization: Bearer <token>
```

### Celery Worker Not Starting

**Problem**: AI tasks remain PENDING indefinitely.

**Solution**:

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Check Celery worker
cd code/backend
celery -A app.workers.celery_app inspect active

# Restart worker
celery -A app.workers.celery_app worker --loglevel=info

# Check logs
tail -f celery.log
```

### CORS Error

**Problem**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**:

```bash
# Update CORS_ORIGINS in backend .env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Or allow all (development only)
CORS_ORIGINS=*

# Restart backend
```

## API Issues

### 404 Not Found

**Problem**: API endpoint returns 404.

**Solution**:

```bash
# Check API is running
curl http://localhost:8000/health

# Verify endpoint URL
curl http://localhost:8000/docs  # View all endpoints

# Check route registration in app/main.py
```

### Rate Limit Exceeded

**Problem**: `429 Too Many Requests`

**Solution**:

```bash
# Wait 60 seconds and retry

# Or increase rate limit in .env
RATE_LIMIT_REQUESTS_PER_MINUTE=200

# Or disable rate limiting (development only)
RATE_LIMIT_ENABLED=false
```

### Timeout Error

**Problem**: Request times out.

**Solution**:

```bash
# Increase timeout
REQUEST_TIMEOUT=60  # in .env

# Check server logs for slow queries
tail -f code/backend/app.log

# Optimize database queries
# Add indexes to frequently queried fields
```

## Database Issues

### Migration Failed

**Problem**: `alembic upgrade head` fails.

**Solution**:

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Downgrade one version
alembic downgrade -1

# Try upgrade again
alembic upgrade head

# If stuck, reset database (WARNING: loses data)
dropdb quantumnest && createdb quantumnest
alembic upgrade head
```

### Slow Queries

**Problem**: Database queries are slow.

**Solution**:

```sql
-- Add indexes
CREATE INDEX idx_portfolio_owner ON portfolios(owner_id);
CREATE INDEX idx_portfolio_assets_portfolio ON portfolio_assets(portfolio_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM portfolios WHERE owner_id = 1;

-- Vacuum database
VACUUM ANALYZE;
```

## Frontend Issues

### Build Fails

**Problem**: `npm run build` fails.

**Solution**:

```bash
# Check TypeScript errors
npm run type-check

# Fix linting issues
npm run lint --fix

# Clear .next directory
rm -rf .next

# Rebuild
npm run build
```

### Blank Screen

**Problem**: Frontend loads but shows blank screen.

**Solution**:

```bash
# Check browser console for errors
# Open DevTools (F12)

# Verify API_URL is correct
cat web-frontend/.env.local

# Check API is accessible
curl http://localhost:8000/health

# Clear browser cache and reload
```

### WebSocket Connection Failed

**Problem**: Real-time updates not working.

**Solution**:

```bash
# Check WebSocket URL
WS_URL=ws://localhost:8000/ws

# Verify CORS allows WebSocket
# Check browser network tab for WS connection

# Test WebSocket manually
wscat -c ws://localhost:8000/ws
```

## Blockchain Issues

### Transaction Failed

**Problem**: Blockchain transaction fails.

**Solution**:

```bash
# Check wallet has sufficient balance
# Verify gas price settings
# Confirm network is correct (mainnet/testnet)

# Check contract address is valid
# Verify ABI is up to date
```

### MetaMask Not Connecting

**Problem**: Cannot connect MetaMask wallet.

**Solution**:

```bash
# Ensure MetaMask is installed
# Check correct network is selected
# Refresh page and try again

# Clear MetaMask cache:
# Settings > Advanced > Reset Account
```

## Performance Issues

### High Memory Usage

**Problem**: Backend using excessive memory.

**Solution**:

```bash
# Monitor memory
top -p $(pgrep -f uvicorn)

# Reduce worker count
WORKERS=1  # in .env

# Implement pagination for large queries
# Add caching with Redis
```

### Slow API Response

**Problem**: API endpoints are slow.

**Solution**:

```bash
# Profile code
python -m cProfile code/backend/app/main.py

# Add database indexes
# Implement caching
CACHE_TTL=300  # 5 minutes

# Use async operations
# Optimize AI model loading
```

## Getting Additional Help

### Check Logs

```bash
# Backend logs
tail -f code/backend/app.log

# Frontend logs
npm run dev  # Check console output

# Docker logs
docker-compose logs -f
```

### Enable Debug Mode

```bash
# Backend
DEBUG=true  # in .env

# Frontend
NODE_ENV=development
```

---
