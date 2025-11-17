import base64
import hashlib
import hmac
import ipaddress
import re
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import jwt
from app.core.config import get_settings
from app.core.logging import get_logger, security_logger
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
from passlib.hash import bcrypt

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
    bcrypt__rounds=12,
    pbkdf2_sha256__rounds=100000,
)


class SecurityManager:
    """Comprehensive security manager for the application"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._blocked_ips: Dict[str, datetime] = {}

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength according to security policies"""
        errors = []
        score = 0

        # Length check
        if len(password) < self.settings.PASSWORD_MIN_LENGTH:
            errors.append(
                f"Password must be at least {self.settings.PASSWORD_MIN_LENGTH} characters long"
            )
        else:
            score += 1

        # Character variety checks
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        else:
            score += 1

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        else:
            score += 1

        # Common password check
        if self._is_common_password(password):
            errors.append(
                "Password is too common, please choose a more unique password"
            )
            score -= 1

        # Sequential characters check
        if self._has_sequential_chars(password):
            errors.append("Password should not contain sequential characters")
            score -= 1

        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 2:
            strength = "medium"

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": max(0, score),
        }

    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list"""
        common_passwords = [
            "password",
            "123456",
            "password123",
            "admin",
            "qwerty",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
        ]
        return password.lower() in common_passwords

    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters in password"""
        for i in range(len(password) - 2):
            if ord(password[i]) + 1 == ord(password[i + 1]) and ord(
                password[i + 1]
            ) + 1 == ord(password[i + 2]):
                return True
        return False

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with enhanced security"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        # Add additional claims
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "iss": "quantumnest-api",
                "aud": "quantumnest-client",
                "jti": secrets.token_urlsafe(16),  # JWT ID for token revocation
            }
        )

        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow()
            + timedelta(minutes=self.settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }
        return jwt.encode(
            data, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """Verify JWT token with enhanced validation"""
        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM],
                audience="quantumnest-client",
                issuer="quantumnest-api",
            )

            # Verify token type
            if payload.get("type") != token_type and token_type != "access":
                return None

            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired", token_type=token_type)
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning("Invalid token", error=str(e), token_type=token_type)
            return None

    def check_rate_limit(
        self, identifier: str, max_requests: int = None, window_minutes: int = 1
    ) -> bool:
        """Check if request is within rate limits"""
        if not self.settings.RATE_LIMIT_ENABLED:
            return True

        max_requests = max_requests or self.settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []

        # Remove old attempts
        self._failed_attempts[identifier] = [
            attempt
            for attempt in self._failed_attempts[identifier]
            if attempt > window_start
        ]

        # Check if within limits
        if len(self._failed_attempts[identifier]) >= max_requests:
            return False

        # Record this attempt
        self._failed_attempts[identifier].append(now)
        return True

    def record_failed_login(self, email: str, ip_address: str) -> bool:
        """Record failed login attempt and check if account should be locked"""
        now = datetime.utcnow()
        lockout_window = now - timedelta(minutes=self.settings.LOCKOUT_DURATION_MINUTES)

        # Initialize tracking for this email
        if email not in self._failed_attempts:
            self._failed_attempts[email] = []

        # Remove old attempts
        self._failed_attempts[email] = [
            attempt
            for attempt in self._failed_attempts[email]
            if attempt > lockout_window
        ]

        # Record this attempt
        self._failed_attempts[email].append(now)

        # Log the attempt
        security_logger.log_failed_authentication(
            email, "invalid_credentials", ip_address
        )

        # Check if account should be locked
        if len(self._failed_attempts[email]) >= self.settings.MAX_LOGIN_ATTEMPTS:
            self.logger.warning(
                "Account locked due to too many failed attempts",
                email=email,
                ip_address=ip_address,
            )
            return True

        return False

    def is_account_locked(self, email: str) -> bool:
        """Check if account is currently locked"""
        if email not in self._failed_attempts:
            return False

        now = datetime.utcnow()
        lockout_window = now - timedelta(minutes=self.settings.LOCKOUT_DURATION_MINUTES)

        # Remove old attempts
        self._failed_attempts[email] = [
            attempt
            for attempt in self._failed_attempts[email]
            if attempt > lockout_window
        ]

        return len(self._failed_attempts[email]) >= self.settings.MAX_LOGIN_ATTEMPTS

    def clear_failed_attempts(self, email: str):
        """Clear failed login attempts for successful login"""
        if email in self._failed_attempts:
            del self._failed_attempts[email]

    def validate_ip_address(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if ip_address in self._blocked_ips:
            block_time = self._blocked_ips[ip_address]
            if datetime.utcnow() - block_time < timedelta(hours=1):  # 1 hour block
                return True
            else:
                del self._blocked_ips[ip_address]
        return False

    def block_ip(self, ip_address: str, reason: str):
        """Block an IP address"""
        self._blocked_ips[ip_address] = datetime.utcnow()
        self.logger.warning("IP address blocked", ip_address=ip_address, reason=reason)

    def generate_api_key(self, user_id: str, name: str) -> str:
        """Generate API key for user"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{name}:{timestamp}"
        signature = hmac.new(
            self.settings.SECRET_KEY.encode(), data.encode(), hashlib.sha256
        ).hexdigest()

        api_key = base64.b64encode(f"{data}:{signature}".encode()).decode()
        return f"qn_{api_key}"

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, str]]:
        """Verify API key and extract user information"""
        try:
            if not api_key.startswith("qn_"):
                return None

            decoded = base64.b64decode(api_key[3:]).decode()
            parts = decoded.split(":")

            if len(parts) != 4:
                return None

            user_id, name, timestamp, signature = parts
            data = f"{user_id}:{name}:{timestamp}"

            expected_signature = hmac.new(
                self.settings.SECRET_KEY.encode(), data.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return None

            return {"user_id": user_id, "name": name, "timestamp": timestamp}
        except Exception:
            return None

    def encrypt_sensitive_data(self, data: str, password: str) -> str:
        """Encrypt sensitive data using Fernet"""
        password_bytes = password.encode()
        salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())

        # Combine salt and encrypted data
        return base64.b64encode(salt + encrypted_data).decode()

    def decrypt_sensitive_data(
        self, encrypted_data: str, password: str
    ) -> Optional[str]:
        """Decrypt sensitive data"""
        try:
            combined_data = base64.b64decode(encrypted_data.encode())
            salt = combined_data[:16]
            encrypted_bytes = combined_data[16:]

            password_bytes = password.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_bytes)

            return decrypted_data.decode()
        except Exception:
            return None

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not isinstance(input_data, str):
            return str(input_data)

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', "", input_data)

        # Remove SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\bOR\b.*\b=\b|\bAND\b.*\b=\b)",
        ]

        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    def validate_file_upload(self, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate file upload security"""
        errors = []

        # Check file size
        if file_size > self.settings.MAX_FILE_SIZE:
            errors.append(
                f"File size exceeds maximum allowed size of {self.settings.MAX_FILE_SIZE} bytes"
            )

        # Check file extension
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext not in self.settings.ALLOWED_FILE_TYPES:
            errors.append(f"File type {file_ext} is not allowed")

        # Check for dangerous filenames
        dangerous_patterns = [r"\.\./", r"\.\.\\", r"^\.", r"\$", r'[<>:"|?*]']

        for pattern in dangerous_patterns:
            if re.search(pattern, filename):
                errors.append("Filename contains dangerous characters")
                break

        return {"valid": len(errors) == 0, "errors": errors}


# Security decorators
def require_auth(f):
    """Decorator to require authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would be implemented with FastAPI dependencies
        return f(*args, **kwargs)

    return decorated_function


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented with FastAPI dependencies
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def rate_limit(max_requests: int = 100, window_minutes: int = 1):
    """Decorator to apply rate limiting"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented with FastAPI middleware
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Initialize security manager
security_manager = SecurityManager()
