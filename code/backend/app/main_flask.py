import logging
import os
import traceback
from datetime import datetime, timedelta

import redis
from app.ai.financial_advisor import AIFinancialAdvisor
from app.ai.fraud_detection import AdvancedFraudDetectionSystem
from app.ai.portfolio_optimization import PortfolioOptimizer
from app.auth.authentication import AdvancedAuthenticationSystem
from app.auth.authorization import RoleBasedAccessControl
# Import our custom modules
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.security import SecurityManager
from app.middleware.security_middleware import (SecurityConfig,
                                                SecurityMiddleware)
from app.models.models import Account, Portfolio, Transaction, User, db
from app.services.market_data_service import MarketDataService
from app.services.risk_management_service import RiskManagementService
from app.services.trading_service import TradingService
from app.utils.encryption import encryption_manager
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException


def create_app(config_name="development"):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    settings = get_settings()

    # Configure Flask app
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": 30,
    }

    # Setup logging
    setup_logging(app)
    logger = get_logger(__name__)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Setup CORS
    CORS(
        app,
        origins=settings.ALLOWED_ORIGINS,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Requested-With",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=True,
    )

    # Initialize Redis
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        # Use in-memory fallback for development
        redis_client = None

    # Initialize security middleware
    security_config = SecurityConfig(
        enable_rate_limiting=True,
        enable_request_signing=settings.ENABLE_REQUEST_SIGNING,
        enable_ip_filtering=settings.ENABLE_IP_FILTERING,
        enable_cors=True,
        enable_csrf_protection=settings.ENABLE_CSRF_PROTECTION,
        max_request_size=10 * 1024 * 1024,  # 10MB
    )

    security_middleware = SecurityMiddleware(app, security_config)

    # Initialize services
    with app.app_context():
        # Create database tables
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")

        # Initialize authentication system
        auth_system = AdvancedAuthenticationSystem(db.session)

        # Initialize RBAC system
        rbac_system = RoleBasedAccessControl(db.session)

        # Initialize trading service
        trading_service = TradingService()

        # Initialize market data service
        market_data_service = MarketDataService()

        # Initialize risk management service
        risk_management_service = RiskManagementService()

        # Initialize AI services
        fraud_detection_system = AdvancedFraudDetectionSystem()
        ai_financial_advisor = AIFinancialAdvisor()
        portfolio_optimizer = PortfolioOptimizer()

        # Store services in app context
        app.auth_system = auth_system
        app.rbac_system = rbac_system
        app.trading_service = trading_service
        app.market_data_service = market_data_service
        app.risk_management_service = risk_management_service
        app.fraud_detection_system = fraud_detection_system
        app.ai_financial_advisor = ai_financial_advisor
        app.portfolio_optimizer = portfolio_optimizer
        app.redis_client = redis_client

    # Error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP exception: {e.code} - {e.description}")
        return (
            jsonify({"error": e.name, "message": e.description, "status_code": e.code}),
            e.code,
        )

    @app.errorhandler(Exception)
    def handle_general_exception(e):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

        if app.debug:
            return (
                jsonify(
                    {
                        "error": "Internal Server Error",
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    }
                ),
                500,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred",
                    }
                ),
                500,
            )

    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 errors"""
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": "The requested resource was not found",
                }
            ),
            404,
        )

    @app.errorhandler(403)
    def handle_forbidden(e):
        """Handle 403 errors"""
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to access this resource",
                }
            ),
            403,
        )

    @app.errorhandler(401)
    def handle_unauthorized(e):
        """Handle 401 errors"""
        return (
            jsonify({"error": "Unauthorized", "message": "Authentication required"}),
            401,
        )

    # Health check endpoints
    @app.route("/health", methods=["GET"])
    def health_check():
        """Basic health check"""
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }
        )

    @app.route("/health/detailed", methods=["GET"])
    def detailed_health_check():
        """Detailed health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {},
        }

        # Check database
        try:
            db.session.execute("SELECT 1")
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check Redis
        try:
            if redis_client:
                redis_client.ping()
                health_status["components"]["redis"] = "healthy"
            else:
                health_status["components"]["redis"] = "not configured"
        except Exception as e:
            health_status["components"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check AI services
        try:
            # Simple check - just verify the services are initialized
            if hasattr(app, "fraud_detection_system"):
                health_status["components"]["fraud_detection"] = "healthy"
            if hasattr(app, "ai_financial_advisor"):
                health_status["components"]["ai_advisor"] = "healthy"
            if hasattr(app, "portfolio_optimizer"):
                health_status["components"]["portfolio_optimizer"] = "healthy"
        except Exception as e:
            health_status["components"]["ai_services"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        return jsonify(health_status)

    # API Routes
    @app.route("/", methods=["GET"])
    def root():
        """Root endpoint"""
        return jsonify(
            {
                "message": "Welcome to QuantumNest Capital API",
                "version": "1.0.0",
                "documentation": "/docs",
                "health": "/health",
            }
        )

    # Authentication routes
    @app.route("/auth/login", methods=["POST"])
    async def login():
        """User login endpoint"""
        try:
            data = request.get_json()

            if not data or not data.get("email") or not data.get("password"):
                return (
                    jsonify(
                        {
                            "error": "Missing credentials",
                            "message": "Email and password are required",
                        }
                    ),
                    400,
                )

            # Get device information
            device_fingerprint = request.headers.get("X-Device-Fingerprint", "unknown")
            ip_address = request.remote_addr
            user_agent = request.headers.get("User-Agent", "unknown")

            # Authenticate user
            result = await app.auth_system.authenticate_user(
                email=data["email"],
                password=data["password"],
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if result.success:
                response_data = {
                    "success": True,
                    "access_token": result.access_token,
                    "refresh_token": result.refresh_token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "user_id": result.user_id,
                }

                if result.requires_2fa:
                    response_data["requires_2fa"] = True
                    response_data["temp_session"] = result.session_token

                return jsonify(response_data)
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": result.error_message,
                            "requires_2fa": result.requires_2fa,
                            "temp_session": (
                                result.session_token if result.requires_2fa else None
                            ),
                        }
                    ),
                    401,
                )

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Authentication failed",
                        "message": "An error occurred during authentication",
                    }
                ),
                500,
            )

    @app.route("/auth/2fa/verify", methods=["POST"])
    async def verify_2fa():
        """2FA verification endpoint"""
        try:
            data = request.get_json()

            required_fields = ["user_id", "temp_session", "totp_code"]
            if not all(field in data for field in required_fields):
                return (
                    jsonify(
                        {
                            "error": "Missing required fields",
                            "message": "user_id, temp_session, and totp_code are required",
                        }
                    ),
                    400,
                )

            # Get device information
            device_fingerprint = request.headers.get("X-Device-Fingerprint", "unknown")
            ip_address = request.remote_addr
            user_agent = request.headers.get("User-Agent", "unknown")

            # Verify 2FA
            result = await app.auth_system.verify_2fa(
                user_id=data["user_id"],
                temp_session=data["temp_session"],
                totp_code=data["totp_code"],
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if result.success:
                return jsonify(
                    {
                        "success": True,
                        "access_token": result.access_token,
                        "refresh_token": result.refresh_token,
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user_id": result.user_id,
                    }
                )
            else:
                return jsonify({"success": False, "error": result.error_message}), 401

        except Exception as e:
            logger.error(f"2FA verification error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "2FA verification failed",
                        "message": "An error occurred during 2FA verification",
                    }
                ),
                500,
            )

    @app.route("/auth/refresh", methods=["POST"])
    def refresh_token():
        """Token refresh endpoint"""
        try:
            data = request.get_json()

            if not data or not data.get("refresh_token"):
                return (
                    jsonify(
                        {
                            "error": "Missing refresh token",
                            "message": "Refresh token is required",
                        }
                    ),
                    400,
                )

            # Refresh token
            result = app.auth_system.refresh_access_token(data["refresh_token"])

            if result:
                return jsonify(result)
            else:
                return (
                    jsonify(
                        {
                            "error": "Invalid refresh token",
                            "message": "The refresh token is invalid or expired",
                        }
                    ),
                    401,
                )

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Token refresh failed",
                        "message": "An error occurred during token refresh",
                    }
                ),
                500,
            )

    @app.route("/auth/logout", methods=["POST"])
    def logout():
        """User logout endpoint"""
        try:
            # Get session from token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return (
                    jsonify(
                        {
                            "error": "Missing authorization header",
                            "message": "Authorization header with Bearer token is required",
                        }
                    ),
                    401,
                )

            token = auth_header.split(" ")[1]
            token_data = app.auth_system.validate_token(token)

            if not token_data:
                return (
                    jsonify(
                        {
                            "error": "Invalid token",
                            "message": "The provided token is invalid",
                        }
                    ),
                    401,
                )

            # Logout
            success = app.auth_system.logout(token_data["session_id"])

            if success:
                return jsonify({"success": True, "message": "Successfully logged out"})
            else:
                return (
                    jsonify(
                        {
                            "error": "Logout failed",
                            "message": "An error occurred during logout",
                        }
                    ),
                    500,
                )

        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Logout failed",
                        "message": "An error occurred during logout",
                    }
                ),
                500,
            )

    # Market data routes
    @app.route("/market/quote/<symbol>", methods=["GET"])
    def get_quote(symbol):
        """Get real-time quote for a symbol"""
        try:
            quote = app.market_data_service.get_real_time_quote(symbol)

            if quote:
                return jsonify({"success": True, "data": quote})
            else:
                return (
                    jsonify(
                        {
                            "error": "Quote not found",
                            "message": f"No quote available for symbol {symbol}",
                        }
                    ),
                    404,
                )

        except Exception as e:
            logger.error(f"Quote retrieval error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Quote retrieval failed",
                        "message": "An error occurred while retrieving the quote",
                    }
                ),
                500,
            )

    @app.route("/market/historical/<symbol>", methods=["GET"])
    def get_historical_data(symbol):
        """Get historical data for a symbol"""
        try:
            # Get query parameters
            period = request.args.get("period", "1y")
            interval = request.args.get("interval", "1d")

            data = app.market_data_service.get_historical_data(symbol, period, interval)

            if data is not None and not data.empty:
                # Convert DataFrame to JSON
                data_json = data.reset_index().to_dict("records")

                return jsonify(
                    {
                        "success": True,
                        "data": data_json,
                        "symbol": symbol,
                        "period": period,
                        "interval": interval,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "error": "Historical data not found",
                            "message": f"No historical data available for symbol {symbol}",
                        }
                    ),
                    404,
                )

        except Exception as e:
            logger.error(f"Historical data retrieval error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Historical data retrieval failed",
                        "message": "An error occurred while retrieving historical data",
                    }
                ),
                500,
            )

    # AI routes
    @app.route("/ai/risk-assessment", methods=["POST"])
    def assess_risk():
        """Assess risk for a transaction or portfolio"""
        try:
            data = request.get_json()

            if not data:
                return (
                    jsonify(
                        {"error": "Missing data", "message": "Request body is required"}
                    ),
                    400,
                )

            # Perform risk assessment
            risk_assessment = app.risk_management_service.assess_transaction_risk(data)

            return jsonify({"success": True, "risk_assessment": risk_assessment})

        except Exception as e:
            logger.error(f"Risk assessment error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Risk assessment failed",
                        "message": "An error occurred during risk assessment",
                    }
                ),
                500,
            )

    @app.route("/ai/fraud-detection", methods=["POST"])
    def detect_fraud():
        """Detect potential fraud in transaction"""
        try:
            data = request.get_json()

            if not data:
                return (
                    jsonify(
                        {
                            "error": "Missing data",
                            "message": "Transaction data is required",
                        }
                    ),
                    400,
                )

            # Perform fraud detection
            fraud_result = app.fraud_detection_system.analyze_transaction(data)

            return jsonify({"success": True, "fraud_analysis": fraud_result})

        except Exception as e:
            logger.error(f"Fraud detection error: {str(e)}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Fraud detection failed",
                        "message": "An error occurred during fraud detection",
                    }
                ),
                500,
            )

    # Register additional blueprints/routes here
    # from app.api import auth_bp, trading_bp, portfolio_bp, admin_bp
    # app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    # app.register_blueprint(trading_bp, url_prefix='/api/v1/trading')
    # app.register_blueprint(portfolio_bp, url_prefix='/api/v1/portfolio')
    # app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')

    logger.info("QuantumNest Capital API initialized successfully")
    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Development server
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_ENV") == "development",
    )
