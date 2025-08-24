import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import get_settings

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record, record, message_dict):
        super(StructuredFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service info
        log_record['service'] = 'quantumnest-api'
        log_record['version'] = get_settings().VERSION
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""
    
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'key', 'authorization',
        'cookie', 'session', 'private_key', 'api_key'
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, (dict, str)):
            record.msg = self._sanitize_message(record.msg)
        return True
    
    def _sanitize_message(self, message):
        """Remove sensitive information from log messages"""
        if isinstance(message, dict):
            sanitized = {}
            for key, value in message.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_message(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(message, str):
            for field in self.SENSITIVE_FIELDS:
                if field in message.lower():
                    # Simple redaction for string messages
                    return message.replace(field, "***REDACTED***")
        return message

class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def filter(self, record):
        # This would be populated by middleware in a real application
        record.request_id = getattr(record, 'request_id', None)
        record.user_id = getattr(record, 'user_id', None)
        record.endpoint = getattr(record, 'endpoint', None)
        return True

def setup_logging():
    """Configure application logging"""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.value))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.value))
    
    if settings.ENVIRONMENT.value == "development":
        # Human-readable format for development
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # JSON format for production
        console_formatter = StructuredFormatter()
    
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SecurityFilter())
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if settings.LOG_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.value))
        file_handler.setFormatter(StructuredFormatter())
        file_handler.addFilter(SecurityFilter())
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully", extra={
        'log_level': settings.LOG_LEVEL.value,
        'environment': settings.ENVIRONMENT.value,
        'log_file': settings.LOG_FILE
    })

def configure_logger_levels():
    """Configure log levels for specific modules"""
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    # Set application loggers
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("app.api").setLevel(logging.INFO)
    logging.getLogger("app.ai").setLevel(logging.INFO)
    logging.getLogger("app.auth").setLevel(logging.INFO)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        return get_logger(self.__class__.__name__)

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(f"Calling function {func.__name__}", 
                   function=func.__name__, 
                   args=len(args), 
                   kwargs=list(kwargs.keys()))
        try:
            result = func(*args, **kwargs)
            logger.info(f"Function {func.__name__} completed successfully",
                       function=func.__name__)
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed",
                        function=func.__name__,
                        error=str(e),
                        exc_info=True)
            raise
    return wrapper

def log_api_call(endpoint: str, method: str, user_id: Optional[str] = None):
    """Decorator to log API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("api")
            request_id = kwargs.get('request_id', 'unknown')
            
            logger.info("API call started",
                       endpoint=endpoint,
                       method=method,
                       user_id=user_id,
                       request_id=request_id)
            
            try:
                result = func(*args, **kwargs)
                logger.info("API call completed",
                           endpoint=endpoint,
                           method=method,
                           user_id=user_id,
                           request_id=request_id)
                return result
            except Exception as e:
                logger.error("API call failed",
                            endpoint=endpoint,
                            method=method,
                            user_id=user_id,
                            request_id=request_id,
                            error=str(e),
                            exc_info=True)
                raise
        return wrapper
    return decorator

# Performance monitoring
class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_request_time(self, endpoint: str, duration: float, status_code: int):
        """Log request processing time"""
        self.logger.info("Request processed",
                        endpoint=endpoint,
                        duration_ms=round(duration * 1000, 2),
                        status_code=status_code)
    
    def log_database_query(self, query: str, duration: float):
        """Log database query performance"""
        self.logger.info("Database query executed",
                        query_type=query.split()[0].upper(),
                        duration_ms=round(duration * 1000, 2))
    
    def log_ai_model_inference(self, model_name: str, duration: float, input_size: int):
        """Log AI model inference performance"""
        self.logger.info("AI model inference completed",
                        model_name=model_name,
                        duration_ms=round(duration * 1000, 2),
                        input_size=input_size)

# Security logging
class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_login_attempt(self, email: str, success: bool, ip_address: str):
        """Log login attempts"""
        self.logger.info("Login attempt",
                        email=email,
                        success=success,
                        ip_address=ip_address,
                        event_type="login_attempt")
    
    def log_failed_authentication(self, email: str, reason: str, ip_address: str):
        """Log failed authentication attempts"""
        self.logger.warning("Authentication failed",
                           email=email,
                           reason=reason,
                           ip_address=ip_address,
                           event_type="auth_failure")
    
    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        self.logger.warning("Suspicious activity detected",
                           user_id=user_id,
                           activity=activity,
                           details=details,
                           event_type="suspicious_activity")
    
    def log_permission_denied(self, user_id: str, resource: str, action: str):
        """Log permission denied events"""
        self.logger.warning("Permission denied",
                           user_id=user_id,
                           resource=resource,
                           action=action,
                           event_type="permission_denied")

# Initialize loggers
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()

