import time
import hashlib
import hmac
import json
import ipaddress
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from flask import Flask, request, jsonify, g
from functools import wraps
import redis
import jwt
from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.core.logging import get_logger
from app.auth.authentication import AdvancedAuthenticationSystem
from app.auth.authorization import RoleBasedAccessControl, AccessRequest, ResourceType, Action

logger = get_logger(__name__)

@dataclass
class SecurityConfig:
    """Security middleware configuration"""
    enable_rate_limiting: bool = True
    enable_request_signing: bool = True
    enable_ip_filtering: bool = True
    enable_cors: bool = True
    enable_csrf_protection: bool = True
    enable_request_encryption: bool = False
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30  # seconds
    
class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = get_logger(__name__)
        
        # Rate limit configurations
        self.limits = {
            'global': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'auth': {'requests': 10, 'window': 300},        # 10 auth requests per 5 minutes
            'api': {'requests': 100, 'window': 300},        # 100 API requests per 5 minutes
            'trading': {'requests': 50, 'window': 60},      # 50 trading requests per minute
            'market_data': {'requests': 200, 'window': 60}, # 200 market data requests per minute
        }
    
    def is_allowed(self, identifier: str, limit_type: str = 'api') -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        try:
            if limit_type not in self.limits:
                limit_type = 'api'
            
            config = self.limits[limit_type]
            key = f"rate_limit:{limit_type}:{identifier}"
            
            # Get current count
            current_count = self.redis.get(key)
            
            if current_count is None:
                # First request in window
                self.redis.setex(key, config['window'], 1)
                return True, {
                    'allowed': True,
                    'count': 1,
                    'limit': config['requests'],
                    'window': config['window'],
                    'reset_time': int(time.time()) + config['window']
                }
            
            current_count = int(current_count)
            
            if current_count >= config['requests']:
                # Rate limit exceeded
                ttl = self.redis.ttl(key)
                return False, {
                    'allowed': False,
                    'count': current_count,
                    'limit': config['requests'],
                    'window': config['window'],
                    'reset_time': int(time.time()) + ttl if ttl > 0 else int(time.time()) + config['window']
                }
            
            # Increment counter
            self.redis.incr(key)
            ttl = self.redis.ttl(key)
            
            return True, {
                'allowed': True,
                'count': current_count + 1,
                'limit': config['requests'],
                'window': config['window'],
                'reset_time': int(time.time()) + ttl if ttl > 0 else int(time.time()) + config['window']
            }
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {str(e)}")
            # Allow request on error to avoid blocking legitimate traffic
            return True, {'allowed': True, 'error': str(e)}
    
    def get_sliding_window_count(self, identifier: str, window_seconds: int) -> int:
        """Get count for sliding window rate limiting"""
        try:
            key = f"sliding:{identifier}"
            now = time.time()
            
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, now - window_seconds)
            
            # Get current count
            count = self.redis.zcard(key)
            
            return count
            
        except Exception as e:
            self.logger.error(f"Sliding window count error: {str(e)}")
            return 0
    
    def add_sliding_window_entry(self, identifier: str, window_seconds: int):
        """Add entry to sliding window"""
        try:
            key = f"sliding:{identifier}"
            now = time.time()
            
            # Add current request
            self.redis.zadd(key, {str(now): now})
            
            # Set expiration
            self.redis.expire(key, window_seconds)
            
        except Exception as e:
            self.logger.error(f"Sliding window add error: {str(e)}")

