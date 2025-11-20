import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import redis
from app.ai.fraud_detection import AdvancedFraudDetectionSystem
from app.auth.authentication import AdvancedAuthenticationSystem
from app.auth.authorization import RoleBasedAccessControl

# Import application modules
from app.models.models import Account, Base, Portfolio, Transaction, User
from app.services.market_data_service import MarketDataService
from app.services.trading_service import TradingService
from app.utils.encryption import AdvancedEncryptionManager
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_settings():
    """Test settings configuration"""
    return {
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD": None,
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "API_SECRET_KEY": "test-api-secret-key",
        "API_KEY": "test-api-key",
        "TESTING": True,
        "DEBUG": True,
    }


@pytest.fixture(scope="session")
def test_database():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    yield SessionLocal

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_database):
    """Create database session for test"""
    session = test_database()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.ttl.return_value = 300
    mock_redis.zadd.return_value = True
    mock_redis.zcard.return_value = 0
    mock_redis.zcount.return_value = 0
    mock_redis.zremrangebyscore.return_value = 0
    mock_redis.expire.return_value = True

    return mock_redis


@pytest.fixture
def test_app():
    """Create test Flask application"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"

    return app


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890",
        "date_of_birth": datetime(1990, 1, 1),
        "address": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
        "country": "US",
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create test user in database"""
    user = User(
        email=test_user_data["email"],
        password_hash="hashed_password",
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        phone=test_user_data["phone"],
        date_of_birth=test_user_data["date_of_birth"],
        address=test_user_data["address"],
        city=test_user_data["city"],
        state=test_user_data["state"],
        zip_code=test_user_data["zip_code"],
        country=test_user_data["country"],
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def test_account(db_session, test_user):
    """Create test account"""
    account = Account(
        user_id=test_user.id,
        account_number="TEST123456789",
        account_type="checking",
        balance=10000.00,
        currency="USD",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    return account


@pytest.fixture
def test_portfolio(db_session, test_user):
    """Create test portfolio"""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        description="Test portfolio for testing",
        total_value=50000.00,
        cash_balance=5000.00,
        currency="USD",
        created_at=datetime.utcnow(),
    )

    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    return portfolio


@pytest.fixture
def test_transaction_data():
    """Test transaction data"""
    return {
        "amount": 1000.00,
        "transaction_type": "buy",
        "symbol": "AAPL",
        "quantity": 10,
        "price": 100.00,
        "currency": "USD",
        "description": "Test transaction",
    }


@pytest.fixture
def test_transaction(db_session, test_user, test_account, test_transaction_data):
    """Create test transaction"""
    transaction = Transaction(
        user_id=test_user.id,
        account_id=test_account.id,
        amount=test_transaction_data["amount"],
        transaction_type=test_transaction_data["transaction_type"],
        symbol=test_transaction_data["symbol"],
        quantity=test_transaction_data["quantity"],
        price=test_transaction_data["price"],
        currency=test_transaction_data["currency"],
        description=test_transaction_data["description"],
        status="completed",
        created_at=datetime.utcnow(),
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    return transaction


@pytest.fixture
def auth_system(db_session, mock_redis):
    """Create authentication system for testing"""
    with patch("app.auth.authentication.redis.Redis", return_value=mock_redis):
        return AdvancedAuthenticationSystem(db_session)


@pytest.fixture
def auth_system_real_redis(db_session):
    """Create authentication system with real Redis (for integration tests)"""
    # Skip if Redis is not available
    try:
        redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        redis_client.ping()
    except:
        pytest.skip("Redis not available for integration tests")

    return AdvancedAuthenticationSystem(db_session)


@pytest.fixture
def rbac_system(db_session):
    """Create RBAC system for testing"""
    return RoleBasedAccessControl(db_session)


@pytest.fixture
def encryption_manager():
    """Create encryption manager for testing"""
    return AdvancedEncryptionManager()


@pytest.fixture
def trading_service():
    """Create trading service for testing"""
    return TradingService()


@pytest.fixture
def market_data_service():
    """Create market data service for testing"""
    return MarketDataService()


@pytest.fixture
def fraud_detection_system():
    """Create fraud detection system for testing"""
    return AdvancedFraudDetectionSystem()


@pytest.fixture
def mock_market_data():
    """Mock market data"""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "price": 150.00,
            "change": 2.50,
            "change_percent": 1.69,
            "volume": 1000000,
            "high": 152.00,
            "low": 148.00,
            "open": 149.00,
            "close": 150.00,
            "timestamp": datetime.utcnow(),
        },
        "GOOGL": {
            "symbol": "GOOGL",
            "price": 2500.00,
            "change": -10.00,
            "change_percent": -0.40,
            "volume": 500000,
            "high": 2520.00,
            "low": 2490.00,
            "open": 2510.00,
            "close": 2500.00,
            "timestamp": datetime.utcnow(),
        },
    }


