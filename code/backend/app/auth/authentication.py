import base64
import hashlib
import io
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
import jwt
import pyotp
import qrcode
import redis
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import SecurityManager
from app.models.models import LoginAttempt, User, UserSession
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class AuthenticationMethod(str, Enum):
    PASSWORD = "password"
    TWO_FACTOR = "two_factor"
    BIOMETRIC = "biometric"
    OAUTH = "oauth"
    API_KEY = "api_key"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


@dataclass
class AuthenticationResult:
    """Authentication result"""

    success: bool
    user_id: Optional[str]
    session_token: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    requires_2fa: bool
    error_message: Optional[str]
    risk_score: float
    device_fingerprint: Optional[str]


@dataclass
class SessionInfo:
    """Session information"""

    session_id: str
    user_id: str
    device_fingerprint: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    risk_score: float
    location: Optional[Dict[str, Any]]


class AdvancedAuthenticationSystem:
    """Advanced authentication system with multi-factor authentication and security features"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.security_manager = SecurityManager()
        self.logger = get_logger(__name__)

        # Redis for session management
        self.redis_client = redis.Redis(
            host=self.settings.REDIS_HOST,
            port=self.settings.REDIS_PORT,
            password=self.settings.REDIS_PASSWORD,
            decode_responses=True,
        )

        # Authentication settings
        self.jwt_secret = self.settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=30)
        self.session_expire = timedelta(hours=24)

        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 12
        self.require_2fa_for_high_risk = True

        # Rate limiting
        self.rate_limits = {
            "login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "password_reset": {"requests": 3, "window": 3600},  # 3 requests per hour
            "2fa_verify": {"requests": 10, "window": 300},  # 10 requests per 5 minutes
        }

    async def authenticate_user(
        self,
        email: str,
        password: str,
        device_fingerprint: str,
        ip_address: str,
        user_agent: str,
    ) -> AuthenticationResult:
        """Authenticate user with comprehensive security checks"""
        try:
            # Rate limiting check
            if not self._check_rate_limit("login", ip_address):
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=False,
                    error_message="Too many login attempts. Please try again later.",
                    risk_score=1.0,
                    device_fingerprint=device_fingerprint,
                )

            # Get user
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                self._log_login_attempt(
                    None, email, ip_address, False, "User not found"
                )
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=False,
                    error_message="Invalid credentials",
                    risk_score=0.8,
                    device_fingerprint=device_fingerprint,
                )

            # Check if account is locked
            if self._is_account_locked(user.id):
                return AuthenticationResult(
                    success=False,
                    user_id=str(user.id),
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=False,
                    error_message="Account is temporarily locked due to suspicious activity",
                    risk_score=1.0,
                    device_fingerprint=device_fingerprint,
                )

            # Verify password
            if not self._verify_password(password, user.password_hash):
                self._log_login_attempt(
                    user.id, email, ip_address, False, "Invalid password"
                )
                self._increment_failed_attempts(user.id)
                return AuthenticationResult(
                    success=False,
                    user_id=str(user.id),
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=False,
                    error_message="Invalid credentials",
                    risk_score=0.7,
                    device_fingerprint=device_fingerprint,
                )

            # Calculate risk score
            risk_score = await self._calculate_authentication_risk(
                user, device_fingerprint, ip_address, user_agent
            )

            # Check if 2FA is required
            requires_2fa = user.two_factor_enabled or (
                self.require_2fa_for_high_risk and risk_score > 0.6
            )

            if requires_2fa:
                # Create temporary session for 2FA
                temp_session = self._create_temp_session(
                    user.id, device_fingerprint, ip_address
                )
                return AuthenticationResult(
                    success=False,
                    user_id=str(user.id),
                    session_token=temp_session,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=True,
                    error_message="Two-factor authentication required",
                    risk_score=risk_score,
                    device_fingerprint=device_fingerprint,
                )

            # Create full session
            session_info = await self._create_session(
                user, device_fingerprint, ip_address, user_agent, risk_score
            )

            # Generate tokens
            access_token = self._generate_access_token(user.id, session_info.session_id)
            refresh_token = self._generate_refresh_token(
                user.id, session_info.session_id
            )

            # Log successful login
            self._log_login_attempt(
                user.id, email, ip_address, True, "Successful login"
            )
            self._reset_failed_attempts(user.id)

            return AuthenticationResult(
                success=True,
                user_id=str(user.id),
                session_token=session_info.session_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=session_info.expires_at,
                requires_2fa=False,
                error_message=None,
                risk_score=risk_score,
                device_fingerprint=device_fingerprint,
            )

        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return AuthenticationResult(
                success=False,
                user_id=None,
                session_token=None,
                access_token=None,
                refresh_token=None,
                expires_at=None,
                requires_2fa=False,
                error_message="Authentication service temporarily unavailable",
                risk_score=1.0,
                device_fingerprint=device_fingerprint,
            )

    async def verify_2fa(
        self,
        user_id: str,
        temp_session: str,
        totp_code: str,
        device_fingerprint: str,
        ip_address: str,
        user_agent: str,
    ) -> AuthenticationResult:
        """Verify two-factor authentication"""
        try:
            # Rate limiting check
            if not self._check_rate_limit("2fa_verify", ip_address):
                return AuthenticationResult(
                    success=False,
                    user_id=user_id,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=True,
                    error_message="Too many 2FA attempts. Please try again later.",
                    risk_score=1.0,
                    device_fingerprint=device_fingerprint,
                )

            # Verify temporary session
            if not self._verify_temp_session(user_id, temp_session):
                return AuthenticationResult(
                    success=False,
                    user_id=user_id,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=True,
                    error_message="Invalid or expired session",
                    risk_score=0.9,
                    device_fingerprint=device_fingerprint,
                )

            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.two_factor_secret:
                return AuthenticationResult(
                    success=False,
                    user_id=user_id,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=True,
                    error_message="2FA not properly configured",
                    risk_score=0.8,
                    device_fingerprint=device_fingerprint,
                )

            # Verify TOTP code
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(totp_code, valid_window=1):
                self._log_login_attempt(
                    user.id, user.email, ip_address, False, "Invalid 2FA code"
                )
                return AuthenticationResult(
                    success=False,
                    user_id=user_id,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    requires_2fa=True,
                    error_message="Invalid 2FA code",
                    risk_score=0.7,
                    device_fingerprint=device_fingerprint,
                )

            # Calculate risk score
            risk_score = await self._calculate_authentication_risk(
                user, device_fingerprint, ip_address, user_agent
            )

            # Create full session
            session_info = await self._create_session(
                user, device_fingerprint, ip_address, user_agent, risk_score
            )

            # Generate tokens
            access_token = self._generate_access_token(user.id, session_info.session_id)
            refresh_token = self._generate_refresh_token(
                user.id, session_info.session_id
            )

            # Clean up temporary session
            self._cleanup_temp_session(temp_session)

            # Log successful 2FA
            self._log_login_attempt(
                user.id, user.email, ip_address, True, "Successful 2FA login"
            )

            return AuthenticationResult(
                success=True,
                user_id=str(user.id),
                session_token=session_info.session_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=session_info.expires_at,
                requires_2fa=False,
                error_message=None,
                risk_score=risk_score,
                device_fingerprint=device_fingerprint,
            )

        except Exception as e:
            self.logger.error(f"2FA verification error: {str(e)}", exc_info=True)
            return AuthenticationResult(
                success=False,
                user_id=user_id,
                session_token=None,
                access_token=None,
                refresh_token=None,
                expires_at=None,
                requires_2fa=True,
                error_message="2FA verification failed",
                risk_score=1.0,
                device_fingerprint=device_fingerprint,
            )

    def setup_2fa(self, user_id: str) -> Dict[str, Any]:
        """Set up two-factor authentication for user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}

            # Generate secret
            secret = pyotp.random_base32()

            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email, issuer_name="QuantumNest Financial"
            )

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_str = base64.b64encode(img_buffer.getvalue()).decode()

            # Store secret temporarily (will be confirmed when user verifies)
            self.redis_client.setex(f"2fa_setup:{user_id}", 300, secret)  # 5 minutes

            return {
                "success": True,
                "secret": secret,
                "qr_code": f"data:image/png;base64,{img_str}",
                "manual_entry_key": secret,
            }

        except Exception as e:
            self.logger.error(f"2FA setup error: {str(e)}", exc_info=True)
            return {"success": False, "error": "Failed to set up 2FA"}

    def confirm_2fa_setup(self, user_id: str, totp_code: str) -> Dict[str, bool]:
        """Confirm 2FA setup with verification code"""
        try:
            # Get temporary secret
            secret = self.redis_client.get(f"2fa_setup:{user_id}")
            if not secret:
                return {"success": False, "error": "Setup session expired"}

            # Verify code
            totp = pyotp.TOTP(secret)
            if not totp.verify(totp_code, valid_window=1):
                return {"success": False, "error": "Invalid verification code"}

            # Save secret to user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}

            user.two_factor_secret = secret
            user.two_factor_enabled = True
            self.db.commit()

            # Clean up temporary secret
            self.redis_client.delete(f"2fa_setup:{user_id}")

            # Generate backup codes
            backup_codes = self._generate_backup_codes(user_id)

            self.logger.info(f"2FA enabled for user {user_id}")

            return {"success": True, "backup_codes": backup_codes}

        except Exception as e:
            self.logger.error(f"2FA confirmation error: {str(e)}", exc_info=True)
            return {"success": False, "error": "Failed to confirm 2FA setup"}

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT access token"""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            # Check if session is still valid
            session_id = payload.get("session_id")
            if not self._is_session_valid(session_id):
                return None

            # Update last activity
            self._update_session_activity(session_id)

            return payload

        except jwt.ExpiredSignatureError:
            self.logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.debug("Invalid token")
            return None
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("user_id")
            session_id = payload.get("session_id")

            # Check if session is still valid
            if not self._is_session_valid(session_id):
                return None

            # Generate new access token
            new_access_token = self._generate_access_token(user_id, session_id)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": int(self.access_token_expire.total_seconds()),
            }

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}")
            return None

    def logout(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        try:
            # Revoke session
            self._revoke_session(session_id)

            # Remove from database
            session = (
                self.db.query(UserSession)
                .filter(UserSession.session_id == session_id)
                .first()
            )

            if session:
                session.status = SessionStatus.REVOKED
                session.ended_at = datetime.utcnow()
                self.db.commit()

            self.logger.info(f"User logged out, session {session_id} revoked")
            return True

        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return False

    def logout_all_sessions(self, user_id: str) -> bool:
        """Logout user from all sessions"""
        try:
            # Get all active sessions
            sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.status == SessionStatus.ACTIVE,
                )
                .all()
            )

            # Revoke all sessions
            for session in sessions:
                self._revoke_session(session.session_id)
                session.status = SessionStatus.REVOKED
                session.ended_at = datetime.utcnow()

            self.db.commit()

            self.logger.info(f"All sessions revoked for user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Logout all sessions error: {str(e)}")
            return False

    def get_active_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for user"""
        try:
            sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.status == SessionStatus.ACTIVE,
                )
                .all()
            )

            session_infos = []
            for session in sessions:
                session_info = SessionInfo(
                    session_id=session.session_id,
                    user_id=str(session.user_id),
                    device_fingerprint=session.device_fingerprint,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    created_at=session.created_at,
                    last_activity=session.last_activity,
                    expires_at=session.expires_at,
                    status=SessionStatus(session.status),
                    risk_score=session.risk_score,
                    location=json.loads(session.location) if session.location else None,
                )
                session_infos.append(session_info)

            return session_infos

        except Exception as e:
            self.logger.error(f"Get active sessions error: {str(e)}")
            return []

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception:
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _generate_access_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "type": "access",
            "exp": datetime.utcnow() + self.access_token_expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "type": "refresh",
            "exp": datetime.utcnow() + self.refresh_token_expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _create_session(
        self,
        user: User,
        device_fingerprint: str,
        ip_address: str,
        user_agent: str,
        risk_score: float,
    ) -> SessionInfo:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.session_expire

        # Get location from IP (simplified)
        location = await self._get_location_from_ip(ip_address)

        # Create session in database
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=expires_at,
            status=SessionStatus.ACTIVE,
            risk_score=risk_score,
            location=json.dumps(location) if location else None,
        )

        self.db.add(session)
        self.db.commit()

        # Store in Redis for fast lookup
        session_data = {
            "user_id": str(user.id),
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "risk_score": risk_score,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        self.redis_client.setex(
            f"session:{session_id}",
            int(self.session_expire.total_seconds()),
            json.dumps(session_data),
        )

        return SessionInfo(
            session_id=session_id,
            user_id=str(user.id),
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=expires_at,
            status=SessionStatus.ACTIVE,
            risk_score=risk_score,
            location=location,
        )

    def _create_temp_session(
        self, user_id: str, device_fingerprint: str, ip_address: str
    ) -> str:
        """Create temporary session for 2FA"""
        temp_session_id = secrets.token_urlsafe(32)

        temp_session_data = {
            "user_id": str(user_id),
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "type": "temp_2fa",
        }

        # Store for 5 minutes
        self.redis_client.setex(
            f"temp_session:{temp_session_id}", 300, json.dumps(temp_session_data)
        )

        return temp_session_id

    def _verify_temp_session(self, user_id: str, temp_session: str) -> bool:
        """Verify temporary session"""
        try:
            session_data = self.redis_client.get(f"temp_session:{temp_session}")
            if not session_data:
                return False

            data = json.loads(session_data)
            return (
                data.get("user_id") == str(user_id) and data.get("type") == "temp_2fa"
            )

        except Exception:
            return False

    def _cleanup_temp_session(self, temp_session: str):
        """Clean up temporary session"""
        self.redis_client.delete(f"temp_session:{temp_session}")

    def _is_session_valid(self, session_id: str) -> bool:
        """Check if session is valid"""
        try:
            session_data = self.redis_client.get(f"session:{session_id}")
            return session_data is not None
        except Exception:
            return False

    def _update_session_activity(self, session_id: str):
        """Update session last activity"""
        try:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                data["last_activity"] = datetime.utcnow().isoformat()

                # Update Redis
                self.redis_client.setex(
                    f"session:{session_id}",
                    int(self.session_expire.total_seconds()),
                    json.dumps(data),
                )

                # Update database
                session = (
                    self.db.query(UserSession)
                    .filter(UserSession.session_id == session_id)
                    .first()
                )

                if session:
                    session.last_activity = datetime.utcnow()
                    self.db.commit()

        except Exception as e:
            self.logger.error(f"Update session activity error: {str(e)}")

    def _revoke_session(self, session_id: str):
        """Revoke session"""
        self.redis_client.delete(f"session:{session_id}")

    async def _calculate_authentication_risk(
        self, user: User, device_fingerprint: str, ip_address: str, user_agent: str
    ) -> float:
        """Calculate authentication risk score"""
        risk_score = 0.0

        try:
            # Check device history
            device_sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user.id,
                    UserSession.device_fingerprint == device_fingerprint,
                )
                .count()
            )

            if device_sessions == 0:
                risk_score += 0.3  # New device
            elif device_sessions < 5:
                risk_score += 0.1  # Infrequent device

            # Check IP history
            ip_sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user.id, UserSession.ip_address == ip_address
                )
                .count()
            )

            if ip_sessions == 0:
                risk_score += 0.2  # New IP

            # Check time patterns (simplified)
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                risk_score += 0.1  # Unusual time

            # Check recent failed attempts
            recent_failures = (
                self.db.query(LoginAttempt)
                .filter(
                    LoginAttempt.user_id == user.id,
                    LoginAttempt.success == False,
                    LoginAttempt.timestamp > datetime.utcnow() - timedelta(hours=24),
                )
                .count()
            )

            if recent_failures > 0:
                risk_score += min(recent_failures * 0.1, 0.3)

            return min(risk_score, 1.0)

        except Exception as e:
            self.logger.error(f"Risk calculation error: {str(e)}")
            return 0.5  # Default moderate risk

    async def _get_location_from_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location from IP address (simplified)"""
        # In production, this would use a real geolocation service
        return {
            "country": "Unknown",
            "region": "Unknown",
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
        }

    def _check_rate_limit(self, action: str, identifier: str) -> bool:
        """Check rate limiting"""
        try:
            if action not in self.rate_limits:
                return True

            limit_config = self.rate_limits[action]
            key = f"rate_limit:{action}:{identifier}"

            current_count = self.redis_client.get(key)
            if current_count is None:
                self.redis_client.setex(key, limit_config["window"], 1)
                return True

            if int(current_count) >= limit_config["requests"]:
                return False

            self.redis_client.incr(key)
            return True

        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            return True  # Allow on error

    def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked"""
        try:
            # Check recent failed attempts
            recent_failures = (
                self.db.query(LoginAttempt)
                .filter(
                    LoginAttempt.user_id == user_id,
                    LoginAttempt.success == False,
                    LoginAttempt.timestamp > datetime.utcnow() - self.lockout_duration,
                )
                .count()
            )

            return recent_failures >= self.max_login_attempts

        except Exception:
            return False

    def _log_login_attempt(
        self,
        user_id: Optional[str],
        email: str,
        ip_address: str,
        success: bool,
        details: str,
    ):
        """Log login attempt"""
        try:
            attempt = LoginAttempt(
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                success=success,
                details=details,
                timestamp=datetime.utcnow(),
            )

            self.db.add(attempt)
            self.db.commit()

        except Exception as e:
            self.logger.error(f"Login attempt logging error: {str(e)}")

    def _increment_failed_attempts(self, user_id: str):
        """Increment failed login attempts counter"""
        try:
            key = f"failed_attempts:{user_id}"
            current_count = self.redis_client.get(key)

            if current_count is None:
                self.redis_client.setex(
                    key, int(self.lockout_duration.total_seconds()), 1
                )
            else:
                self.redis_client.incr(key)

        except Exception as e:
            self.logger.error(f"Failed attempts increment error: {str(e)}")

    def _reset_failed_attempts(self, user_id: str):
        """Reset failed login attempts counter"""
        try:
            self.redis_client.delete(f"failed_attempts:{user_id}")
        except Exception as e:
            self.logger.error(f"Failed attempts reset error: {str(e)}")

    def _generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes for 2FA"""
        backup_codes = []

        for _ in range(10):
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)

        # Store hashed backup codes
        hashed_codes = [self._hash_password(code) for code in backup_codes]

        # Store in Redis with expiration
        self.redis_client.setex(
            f"backup_codes:{user_id}", 86400 * 365, json.dumps(hashed_codes)  # 1 year
        )

        return backup_codes

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        issues = []
        score = 0

        if len(password) < self.password_min_length:
            issues.append(
                f"Password must be at least {self.password_min_length} characters long"
            )
        else:
            score += 1

        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        else:
            score += 1

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        else:
            score += 1

        # Check for common patterns
        if password.lower() in ["password", "123456", "qwerty", "admin"]:
            issues.append("Password is too common")
            score = 0

        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        strength = strength_levels[min(score, 4)]

        return {
            "valid": len(issues) == 0,
            "strength": strength,
            "score": score,
            "issues": issues,
        }