class RequestValidator:
    """Request validation and sanitization"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Dangerous patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)"
        ]
        
        self.xss_patterns = [
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>"
        ]
        
        self.command_injection_patterns = [
            r"[;&|`$(){}[\]\\]",
            r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b"
        ]
    
    def validate_request(self, data: Any) -> tuple[bool, List[str]]:
        """Validate request data for security threats"""
        issues = []
        
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    key_issues = self._validate_string(str(key))
                    if key_issues:
                        issues.extend([f"Key '{key}': {issue}" for issue in key_issues])
                    
                    if isinstance(value, (str, int, float)):
                        value_issues = self._validate_string(str(value))
                        if value_issues:
                            issues.extend([f"Value for '{key}': {issue}" for issue in value_issues])
                    elif isinstance(value, (dict, list)):
                        nested_valid, nested_issues = self.validate_request(value)
                        if not nested_valid:
                            issues.extend(nested_issues)
            
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    item_valid, item_issues = self.validate_request(item)
                    if not item_valid:
                        issues.extend([f"Item {i}: {issue}" for issue in item_issues])
            
            elif isinstance(data, str):
                issues = self._validate_string(data)
            
            return len(issues) == 0, issues
            
        except Exception as e:
            self.logger.error(f"Request validation error: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_string(self, text: str) -> List[str]:
        """Validate string for security issues"""
        issues = []
        
        # Check for SQL injection
        import re
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Potential SQL injection detected")
                break
        
        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Potential XSS attack detected")
                break
        
        # Check for command injection
        for pattern in self.command_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Potential command injection detected")
                break
        
        return issues
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data"""
        try:
            if isinstance(data, dict):
                return {key: self.sanitize_input(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [self.sanitize_input(item) for item in data]
            elif isinstance(data, str):
                return self._sanitize_string(data)
            else:
                return data
                
        except Exception as e:
            self.logger.error(f"Input sanitization error: {str(e)}")
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string input"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Escape HTML entities
        import html
        text = html.escape(text)
        
        # Remove control characters except common ones
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        return text

class IPFilter:
    """IP address filtering and geolocation"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Default blocked IP ranges
        self.blocked_ranges = [
            # Private ranges (if needed)
            # ipaddress.ip_network('10.0.0.0/8'),
            # ipaddress.ip_network('172.16.0.0/12'),
            # ipaddress.ip_network('192.168.0.0/16'),
        ]
        
        # Allowed IP ranges (if whitelist mode)
        self.allowed_ranges = []
        
        # Blocked countries (ISO codes)
        self.blocked_countries = []
        
        # Whitelist mode
        self.whitelist_mode = False
    
    def is_allowed(self, ip_address: str) -> tuple[bool, str]:
        """Check if IP address is allowed"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check blocked ranges
            for blocked_range in self.blocked_ranges:
                if ip in blocked_range:
                    return False, f"IP {ip_address} is in blocked range {blocked_range}"
            
            # Check whitelist mode
            if self.whitelist_mode:
                allowed = False
                for allowed_range in self.allowed_ranges:
                    if ip in allowed_range:
                        allowed = True
                        break
                
                if not allowed:
                    return False, f"IP {ip_address} is not in allowed ranges"
            
            # Check geolocation (simplified)
            country = self._get_country_from_ip(ip_address)
            if country in self.blocked_countries:
                return False, f"IP {ip_address} is from blocked country {country}"
            
            return True, "IP allowed"
            
        except Exception as e:
            self.logger.error(f"IP filtering error: {str(e)}")
            return True, "IP filtering error - allowing by default"
    
    def _get_country_from_ip(self, ip_address: str) -> str:
        """Get country from IP address (simplified)"""
        # In production, this would use a real geolocation service
        return "US"  # Default
    
    def add_blocked_ip(self, ip_range: str):
        """Add IP range to blocked list"""
        try:
            network = ipaddress.ip_network(ip_range)
            self.blocked_ranges.append(network)
            self.logger.info(f"Added blocked IP range: {ip_range}")
        except Exception as e:
            self.logger.error(f"Error adding blocked IP range: {str(e)}")
    
    def add_allowed_ip(self, ip_range: str):
        """Add IP range to allowed list"""
        try:
            network = ipaddress.ip_network(ip_range)
            self.allowed_ranges.append(network)
            self.logger.info(f"Added allowed IP range: {ip_range}")
        except Exception as e:
            self.logger.error(f"Error adding allowed IP range: {str(e)}")

class RequestSigner:
    """Request signing and verification"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
        self.logger = get_logger(__name__)
    
    def sign_request(self, method: str, path: str, body: str, timestamp: int) -> str:
        """Sign request with HMAC"""
        try:
            message = f"{method}\n{path}\n{body}\n{timestamp}"
            signature = hmac.new(
                self.secret_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            self.logger.error(f"Request signing error: {str(e)}")
            return ""
    
    def verify_signature(self, method: str, path: str, body: str, 
                        timestamp: int, signature: str) -> bool:
        """Verify request signature"""
        try:
            expected_signature = self.sign_request(method, path, body, timestamp)
            
            # Use constant-time comparison
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Signature verification error: {str(e)}")
            return False
    
    def is_timestamp_valid(self, timestamp: int, tolerance: int = 300) -> bool:
        """Check if timestamp is within tolerance (default 5 minutes)"""
        current_time = int(time.time())
        return abs(current_time - timestamp) <= tolerance

class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app: Flask, config: SecurityConfig = None):
        self.app = app
        self.config = config or SecurityConfig()
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.redis_client = redis.Redis(
            host=self.settings.REDIS_HOST,
            port=self.settings.REDIS_PORT,
            password=self.settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
        self.rate_limiter = RateLimiter(self.redis_client)
        self.request_validator = RequestValidator()
        self.ip_filter = IPFilter()
        self.request_signer = RequestSigner(self.settings.API_SECRET_KEY)
        
        # Initialize middleware
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup Flask middleware"""
        
        @self.app.before_request
        def security_checks():
            """Run security checks before each request"""
            
            # Skip security checks for health endpoints
            if request.path in ['/health', '/ping']:
                return
            
            # Request size check
            if request.content_length and request.content_length > self.config.max_request_size:
                return jsonify({
                    'error': 'Request too large',
                    'max_size': self.config.max_request_size
                }), 413
            
            # IP filtering
            if self.config.enable_ip_filtering:
                client_ip = self._get_client_ip()
                ip_allowed, ip_reason = self.ip_filter.is_allowed(client_ip)
                if not ip_allowed:
                    self.logger.warning(f"Blocked IP {client_ip}: {ip_reason}")
                    return jsonify({'error': 'Access denied'}), 403
            
            # Rate limiting
            if self.config.enable_rate_limiting:
                client_id = self._get_client_identifier()
                limit_type = self._get_limit_type()
                
                allowed, limit_info = self.rate_limiter.is_allowed(client_id, limit_type)
                if not allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'limit_info': limit_info
                    }), 429
                
                # Add rate limit headers
                g.rate_limit_info = limit_info
            
            # Request validation
            if request.is_json and request.get_json():
                valid, issues = self.request_validator.validate_request(request.get_json())
                if not valid:
                    self.logger.warning(f"Request validation failed: {issues}")
                    return jsonify({
                        'error': 'Invalid request',
                        'issues': issues
                    }), 400
            
            # Request signing verification
            if self.config.enable_request_signing and request.method in ['POST', 'PUT', 'DELETE']:
                if not self._verify_request_signature():
                    return jsonify({'error': 'Invalid request signature'}), 401
            
            # CSRF protection
            if self.config.enable_csrf_protection and request.method in ['POST', 'PUT', 'DELETE']:
                if not self._verify_csrf_token():
                    return jsonify({'error': 'CSRF token missing or invalid'}), 403
        
        @self.app.after_request
        def security_headers(response):
            """Add security headers to response"""
            
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Rate limit headers
            if hasattr(g, 'rate_limit_info'):
                info = g.rate_limit_info
                response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                response.headers['X-RateLimit-Remaining'] = str(info.get('limit', 0) - info.get('count', 0))
                response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
            
            # CORS headers
            if self.config.enable_cors:
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
                response.headers['Access-Control-Max-Age'] = '86400'
            
            return response
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded IP
        if 'X-Forwarded-For' in request.headers:
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif 'X-Real-IP' in request.headers:
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr or '127.0.0.1'
    
    def _get_client_identifier(self) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, verify=False)  # Don't verify for rate limiting
                return f"user:{payload.get('user_id', 'unknown')}"
            except:
                pass
        
        # Fall back to IP address
        return f"ip:{self._get_client_ip()}"
    
    def _get_limit_type(self) -> str:
        """Determine rate limit type based on request"""
        path = request.path.lower()
        
        if '/auth' in path:
            return 'auth'
        elif '/trading' in path or '/trade' in path:
            return 'trading'
        elif '/market' in path:
            return 'market_data'
        else:
            return 'api'
    
    def _verify_request_signature(self) -> bool:
        """Verify request signature"""
        try:
            # Get signature from header
            signature = request.headers.get('X-Signature')
            timestamp_str = request.headers.get('X-Timestamp')
            
            if not signature or not timestamp_str:
                return False
            
            timestamp = int(timestamp_str)
            
            # Check timestamp validity
            if not self.request_signer.is_timestamp_valid(timestamp):
                return False
            
            # Get request body
            body = request.get_data(as_text=True) or ''
            
            # Verify signature
            return self.request_signer.verify_signature(
                request.method,
                request.path,
                body,
                timestamp,
                signature
            )
            
        except Exception as e:
            self.logger.error(f"Signature verification error: {str(e)}")
            return False
    
    def _verify_csrf_token(self) -> bool:
        """Verify CSRF token"""
        try:
            # Get CSRF token from header or form
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token and request.is_json:
                csrf_token = request.get_json().get('csrf_token')
            
            if not csrf_token:
                return False
            
            # In production, this would verify against a stored token
            # For now, just check if token exists
            return len(csrf_token) > 0
            
        except Exception as e:
            self.logger.error(f"CSRF verification error: {str(e)}")
            return False

