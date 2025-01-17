"""Authorization infrastructure for IndexForge.

This module provides role-based access control (RBAC) functionality including:
- Role and permission management
- Access control enforcement
- Resource-level permissions
- Permission inheritance
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from src.core.errors import SecurityError


class AuthorizationError(SecurityError):
    """Base class for authorization errors."""


class PermissionDeniedError(AuthorizationError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class ResourceType(str, Enum):
    """Types of resources that can be protected."""

    DOCUMENT = "document"
    CHUNK = "chunk"
    REFERENCE = "reference"
    SCHEMA = "schema"
    USER = "user"
    ROLE = "role"


class Permission(str, Enum):
    """Available permissions for resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"  # Implies all permissions


class Role(BaseModel):
    """Role definition with associated permissions."""

    id: UUID
    name: str
    description: str | None = None
    permissions: dict[ResourceType, set[Permission]]
    parent_role: UUID | None = None

    def has_permission(
        self,
        resource_type: ResourceType,
        permission: Permission,
    ) -> bool:
        """Check if role has specific permission.

        Args:
            resource_type: Type of resource to check
            permission: Permission to check

        Returns:
            True if role has permission, False otherwise
        """
        if resource_type not in self.permissions:
            return False

        return (
            Permission.MANAGE in self.permissions[resource_type]
            or permission in self.permissions[resource_type]
        )


class ResourcePolicy(BaseModel):
    """Access policy for a specific resource."""

    resource_id: UUID
    resource_type: ResourceType
    owner_id: UUID
    allowed_roles: set[UUID]
    allowed_users: set[UUID]
    public: bool = False

    def can_access(
        self,
        user_id: UUID,
        user_roles: set[UUID],
        permission: Permission,
        roles_by_id: dict[UUID, Role],
    ) -> bool:
        """Check if user can access resource with given permission.

        Args:
            user_id: ID of user requesting access
            user_roles: Set of role IDs assigned to user
            permission: Requested permission
            roles_by_id: Dictionary of roles by ID for permission lookup

        Returns:
            True if access is allowed, False otherwise
        """
        # Public resources only allow read
        if self.public and permission == Permission.READ:
            return True

        # Owner has full access
        if user_id == self.owner_id:
            return True

        # Check user-specific access
        if user_id in self.allowed_users:
            return True

        # Check role-based access
        return any(
            role_id in self.allowed_roles
            and roles_by_id[role_id].has_permission(
                self.resource_type,
                permission,
            )
            for role_id in user_roles
            if role_id in roles_by_id
        )


class AuthorizationManager:
    """Manages role-based access control."""

    def __init__(self):
        """Initialize authorization manager."""
        self._roles: dict[UUID, Role] = {}
        self._user_roles: dict[UUID, set[UUID]] = {}
        self._resource_policies: dict[UUID, ResourcePolicy] = {}

    def _get_effective_roles(self, role_ids: set[UUID]) -> set[UUID]:
        """Get all roles including inherited ones.

        Args:
            role_ids: Initial set of role IDs

        Returns:
            Set of all role IDs including parents
        """
        result = set(role_ids)
        for role_id in role_ids:
            role = self._roles.get(role_id)
            if role and role.parent_role:
                result.update(self._get_effective_roles({role.parent_role}))
        return result

    async def add_role(self, role: Role) -> None:
        """Add or update role.

        Args:
            role: Role to add/update
        """
        self._roles[role.id] = role

    async def remove_role(self, role_id: UUID) -> None:
        """Remove role.

        Args:
            role_id: ID of role to remove

        Raises:
            KeyError: If role does not exist
        """
        if role_id not in self._roles:
            raise KeyError(f"Role {role_id} not found")

        # Remove role from all users
        for user_roles in self._user_roles.values():
            user_roles.discard(role_id)

        # Remove role from all resource policies
        for policy in self._resource_policies.values():
            policy.allowed_roles.discard(role_id)

        del self._roles[role_id]

    async def assign_role(self, user_id: UUID, role_id: UUID) -> None:
        """Assign role to user.

        Args:
            user_id: ID of user to assign role to
            role_id: ID of role to assign

        Raises:
            KeyError: If role does not exist
        """
        if role_id not in self._roles:
            raise KeyError(f"Role {role_id} not found")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()

        self._user_roles[user_id].add(role_id)

    async def revoke_role(self, user_id: UUID, role_id: UUID) -> None:
        """Revoke role from user.

        Args:
            user_id: ID of user to revoke role from
            role_id: ID of role to revoke
        """
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_id)

    async def set_resource_policy(self, policy: ResourcePolicy) -> None:
        """Set access policy for resource.

        Args:
            policy: Resource policy to set
        """
        self._resource_policies[policy.resource_id] = policy

    async def remove_resource_policy(self, resource_id: UUID) -> None:
        """Remove resource policy.

        Args:
            resource_id: ID of resource to remove policy for
        """
        self._resource_policies.pop(resource_id, None)

    async def check_permission(
        self,
        user_id: UUID,
        resource_id: UUID,
        permission: Permission,
    ) -> bool:
        """Check if user has permission for resource.

        Args:
            user_id: ID of user requesting access
            resource_id: ID of resource to check
            permission: Requested permission

        Returns:
            True if user has permission, False otherwise
        """
        # Get resource policy
        policy = self._resource_policies.get(resource_id)
        if not policy:
            return False

        # Get user roles including inherited ones
        user_roles = self._user_roles.get(user_id, set())
        effective_roles = self._get_effective_roles(user_roles)

        return policy.can_access(
            user_id,
            effective_roles,
            permission,
            self._roles,
        )

    async def enforce_permission(
        self,
        user_id: UUID,
        resource_id: UUID,
        permission: Permission,
    ) -> None:
        """Enforce permission check for resource.

        Args:
            user_id: ID of user requesting access
            resource_id: ID of resource to check
            permission: Requested permission

        Raises:
            PermissionDeniedError: If user lacks required permission
        """
        if not await self.check_permission(user_id, resource_id, permission):
            raise PermissionDeniedError(
                f"User {user_id} lacks {permission} permission for resource {resource_id}"
            )
