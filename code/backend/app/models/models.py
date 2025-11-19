import enum
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from app.db.database import Base
from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# Enhanced Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ANALYST = "analyst"
    USER = "user"
    API_USER = "api_user"


class UserTier(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    INSTITUTIONAL = "institutional"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class AssetType(str, enum.Enum):
    STOCK = "stock"
    BOND = "bond"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    FOREX = "forex"
    DERIVATIVE = "derivative"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    REAL_ESTATE = "real_estate"
    ALTERNATIVE = "alternative"


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"
    TRANSFER = "transfer"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class RiskLevel(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AlertType(str, enum.Enum):
    PRICE_ALERT = "price_alert"
    VOLUME_ALERT = "volume_alert"
    NEWS_ALERT = "news_alert"
    RISK_ALERT = "risk_alert"
    COMPLIANCE_ALERT = "compliance_alert"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    EXEMPT = "exempt"


# Enhanced User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    tier = Column(Enum(UserTier), default=UserTier.BASIC, nullable=False)
    status = Column(
        Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False
    )

    # Profile information
    phone_number = Column(String)
    date_of_birth = Column(DateTime)
    country = Column(String)
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")

    # Financial profile
    risk_tolerance = Column(Enum(RiskLevel), default=RiskLevel.MODERATE)
    investment_experience = Column(String)  # beginner, intermediate, advanced, expert
    annual_income = Column(DECIMAL(15, 2))
    net_worth = Column(DECIMAL(15, 2))
    investment_goals = Column(JSON)

    # Security settings
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=func.now())

    # Compliance and verification
    kyc_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.UNDER_REVIEW)
    kyc_verified_at = Column(DateTime)
    aml_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.UNDER_REVIEW)
    accredited_investor = Column(Boolean, default=False)

    # Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    marketing_consent = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))

    # Relationships
    portfolios = relationship(
        "Portfolio", back_populates="owner", cascade="all, delete-orphan"
    )
    transactions = relationship("Transaction", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, nullable=False)
    permissions = Column(JSON)  # List of allowed endpoints/actions
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="api_keys")


# Enhanced Portfolio Model
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Portfolio configuration
    base_currency = Column(String, default="USD")
    portfolio_type = Column(String)  # personal, managed, algorithmic, etc.
    investment_strategy = Column(String)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MODERATE)

    # Performance tracking
    initial_value = Column(DECIMAL(15, 2), default=0)
    current_value = Column(DECIMAL(15, 2), default=0)
    total_return = Column(DECIMAL(15, 4), default=0)  # Percentage
    total_return_amount = Column(DECIMAL(15, 2), default=0)
    daily_return = Column(DECIMAL(15, 4), default=0)
    volatility = Column(DECIMAL(15, 4), default=0)
    sharpe_ratio = Column(DECIMAL(15, 4))
    max_drawdown = Column(DECIMAL(15, 4))

    # Rebalancing settings
    auto_rebalance = Column(Boolean, default=False)
    rebalance_threshold = Column(DECIMAL(5, 2), default=5.0)  # Percentage
    last_rebalanced = Column(DateTime)

    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    benchmark_symbol = Column(String, default="SPY")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="portfolios")
    assets = relationship(
        "PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan"
    )
    performance_history = relationship(
        "PortfolioPerformance", back_populates="portfolio"
    )
    rebalancing_history = relationship("RebalancingEvent", back_populates="portfolio")


# Enhanced Asset Model
class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)

    # Asset details
    description = Column(Text)
    sector = Column(String)
    industry = Column(String)
    country = Column(String)
    currency = Column(String, default="USD")
    exchange = Column(String)

    # Financial metrics
    market_cap = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    pe_ratio = Column(DECIMAL(10, 2))
    dividend_yield = Column(DECIMAL(5, 4))
    beta = Column(DECIMAL(10, 4))

    # Trading information
    is_tradable = Column(Boolean, default=True)
    min_trade_amount = Column(DECIMAL(15, 2), default=1.0)
    tick_size = Column(DECIMAL(10, 6), default=0.01)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_updated = Column(DateTime(timezone=True))

    # Relationships
    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")
    price_history = relationship("AssetPrice", back_populates="asset")
    fundamental_data = relationship("FundamentalData", back_populates="asset")
    news = relationship("NewsItem", back_populates="asset")