@pytest.fixture
def sample_training_data():
    """Sample training data for ML models"""
    import numpy as np
    import pandas as pd

    # Generate sample transaction data
    np.random.seed(42)
    n_samples = 1000

    data = {
        "user_id": np.random.randint(1, 100, n_samples),
        "amount": np.random.exponential(1000, n_samples),
        "transaction_type": np.random.choice(["buy", "sell", "transfer"], n_samples),
        "hour": np.random.randint(0, 24, n_samples),
        "day_of_week": np.random.randint(0, 7, n_samples),
        "merchant_category": np.random.choice(
            ["retail", "restaurant", "gas", "grocery"], n_samples
        ),
        "is_weekend": np.random.choice([0, 1], n_samples),
        "device_fingerprint": [f"device_{i%20}" for i in range(n_samples)],
        "ip_address": [f"192.168.1.{i%255}" for i in range(n_samples)],
        "is_fraud": np.random.choice(
            [0, 1], n_samples, p=[0.95, 0.05]
        ),  # 5% fraud rate
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_price_data():
    """Sample price data for time series models"""
    import numpy as np
    import pandas as pd

    # Generate sample price data
    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")

    # Generate realistic price movements
    returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
    prices = [100]  # Starting price

    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    data = pd.DataFrame(
        {
            "date": dates,
            "price": prices,
            "volume": np.random.randint(100000, 10000000, len(dates)),
            "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            "open": [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            "close": prices,
        }
    )

    return data


@pytest.fixture
def jwt_token(auth_system, test_user):
    """Generate JWT token for testing"""
    session_id = "test_session_123"
    return auth_system._generate_access_token(str(test_user.id), session_id)


@pytest.fixture
def api_headers(jwt_token):
    """API headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key",
    }


@pytest.fixture
def temp_file():
    """Create temporary file for testing"""
    fd, path = tempfile.mkstemp()

    yield path

    # Cleanup
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file names
    for item in items:
        if "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)


# Test utilities
class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_user_data(**kwargs):
        """Create user data with defaults"""
        default_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890",
            "date_of_birth": datetime(1990, 1, 1),
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "US",
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_transaction_data(**kwargs):
        """Create transaction data with defaults"""
        default_data = {
            "amount": 1000.00,
            "transaction_type": "buy",
            "symbol": "AAPL",
            "quantity": 10,
            "price": 100.00,
            "currency": "USD",
            "description": "Test transaction",
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_portfolio_data(**kwargs):
        """Create portfolio data with defaults"""
        default_data = {
            "name": "Test Portfolio",
            "description": "Test portfolio for testing",
            "total_value": 50000.00,
            "cash_balance": 5000.00,
            "currency": "USD",
        }
        default_data.update(kwargs)
        return default_data


# Mock helpers
class MockResponse:
    """Mock HTTP response"""

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def mock_requests_get(url, **kwargs):
    """Mock requests.get"""
    if "api.example.com" in url:
        return MockResponse({"data": "test"}, 200)
    return MockResponse({"error": "Not found"}, 404)


def mock_requests_post(url, **kwargs):
    """Mock requests.post"""
    if "api.example.com" in url:
        return MockResponse({"success": True}, 200)
    return MockResponse({"error": "Bad request"}, 400)


# Performance testing helpers
import time
from contextlib import contextmanager


@contextmanager
def timer():
    """Context manager to measure execution time"""
    start = time.time()
    yield
    end = time.time()
    print(f"Execution time: {end - start:.4f} seconds")


def measure_memory_usage():
    """Measure memory usage"""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB


# Security testing helpers
def generate_malicious_inputs():
    """Generate malicious inputs for security testing"""
    return [
        # SQL injection attempts
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        # XSS attempts
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        # Command injection attempts
        "; cat /etc/passwd",
        "| whoami",
        "&& ls -la",
        # Path traversal attempts
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        # Buffer overflow attempts
        "A" * 10000,
        "\x00" * 1000,
        # Format string attacks
        "%s%s%s%s%s",
        "%x%x%x%x%x",
    ]


# Assertion helpers
def assert_valid_uuid(uuid_string):
    """Assert that string is valid UUID"""
    import uuid

    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def assert_valid_email(email):
    """Assert that string is valid email"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def assert_secure_password(password):
    """Assert that password meets security requirements"""
    import re

    # At least 8 characters
    if len(password) < 8:
        return False

    # Contains uppercase letter
    if not re.search(r"[A-Z]", password):
        return False

    # Contains lowercase letter
    if not re.search(r"[a-z]", password):
        return False

    # Contains digit
    if not re.search(r"\d", password):
        return False

    # Contains special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


def assert_encrypted_data(data):
    """Assert that data appears to be encrypted"""
    # Basic checks for encrypted data
    if isinstance(data, str):
        # Should not be readable text
        if any(word in data.lower() for word in ["password", "secret", "key", "token"]):
            return False

        # Should contain non-printable characters or be base64 encoded
        try:
            import base64

            base64.b64decode(data)
            return True
        except:
            # Check for non-printable characters
            return any(ord(c) < 32 or ord(c) > 126 for c in data)

    return isinstance(data, bytes)
