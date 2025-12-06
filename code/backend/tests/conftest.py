import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch
import pytest
import redis
from app.ai.fraud_detection import AdvancedFraudDetectionSystem
from app.auth.authentication import AdvancedAuthenticationSystem
from app.auth.authorization import RoleBasedAccessControl
from app.models.models import Account, Base, Portfolio, Transaction, User
from app.services.market_data_service import MarketDataService
from app.services.trading_service import TradingService
from app.utils.encryption import AdvancedEncryptionManager
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_settings() -> Any:
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
def test_database() -> Any:
    """Create test database"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    yield SessionLocal
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_database: Any) -> Any:
    """Create database session for test"""
    session = test_database()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_redis() -> Any:
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
def test_app() -> Any:
    """Create test Flask application"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


@pytest.fixture
def test_user_data() -> Any:
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
def test_user(db_session: Any, test_user_data: Any) -> Any:
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
def test_account(db_session: Any, test_user: Any) -> Any:
    """Create test account"""
    account = Account(
        user_id=test_user.id,
        account_number="TEST123456789",
        account_type="checking",
        balance=10000.0,
        currency="USD",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def test_portfolio(db_session: Any, test_user: Any) -> Any:
    """Create test portfolio"""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        description="Test portfolio for testing",
        total_value=50000.0,
        cash_balance=5000.0,
        currency="USD",
        created_at=datetime.utcnow(),
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_transaction_data() -> Any:
    """Test transaction data"""
    return {
        "amount": 1000.0,
        "transaction_type": "buy",
        "symbol": "AAPL",
        "quantity": 10,
        "price": 100.0,
        "currency": "USD",
        "description": "Test transaction",
    }


@pytest.fixture
def test_transaction(
    db_session: Any, test_user: Any, test_account: Any, test_transaction_data: Any
) -> Any:
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
def auth_system(db_session: Any, mock_redis: Any) -> Any:
    """Create authentication system for testing"""
    with patch("app.auth.authentication.redis.Redis", return_value=mock_redis):
        return AdvancedAuthenticationSystem(db_session)


@pytest.fixture
def auth_system_real_redis(db_session: Any) -> Any:
    """Create authentication system with real Redis (for integration tests)"""
    try:
        redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        redis_client.ping()
    except:
        pytest.skip("Redis not available for integration tests")
    return AdvancedAuthenticationSystem(db_session)


@pytest.fixture
def rbac_system(db_session: Any) -> Any:
    """Create RBAC system for testing"""
    return RoleBasedAccessControl(db_session)


@pytest.fixture
def encryption_manager() -> Any:
    """Create encryption manager for testing"""
    return AdvancedEncryptionManager()


@pytest.fixture
def trading_service() -> Any:
    """Create trading service for testing"""
    return TradingService()


@pytest.fixture
def market_data_service() -> Any:
    """Create market data service for testing"""
    return MarketDataService()


@pytest.fixture
def fraud_detection_system() -> Any:
    """Create fraud detection system for testing"""
    return AdvancedFraudDetectionSystem()


@pytest.fixture
def mock_market_data() -> Any:
    """Mock market data"""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "price": 150.0,
            "change": 2.5,
            "change_percent": 1.69,
            "volume": 1000000,
            "high": 152.0,
            "low": 148.0,
            "open": 149.0,
            "close": 150.0,
            "timestamp": datetime.utcnow(),
        },
        "GOOGL": {
            "symbol": "GOOGL",
            "price": 2500.0,
            "change": -10.0,
            "change_percent": -0.4,
            "volume": 500000,
            "high": 2520.0,
            "low": 2490.0,
            "open": 2510.0,
            "close": 2500.0,
            "timestamp": datetime.utcnow(),
        },
    }


@pytest.fixture
def sample_training_data() -> Any:
    """Sample training data for ML models"""
    import numpy as np
    import pandas as pd

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
        "device_fingerprint": [f"device_{i % 20}" for i in range(n_samples)],
        "ip_address": [f"192.168.1.{i % 255}" for i in range(n_samples)],
        "is_fraud": np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_price_data() -> Any:
    """Sample price data for time series models"""
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [100]
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
def jwt_token(auth_system: Any, test_user: Any) -> Any:
    """Generate JWT token for testing"""
    session_id = "test_session_123"
    return auth_system._generate_access_token(str(test_user.id), session_id)


@pytest.fixture
def api_headers(jwt_token: Any) -> Any:
    """API headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key",
    }


@pytest.fixture
def temp_file() -> Any:
    """Create temporary file for testing"""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def temp_dir() -> Any:
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def pytest_configure(config: Any) -> Any:
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: Any, items: Any) -> Any:
    """Modify test collection"""
    for item in items:
        if "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)


class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_user_data(**kwargs) -> Any:
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
    def create_transaction_data(**kwargs) -> Any:
        """Create transaction data with defaults"""
        default_data = {
            "amount": 1000.0,
            "transaction_type": "buy",
            "symbol": "AAPL",
            "quantity": 10,
            "price": 100.0,
            "currency": "USD",
            "description": "Test transaction",
        }
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_portfolio_data(**kwargs) -> Any:
        """Create portfolio data with defaults"""
        default_data = {
            "name": "Test Portfolio",
            "description": "Test portfolio for testing",
            "total_value": 50000.0,
            "cash_balance": 5000.0,
            "currency": "USD",
        }
        default_data.update(kwargs)
        return default_data


class MockResponse:
    """Mock HTTP response"""

    def __init__(self, json_data: Any, status_code: Any) -> Any:
        self.json_data = json_data
        self.status_code = status_code

    def json(self) -> Any:
        return self.json_data

    def raise_for_status(self) -> Any:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def mock_requests_get(url: Any, **kwargs) -> Any:
    """Mock requests.get"""
    if "api.example.com" in url:
        return MockResponse({"data": "test"}, 200)
    return MockResponse({"error": "Not found"}, 404)


def mock_requests_post(url: Any, **kwargs) -> Any:
    """Mock requests.post"""
    if "api.example.com" in url:
        return MockResponse({"success": True}, 200)
    return MockResponse({"error": "Bad request"}, 400)


import time
from contextlib import contextmanager
from core.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def timer() -> Any:
    """Context manager to measure execution time"""
    start = time.time()
    yield
    end = time.time()
    logger.info(f"Execution time: {end - start:.4f} seconds")


def measure_memory_usage() -> Any:
    """Measure memory usage"""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def generate_malicious_inputs() -> Any:
    """Generate malicious inputs for security testing"""
    return [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "; cat /etc/passwd",
        "| whoami",
        "&& ls -la",
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "A" * 10000,
        "\x00" * 1000,
        "%s%s%s%s%s",
        "%x%x%x%x%x",
    ]


def assert_valid_uuid(uuid_string: Any) -> Any:
    """Assert that string is valid UUID"""
    import uuid

    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def assert_valid_email(email: Any) -> Any:
    """Assert that string is valid email"""
    import re

    pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def assert_secure_password(password: Any) -> Any:
    """Assert that password meets security requirements"""
    import re

    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("\\d", password):
        return False
    if not re.search('[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def assert_encrypted_data(data: Any) -> Any:
    """Assert that data appears to be encrypted"""
    if isinstance(data, str):
        if any(
            (word in data.lower() for word in ["password", "secret", "key", "token"])
        ):
            return False
        try:
            import base64

            base64.b64decode(data)
            return True
        except:
            return any((ord(c) < 32 or ord(c) > 126 for c in data))
    return isinstance(data, bytes)