class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)

    # Position information
    quantity = Column(DECIMAL(20, 8), nullable=False)
    average_cost = Column(DECIMAL(15, 2), nullable=False)
    current_price = Column(DECIMAL(15, 2))
    market_value = Column(DECIMAL(15, 2))

    # Allocation
    target_allocation = Column(DECIMAL(5, 2))  # Target percentage
    current_allocation = Column(DECIMAL(5, 2))  # Current percentage

    # Performance
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    total_return = Column(DECIMAL(15, 4), default=0)

    # Metadata
    first_purchase_date = Column(DateTime(timezone=True))
    last_transaction_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")
    asset = relationship("Asset", back_populates="portfolio_assets")

    # Constraints
    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="unique_portfolio_asset"),
        CheckConstraint("quantity >= 0", name="positive_quantity"),
        CheckConstraint("average_cost >= 0", name="positive_average_cost"),
    )


class AssetPrice(Base):
    __tablename__ = "asset_prices"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)

    # Price data
    open_price = Column(DECIMAL(15, 6))
    high_price = Column(DECIMAL(15, 6))
    low_price = Column(DECIMAL(15, 6))
    close_price = Column(DECIMAL(15, 6), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(15, 6))

    # Technical indicators
    sma_20 = Column(DECIMAL(15, 6))
    sma_50 = Column(DECIMAL(15, 6))
    ema_12 = Column(DECIMAL(15, 6))
    ema_26 = Column(DECIMAL(15, 6))
    rsi = Column(DECIMAL(5, 2))
    macd = Column(DECIMAL(15, 6))
    bollinger_upper = Column(DECIMAL(15, 6))
    bollinger_lower = Column(DECIMAL(15, 6))

    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    data_source = Column(String, default="api")

    # Relationships
    asset = relationship("Asset", back_populates="price_history")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("asset_id", "timestamp", name="unique_asset_price_timestamp"),
        Index("idx_asset_timestamp", "asset_id", "timestamp"),
        CheckConstraint("close_price > 0", name="positive_close_price"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))

    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(DECIMAL(20, 8))
    price = Column(DECIMAL(15, 6))
    amount = Column(DECIMAL(15, 2), nullable=False)
    fees = Column(DECIMAL(15, 2), default=0)
    tax = Column(DECIMAL(15, 2), default=0)

    # Order information
    order_id = Column(String)
    execution_venue = Column(String)
    settlement_date = Column(DateTime)

    # Status and metadata
    status = Column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    notes = Column(Text)
    external_id = Column(String)  # For integration with external systems

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    executed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="transactions")
    asset = relationship("Asset")
    portfolio = relationship("Portfolio")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"))

    # Alert configuration
    alert_type = Column(Enum(AlertType), nullable=False)
    condition = Column(
        String, nullable=False
    )  # e.g., "price > 100", "volume > 1000000"
    threshold_value = Column(DECIMAL(15, 6))
    message = Column(Text)

    # Delivery settings
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)
    triggered_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="alerts")
    asset = relationship("Asset")


class PortfolioPerformance(Base):
    __tablename__ = "portfolio_performance"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Performance metrics
    date = Column(DateTime(timezone=True), nullable=False)
    total_value = Column(DECIMAL(15, 2), nullable=False)
    daily_return = Column(DECIMAL(15, 6))
    cumulative_return = Column(DECIMAL(15, 6))
    benchmark_return = Column(DECIMAL(15, 6))
    alpha = Column(DECIMAL(15, 6))
    beta = Column(DECIMAL(15, 6))
    volatility = Column(DECIMAL(15, 6))
    sharpe_ratio = Column(DECIMAL(15, 6))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="performance_history")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "date", name="unique_portfolio_performance_date"
        ),
        Index("idx_portfolio_date", "portfolio_id", "date"),
    )


class RebalancingEvent(Base):
    __tablename__ = "rebalancing_events"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Rebalancing details
    trigger_reason = Column(String)  # threshold, scheduled, manual
    trades_executed = Column(JSON)  # List of trades made
    total_trades = Column(Integer)
    total_fees = Column(DECIMAL(15, 2))

    # Performance impact
    portfolio_value_before = Column(DECIMAL(15, 2))
    portfolio_value_after = Column(DECIMAL(15, 2))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="rebalancing_history")


