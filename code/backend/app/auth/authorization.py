import functools
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.models.models import Permission, Role, RolePermission, UserRole
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class ResourceType(str, Enum):
    USER = "user"
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    PORTFOLIO = "portfolio"
    MARKET_DATA = "market_data"
    REPORT = "report"
    ADMIN = "admin"
    SYSTEM = "system"


class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    IMPORT = "import"


class AccessLevel(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class Permission:
    """Permission definition"""

    resource: ResourceType
    action: Action
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class AccessRequest:
    """Access request for authorization"""

    user_id: str
    resource: ResourceType
    action: Action
    resource_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class AuthorizationResult:
    """Authorization result"""

    granted: bool
    reason: str
    required_permissions: List[str]
    user_permissions: List[str]
    conditions_met: bool
    risk_level: str


class RoleBasedAccessControl:
    """Role-Based Access Control (RBAC) system"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

        # Permission cache
        self.permission_cache = {}
        self.cache_ttl = timedelta(minutes=15)
        self.last_cache_update = {}

        # Default roles and permissions
        self.default_roles = {
            "admin": {
                "description": "System administrator with full access",
                "permissions": [
                    f"{resource.value}:{action.value}"
                    for resource in ResourceType
                    for action in Action
                ],
            },
            "portfolio_manager": {
                "description": "Portfolio management access",
                "permissions": [
                    "portfolio:read",
                    "portfolio:update",
                    "portfolio:create",
                    "transaction:read",
                    "transaction:create",
                    "market_data:read",
                    "report:read",
                    "report:create",
                ],
            },
            "trader": {
                "description": "Trading operations access",
                "permissions": [
                    "transaction:read",
                    "transaction:create",
                    "market_data:read",
                    "portfolio:read",
                    "account:read",
                ],
            },
            "analyst": {
                "description": "Analysis and reporting access",
                "permissions": [
                    "market_data:read",
                    "report:read",
                    "report:create",
                    "portfolio:read",
                    "transaction:read",
                ],
            },
            "client": {
                "description": "Client access to own data",
                "permissions": [
                    "account:read",
                    "portfolio:read",
                    "transaction:read",
                    "report:read",
                ],
            },
            "compliance_officer": {
                "description": "Compliance monitoring access",
                "permissions": [
                    "transaction:read",
                    "account:read",
                    "portfolio:read",
                    "report:read",
                    "report:create",
                    "user:read",
                ],
            },
        }

    def authorize(self, request: AccessRequest) -> AuthorizationResult:
        """Authorize access request"""
        try:
            # Get user permissions
            user_permissions = self._get_user_permissions(request.user_id)

            # Check required permission
            required_permission = f"{request.resource.value}:{request.action.value}"

            # Basic permission check
            if required_permission not in user_permissions:
                return AuthorizationResult(
                    granted=False,
                    reason=f"Missing required permission: {required_permission}",
                    required_permissions=[required_permission],
                    user_permissions=user_permissions,
                    conditions_met=False,
                    risk_level="low",
                )

            # Resource-specific authorization
            resource_authorized = self._check_resource_authorization(
                request, user_permissions
            )
            if not resource_authorized.granted:
                return resource_authorized

            # Context-based conditions
            conditions_met = self._check_conditions(request, user_permissions)

            # Risk assessment
            risk_level = self._assess_access_risk(request)

            return AuthorizationResult(
                granted=True,
                reason="Access granted",
                required_permissions=[required_permission],
                user_permissions=user_permissions,
                conditions_met=conditions_met,
                risk_level=risk_level,
            )

        except Exception as e:
            self.logger.error(f"Authorization error: {str(e)}", exc_info=True)
            return AuthorizationResult(
                granted=False,
                reason=f"Authorization system error: {str(e)}",
                required_permissions=[],
                user_permissions=[],
                conditions_met=False,
                risk_level="high",
            )

    def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for user"""
        try:
            # Check cache first
            cache_key = f"permissions:{user_id}"
            if (
                cache_key in self.permission_cache
                and cache_key in self.last_cache_update
                and datetime.utcnow() - self.last_cache_update[cache_key]
                < self.cache_ttl
            ):
                return self.permission_cache[cache_key]

            # Query database
            user_roles = (
                self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
            )

            permissions = set()
            for user_role in user_roles:
                role_permissions = (
                    self.db.query(RolePermission)
                    .filter(RolePermission.role_id == user_role.role_id)
                    .all()
                )

                for role_permission in role_permissions:
                    permission = (
                        self.db.query(Permission)
                        .filter(Permission.id == role_permission.permission_id)
                        .first()
                    )

                    if permission:
                        permissions.add(f"{permission.resource}:{permission.action}")

            # Cache result
            permissions_list = list(permissions)
            self.permission_cache[cache_key] = permissions_list
            self.last_cache_update[cache_key] = datetime.utcnow()

            return permissions_list

        except Exception as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    def _check_resource_authorization(
        self, request: AccessRequest, user_permissions: List[str]
    ) -> AuthorizationResult:
        """Check resource-specific authorization rules"""
        try:
            # Account access - users can only access their own accounts
            if request.resource == ResourceType.ACCOUNT:
                if request.resource_id:
                    # Check if user owns the account
                    if not self._user_owns_resource(
                        request.user_id, "account", request.resource_id
                    ):
                        # Check if user has admin privileges
                        if "admin:read" not in user_permissions:
                            return AuthorizationResult(
                                granted=False,
                                reason="Access denied: Can only access own accounts",
                                required_permissions=[
                                    f"{request.resource.value}:{request.action.value}"
                                ],
                                user_permissions=user_permissions,
                                conditions_met=False,
                                risk_level="medium",
                            )

            # Portfolio access - similar to accounts
            elif request.resource == ResourceType.PORTFOLIO:
                if request.resource_id:
                    if not self._user_owns_resource(
                        request.user_id, "portfolio", request.resource_id
                    ):
                        if (
                            "admin:read" not in user_permissions
                            and "portfolio_manager"
                            not in self._get_user_roles(request.user_id)
                        ):
                            return AuthorizationResult(
                                granted=False,
                                reason="Access denied: Can only access assigned portfolios",
                                required_permissions=[
                                    f"{request.resource.value}:{request.action.value}"
                                ],
                                user_permissions=user_permissions,
                                conditions_met=False,
                                risk_level="medium",
                            )

            # Transaction access - check ownership and limits
            elif request.resource == ResourceType.TRANSACTION:
                if request.action in [Action.CREATE, Action.UPDATE, Action.DELETE]:
                    # Check transaction limits
                    if not self._check_transaction_limits(request):
                        return AuthorizationResult(
                            granted=False,
                            reason="Transaction exceeds authorized limits",
                            required_permissions=[
                                f"{request.resource.value}:{request.action.value}"
                            ],
                            user_permissions=user_permissions,
                            conditions_met=False,
                            risk_level="high",
                        )

            # Admin resources - require admin role
            elif request.resource == ResourceType.ADMIN:
                if "admin" not in self._get_user_roles(request.user_id):
                    return AuthorizationResult(
                        granted=False,
                        reason="Admin access required",
                        required_permissions=[
                            f"{request.resource.value}:{request.action.value}"
                        ],
                        user_permissions=user_permissions,
                        conditions_met=False,
                        risk_level="high",
                    )

            return AuthorizationResult(
                granted=True,
                reason="Resource authorization passed",
                required_permissions=[
                    f"{request.resource.value}:{request.action.value}"
                ],
                user_permissions=user_permissions,
                conditions_met=True,
                risk_level="low",
            )

        except Exception as e:
            self.logger.error(f"Resource authorization error: {str(e)}")
            return AuthorizationResult(
                granted=False,
                reason=f"Resource authorization error: {str(e)}",
                required_permissions=[],
                user_permissions=user_permissions,
                conditions_met=False,
                risk_level="high",
            )

    def _check_conditions(
        self, request: AccessRequest, user_permissions: List[str]
    ) -> bool:
        """Check context-based conditions"""
        try:
            if not request.context:
                return True

            # Time-based conditions
            if "time_restriction" in request.context:
                current_hour = datetime.utcnow().hour
                allowed_hours = request.context["time_restriction"]
                if current_hour not in allowed_hours:
                    return False

            # IP-based conditions
            if "ip_restriction" in request.context:
                allowed_ips = request.context["ip_restriction"]
                user_ip = request.context.get("user_ip")
                if user_ip and user_ip not in allowed_ips:
                    return False

            # Amount-based conditions for transactions
            if (
                request.resource == ResourceType.TRANSACTION
                and "amount" in request.context
            ):
                amount = request.context["amount"]
                user_roles = self._get_user_roles(request.user_id)

                # Different limits for different roles
                limits = {
                    "client": 10000,
                    "trader": 100000,
                    "portfolio_manager": 1000000,
                    "admin": float("inf"),
                }

                max_limit = 0
                for role in user_roles:
                    if role in limits:
                        max_limit = max(max_limit, limits[role])

                if amount > max_limit:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Condition check error: {str(e)}")
            return False

    def _assess_access_risk(self, request: AccessRequest) -> str:
        """Assess risk level of access request"""
        risk_score = 0

        # High-risk actions
        if request.action in [Action.DELETE, Action.EXECUTE]:
            risk_score += 3
        elif request.action in [Action.CREATE, Action.UPDATE]:
            risk_score += 2
        else:
            risk_score += 1

        # High-risk resources
        if request.resource in [ResourceType.ADMIN, ResourceType.SYSTEM]:
            risk_score += 3
        elif request.resource in [ResourceType.TRANSACTION]:
            risk_score += 2

        # Context-based risk
        if request.context:
            if request.context.get("amount", 0) > 100000:
                risk_score += 2
            if request.context.get("external_access", False):
                risk_score += 1

        if risk_score >= 6:
            return "high"
        elif risk_score >= 4:
            return "medium"
        else:
            return "low"

    def _user_owns_resource(
        self, user_id: str, resource_type: str, resource_id: str
    ) -> bool:
        """Check if user owns the resource"""
        try:
            if resource_type == "account":
                # Check if user owns the account
                from app.models.models import Account

                account = (
                    self.db.query(Account)
                    .filter(Account.id == resource_id, Account.user_id == user_id)
                    .first()
                )
                return account is not None

            elif resource_type == "portfolio":
                # Check if user owns or is assigned to the portfolio
                from app.models.models import Portfolio

                portfolio = (
                    self.db.query(Portfolio)
                    .filter(Portfolio.id == resource_id, Portfolio.user_id == user_id)
                    .first()
                )
                return portfolio is not None

            return False

        except Exception as e:
            self.logger.error(f"Resource ownership check error: {str(e)}")
            return False

    def _get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles"""
        try:
            user_roles = (
                self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
            )
            roles = []

            for user_role in user_roles:
                role = self.db.query(Role).filter(Role.id == user_role.role_id).first()
                if role:
                    roles.append(role.name)

            return roles

        except Exception as e:
            self.logger.error(f"Error getting user roles: {str(e)}")
            return []

    def _check_transaction_limits(self, request: AccessRequest) -> bool:
        """Check transaction limits"""
        try:
            if not request.context or "amount" not in request.context:
                return True

            amount = request.context["amount"]
            user_roles = self._get_user_roles(request.user_id)

            # Daily transaction limits by role
            daily_limits = {
                "client": 50000,
                "trader": 500000,
                "portfolio_manager": 5000000,
                "admin": float("inf"),
            }

            # Get maximum limit for user
            max_daily_limit = 0
            for role in user_roles:
                if role in daily_limits:
                    max_daily_limit = max(max_daily_limit, daily_limits[role])

            # Check single transaction limit
            if amount > max_daily_limit:
                return False

            # Check daily cumulative limit
            today = datetime.utcnow().date()
            from app.models.models import Transaction

            daily_total = (
                self.db.query(Transaction)
                .filter(
                    Transaction.user_id == request.user_id,
                    Transaction.created_at >= today,
                )
                .with_entities(Transaction.amount)
                .all()
            )

            current_daily_total = sum(t.amount for t in daily_total if t.amount)

            if current_daily_total + amount > max_daily_limit:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Transaction limit check error: {str(e)}")
            return False

    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        try:
            # Get role
            role = self.db.query(Role).filter(Role.name == role_name).first()
            if not role:
                self.logger.error(f"Role {role_name} not found")
                return False

            # Check if already assigned
            existing = (
                self.db.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
                .first()
            )

            if existing:
                return True  # Already assigned

            # Assign role
            user_role = UserRole(user_id=user_id, role_id=role.id)
            self.db.add(user_role)
            self.db.commit()

            # Clear cache
            self._clear_user_cache(user_id)

            self.logger.info(f"Assigned role {role_name} to user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Role assignment error: {str(e)}")
            self.db.rollback()
            return False

    def revoke_role(self, user_id: str, role_name: str) -> bool:
        """Revoke role from user"""
        try:
            # Get role
            role = self.db.query(Role).filter(Role.name == role_name).first()
            if not role:
                return False

            # Remove assignment
            user_role = (
                self.db.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
                .first()
            )

            if user_role:
                self.db.delete(user_role)
                self.db.commit()

                # Clear cache
                self._clear_user_cache(user_id)

                self.logger.info(f"Revoked role {role_name} from user {user_id}")

            return True

        except Exception as e:
            self.logger.error(f"Role revocation error: {str(e)}")
            self.db.rollback()
            return False

    def create_role(
        self, role_name: str, description: str, permissions: List[str]
    ) -> bool:
        """Create new role with permissions"""
        try:
            # Check if role exists
            existing_role = self.db.query(Role).filter(Role.name == role_name).first()
            if existing_role:
                return False

            # Create role
            role = Role(name=role_name, description=description)
            self.db.add(role)
            self.db.flush()  # Get role ID

            # Add permissions
            for perm_string in permissions:
                resource, action = perm_string.split(":")

                # Get or create permission
                permission = (
                    self.db.query(Permission)
                    .filter(
                        Permission.resource == resource, Permission.action == action
                    )
                    .first()
                )

                if not permission:
                    permission = Permission(resource=resource, action=action)
                    self.db.add(permission)
                    self.db.flush()

                # Link role to permission
                role_permission = RolePermission(
                    role_id=role.id, permission_id=permission.id
                )
                self.db.add(role_permission)

            self.db.commit()
            self.logger.info(
                f"Created role {role_name} with {len(permissions)} permissions"
            )
            return True

        except Exception as e:
            self.logger.error(f"Role creation error: {str(e)}")
            self.db.rollback()
            return False

    def initialize_default_roles(self) -> bool:
        """Initialize default roles and permissions"""
        try:
            for role_name, role_config in self.default_roles.items():
                # Check if role exists
                existing_role = (
                    self.db.query(Role).filter(Role.name == role_name).first()
                )
                if not existing_role:
                    self.create_role(
                        role_name,
                        role_config["description"],
                        role_config["permissions"],
                    )

            self.logger.info("Default roles initialized")
            return True

        except Exception as e:
            self.logger.error(f"Default role initialization error: {str(e)}")
            return False

    def _clear_user_cache(self, user_id: str):
        """Clear user permission cache"""
        cache_key = f"permissions:{user_id}"
        if cache_key in self.permission_cache:
            del self.permission_cache[cache_key]
        if cache_key in self.last_cache_update:
            del self.last_cache_update[cache_key]

    def get_user_permissions_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user permissions"""
        try:
            roles = self._get_user_roles(user_id)
            permissions = self._get_user_permissions(user_id)

            # Group permissions by resource
            permission_groups = {}
            for perm in permissions:
                resource, action = perm.split(":")
                if resource not in permission_groups:
                    permission_groups[resource] = []
                permission_groups[resource].append(action)

            return {
                "user_id": user_id,
                "roles": roles,
                "permissions": permissions,
                "permission_groups": permission_groups,
                "total_permissions": len(permissions),
            }

        except Exception as e:
            self.logger.error(f"Permission summary error: {str(e)}")
            return {}


def require_permission(resource: ResourceType, action: Action):
    """Decorator to require specific permission for endpoint access"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented with Flask request context
            # For now, it's a placeholder for the decorator pattern
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role for endpoint access"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented with Flask request context
            # For now, it's a placeholder for the decorator pattern
            return func(*args, **kwargs)

        return wrapper

    return decorator


class AttributeBasedAccessControl:
    """Attribute-Based Access Control (ABAC) system for fine-grained permissions"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    def evaluate_policy(
        self,
        subject_attributes: Dict[str, Any],
        resource_attributes: Dict[str, Any],
        action_attributes: Dict[str, Any],
        environment_attributes: Dict[str, Any],
    ) -> bool:
        """Evaluate ABAC policy"""
        try:
            # Example policy evaluation
            # In production, this would use a policy engine

            # Time-based access
            if "allowed_hours" in environment_attributes:
                current_hour = datetime.utcnow().hour
                if current_hour not in environment_attributes["allowed_hours"]:
                    return False

            # Location-based access
            if "allowed_locations" in environment_attributes:
                user_location = subject_attributes.get("location")
                if user_location not in environment_attributes["allowed_locations"]:
                    return False

            # Resource sensitivity
            if resource_attributes.get("sensitivity") == "high":
                if subject_attributes.get("clearance_level", 0) < 3:
                    return False

            # Amount-based restrictions
            if "amount" in action_attributes:
                amount = action_attributes["amount"]
                max_amount = subject_attributes.get("max_transaction_amount", 0)
                if amount > max_amount:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"ABAC policy evaluation error: {str(e)}")
            return False