def create_security_middleware(app: Flask, config: SecurityConfig = None) -> SecurityMiddleware:
    """Factory function to create security middleware"""
    return SecurityMiddleware(app, config)

# Decorators for additional security
def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Verify API key (simplified)
        # In production, this would check against a database
        if api_key != get_settings().API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_https(f):
    """Decorator to require HTTPS"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not request.headers.get('X-Forwarded-Proto') == 'https':
            return jsonify({'error': 'HTTPS required'}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security event"""
    try:
        security_logger = get_logger('security')
        
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'client_ip': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent') if request else 'unknown',
            'details': details
        }
        
        security_logger.warning(f"Security event: {json.dumps(event)}")
        
    except Exception as e:
        logger.error(f"Security event logging error: {str(e)}")

# Security monitoring
class SecurityMonitor:
    """Security monitoring and alerting"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = get_logger(__name__)
        
        # Thresholds for alerts
        self.thresholds = {
            'failed_logins': {'count': 10, 'window': 300},  # 10 failed logins in 5 minutes
            'rate_limit_hits': {'count': 5, 'window': 300}, # 5 rate limit hits in 5 minutes
            'blocked_ips': {'count': 20, 'window': 3600},   # 20 blocked IPs in 1 hour
        }
    
    def record_event(self, event_type: str, identifier: str):
        """Record security event"""
        try:
            key = f"security_event:{event_type}:{identifier}"
            
            # Add to sorted set with timestamp
            self.redis.zadd(key, {str(time.time()): time.time()})
            
            # Set expiration
            self.redis.expire(key, 3600)  # 1 hour
            
            # Check if threshold exceeded
            self._check_threshold(event_type, identifier)
            
        except Exception as e:
            self.logger.error(f"Security event recording error: {str(e)}")
    
    def _check_threshold(self, event_type: str, identifier: str):
        """Check if event threshold is exceeded"""
        try:
            if event_type not in self.thresholds:
                return
            
            threshold = self.thresholds[event_type]
            key = f"security_event:{event_type}:{identifier}"
            
            # Count events in window
            now = time.time()
            count = self.redis.zcount(key, now - threshold['window'], now)
            
            if count >= threshold['count']:
                self._trigger_alert(event_type, identifier, count, threshold)
                
        except Exception as e:
            self.logger.error(f"Threshold check error: {str(e)}")
    
    def _trigger_alert(self, event_type: str, identifier: str, count: int, threshold: Dict[str, int]):
        """Trigger security alert"""
        alert = {
            'event_type': event_type,
            'identifier': identifier,
            'count': count,
            'threshold': threshold,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.critical(f"Security alert: {json.dumps(alert)}")
        
        # In production, this would send alerts via email, SMS, etc.
        log_security_event('security_alert', alert)