class FundamentalData(Base):
    __tablename__ = "fundamental_data"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)

    # Financial metrics
    revenue = Column(DECIMAL(20, 2))
    net_income = Column(DECIMAL(20, 2))
    total_assets = Column(DECIMAL(20, 2))
    total_debt = Column(DECIMAL(20, 2))
    shareholders_equity = Column(DECIMAL(20, 2))
    operating_cash_flow = Column(DECIMAL(20, 2))
    free_cash_flow = Column(DECIMAL(20, 2))

    # Ratios
    pe_ratio = Column(DECIMAL(10, 2))
    pb_ratio = Column(DECIMAL(10, 2))
    debt_to_equity = Column(DECIMAL(10, 4))
    return_on_equity = Column(DECIMAL(10, 4))
    return_on_assets = Column(DECIMAL(10, 4))
    profit_margin = Column(DECIMAL(10, 4))

    # Metadata
    period_type = Column(String)  # quarterly, annual
    period_end_date = Column(DateTime)
    report_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    asset = relationship("Asset", back_populates="fundamental_data")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "asset_id", "period_end_date", "period_type", name="unique_fundamental_data"
        ),
    )


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))

    # News content
    title = Column(String, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String)
    source = Column(String)
    author = Column(String)

    # Sentiment analysis
    sentiment_score = Column(DECIMAL(5, 4))  # -1 to 1
    sentiment_label = Column(String)  # positive, negative, neutral

    # Metadata
    published_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    asset = relationship("Asset", back_populates="news")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Audit details
    action = Column(String, nullable=False)
    resource_type = Column(String)  # user, portfolio, transaction, etc.
    resource_id = Column(String)
    old_values = Column(JSON)
    new_values = Column(JSON)

    # Request context
    ip_address = Column(String)
    user_agent = Column(String)
    endpoint = Column(String)
    request_id = Column(String)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")


# AI and ML Models (Enhanced)
class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    model_type = Column(String, nullable=False)  # LSTM, GARCH, PCA, etc.
    version = Column(String, default="1.0")

    # Model configuration
    parameters = Column(JSON)
    hyperparameters = Column(JSON)
    training_data_period = Column(String)

    # Performance metrics
    accuracy = Column(DECIMAL(5, 4))
    precision = Column(DECIMAL(5, 4))
    recall = Column(DECIMAL(5, 4))
    f1_score = Column(DECIMAL(5, 4))
    mse = Column(DECIMAL(15, 8))
    mae = Column(DECIMAL(15, 8))

    # Status
    is_active = Column(Boolean, default=True)
    is_trained = Column(Boolean, default=False)
    last_trained = Column(DateTime)
    next_training = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    predictions = relationship("AIPrediction", back_populates="model")


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"))

    # Prediction details
    prediction_type = Column(String, nullable=False)  # price, trend, risk, etc.
    prediction_value = Column(DECIMAL(15, 6))
    confidence = Column(DECIMAL(5, 4))
    probability_distribution = Column(JSON)

    # Time horizon
    prediction_horizon = Column(String)  # 1d, 1w, 1m, 3m, 1y
    target_date = Column(DateTime(timezone=True))

    # Validation
    actual_value = Column(DECIMAL(15, 6))
    accuracy_score = Column(DECIMAL(5, 4))

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("AIModel", back_populates="predictions")
    asset = relationship("Asset")


# Blockchain Models (Enhanced)
class SmartContract(Base):
    __tablename__ = "smart_contracts"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    contract_type = Column(String, nullable=False)

    # Contract details
    abi = Column(JSON)
    bytecode = Column(Text)
    source_code = Column(Text)
    compiler_version = Column(String)

    # Network information
    network = Column(String, nullable=False)  # mainnet, testnet, polygon, etc.
    chain_id = Column(Integer)
    deployment_tx_hash = Column(String)

    # Status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transactions = relationship("BlockchainTransaction", back_populates="contract")


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True, nullable=False)
    contract_id = Column(Integer, ForeignKey("smart_contracts.id"))

    # Transaction details
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    value = Column(DECIMAL(30, 18))  # Support for high precision crypto values
    gas_limit = Column(Integer)
    gas_used = Column(Integer)
    gas_price = Column(DECIMAL(30, 18))

    # Block information
    block_number = Column(BigInteger)
    block_hash = Column(String)
    transaction_index = Column(Integer)

    # Status and metadata
    status = Column(String, nullable=False)  # confirmed, pending, failed
    confirmations = Column(Integer, default=0)
    network = Column(String, nullable=False)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    block_timestamp = Column(DateTime(timezone=True))

    contract = relationship("SmartContract", back_populates="transactions")


# System and Monitoring Models
class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String, nullable=False, index=True)
    component = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Context
    request_id = Column(String)
    user_id = Column(Integer)
    session_id = Column(String)

    # Additional data
    log_metadata = Column(JSON)
    stack_trace = Column(Text)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_log_level_timestamp", "log_level", "timestamp"),
        Index("idx_component_timestamp", "component", "timestamp"),
    )


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(DECIMAL(15, 6), nullable=False)
    metric_type = Column(String)  # counter, gauge, histogram

    # Labels/tags
    labels = Column(JSON)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Constraints
    __table_args__ = (Index("idx_metric_name_timestamp", "metric_name", "timestamp"),)
