import os
import sys
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.security import get_current_active_user
from app.db.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
mock_user = {
    "id": 1,
    "email": "test@example.com",
    "full_name": "Test User",
    "is_active": True,
    "is_admin": False,
}


async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_current_active_user():
    return mock_user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user
client = TestClient(app)


class MockAsyncResult:

    def __init__(self, id: Any, status: Any = "SUCCESS", result: Any = None) -> Any:
        self.id = id
        self._status = status
        self._result = result

    @property
    def status(self) -> Any:
        return self._status

    def ready(self) -> Any:
        return self._status in ["SUCCESS", "FAILURE"]

    def successful(self) -> Any:
        return self._status == "SUCCESS"

    @property
    def result(self) -> Any:
        return self._result


def test_health_check() -> Any:
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("app.workers.ai_tasks.predict_asset_price")
def test_predict_asset_price(mock_predict: Any) -> Any:
    """Test asset price prediction endpoint"""
    task_id = "test-task-id"
    mock_task = MagicMock()
    mock_task.id = task_id
    mock_predict.delay.return_value = mock_task
    response = client.post("/ai/predict/asset/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "PENDING"
    assert "check_status_endpoint" in data
    mock_predict.delay.assert_called_once_with("AAPL", 5, "lstm")


@patch("celery.result.AsyncResult")
def test_get_task_status(mock_async_result: Any) -> Any:
    """Test task status endpoint"""
    task_id = "test-task-id"
    mock_result = {
        "asset_symbol": "AAPL",
        "model_type": "lstm",
        "predictions": [{"date": "2025-05-20", "predicted_price": 200.0}],
    }
    mock_async_result.return_value = MockAsyncResult(task_id, "SUCCESS", mock_result)
    response = client.get(f"/ai/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "SUCCESS"
    assert data["result"] == mock_result


@patch("app.workers.ai_tasks.analyze_sentiment")
def test_analyze_sentiment(mock_analyze: Any) -> Any:
    """Test sentiment analysis endpoint"""
    task_id = "test-task-id"
    mock_task = MagicMock()
    mock_task.id = task_id
    mock_analyze.delay.return_value = mock_task
    response = client.post("/ai/sentiment/asset/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "PENDING"
    assert "check_status_endpoint" in data
    mock_analyze.delay.assert_called_once_with("AAPL", None)


@patch("app.workers.ai_tasks.optimize_portfolio")
def test_optimize_portfolio(mock_optimize: Any) -> Any:
    """Test portfolio optimization endpoint"""
    task_id = "test-task-id"
    mock_task = MagicMock()
    mock_task.id = task_id
    mock_optimize.delay.return_value = mock_task
    with patch("sqlalchemy.orm.query.Query.filter") as mock_filter:
        mock_filter.return_value.first.return_value = {"id": 1, "owner_id": 1}
        response = client.post("/ai/optimize/portfolio/1")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "PENDING"
        assert "check_status_endpoint" in data
        mock_optimize.delay.assert_called_once_with(1, None, None)


@patch("app.workers.ai_tasks.analyze_portfolio_risk")
def test_analyze_portfolio_risk(mock_analyze: Any) -> Any:
    """Test portfolio risk analysis endpoint"""
    task_id = "test-task-id"
    mock_task = MagicMock()
    mock_task.id = task_id
    mock_analyze.delay.return_value = mock_task
    with patch("sqlalchemy.orm.query.Query.filter") as mock_filter:
        mock_filter.return_value.first.return_value = {"id": 1, "owner_id": 1}
        response = client.post("/ai/risk/portfolio/1")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "PENDING"
        assert "check_status_endpoint" in data
        mock_analyze.delay.assert_called_once_with(1)


@patch("app.workers.ai_tasks.generate_market_recommendations")
def test_market_recommendations(mock_generate: Any) -> Any:
    """Test market recommendations endpoint"""
    task_id = "test-task-id"
    mock_task = MagicMock()
    mock_task.id = task_id
    mock_generate.delay.return_value = mock_task
    response = client.post("/ai/recommendations/market")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "PENDING"
    assert "check_status_endpoint" in data
    mock_generate.delay.assert_called_once()


def test_deprecated_endpoints() -> Any:
    """Test deprecated endpoints still work but are marked as deprecated"""
    with patch("sqlalchemy.orm.query.Query.filter") as mock_filter:
        mock_filter.return_value.first.return_value = {"id": 1, "owner_id": 1}
        response = client.get("/ai/recommendations/portfolio/1")
        assert response.status_code == 200
        assert "Deprecation" in response.headers
    response = client.get("/ai/recommendations/market")
    assert response.status_code == 200
    assert "Deprecation" in response.headers
    response = client.get("/ai/sentiment/asset/AAPL")
    assert response.status_code == 200
    assert "Deprecation" in response.headers
    with patch("sqlalchemy.orm.query.Query.filter") as mock_filter:
        mock_filter.return_value.first.return_value = {"id": 1, "owner_id": 1}
        response = client.get("/ai/risk/portfolio/1")
        assert response.status_code == 200
        assert "Deprecation" in response.headers
