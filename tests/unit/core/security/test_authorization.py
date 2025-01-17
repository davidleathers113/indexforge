"""Unit tests for authorization functionality."""

from uuid import UUID, uuid4

import pytest

from src.core.security.authorization import (
    AuthorizationManager,
    Permission,
    PermissionDeniedError,
    ResourcePolicy,
    ResourceType,
    Role,
)


@pytest.fixture
def auth_manager():
    """Create test authorization manager."""
    return AuthorizationManager()


@pytest.fixture
def test_role():
    """Create test role with basic permissions."""
    return Role(
        id=uuid4(),
        name="test_role",
        description="Test role",
        permissions={
            ResourceType.DOCUMENT: {Permission.READ, Permission.CREATE},
            ResourceType.CHUNK: {Permission.READ},
        },
    )


@pytest.fixture
def admin_role():
    """Create admin role with full permissions."""
    return Role(
        id=uuid4(),
        name="admin",
        description="Admin role",
        permissions={resource_type: {Permission.MANAGE} for resource_type in ResourceType},
    )


@pytest.fixture
def test_policy(test_role):
    """Create test resource policy."""
    return ResourcePolicy(
        resource_id=uuid4(),
        resource_type=ResourceType.DOCUMENT,
        owner_id=uuid4(),
        allowed_roles={test_role.id},
        allowed_users=set(),
        public=False,
    )


def test_role_permission_checking(test_role):
    """Test role permission checking."""
    # Test allowed permissions
    assert test_role.has_permission(ResourceType.DOCUMENT, Permission.READ)
    assert test_role.has_permission(ResourceType.DOCUMENT, Permission.CREATE)
    assert test_role.has_permission(ResourceType.CHUNK, Permission.READ)

    # Test denied permissions
    assert not test_role.has_permission(ResourceType.DOCUMENT, Permission.UPDATE)
    assert not test_role.has_permission(ResourceType.DOCUMENT, Permission.DELETE)
    assert not test_role.has_permission(ResourceType.CHUNK, Permission.CREATE)
    assert not test_role.has_permission(ResourceType.REFERENCE, Permission.READ)


def test_manage_permission(admin_role):
    """Test MANAGE permission implies all permissions."""
    for resource_type in ResourceType:
        for permission in Permission:
            assert admin_role.has_permission(resource_type, permission)


@pytest.mark.asyncio
async def test_role_inheritance(auth_manager):
    """Test role inheritance."""
    # Create parent role
    parent_role = Role(
        id=uuid4(),
        name="parent",
        permissions={
            ResourceType.DOCUMENT: {Permission.READ},
        },
    )
    await auth_manager.add_role(parent_role)

    # Create child role
    child_role = Role(
        id=uuid4(),
        name="child",
        permissions={
            ResourceType.CHUNK: {Permission.READ},
        },
        parent_role=parent_role.id,
    )
    await auth_manager.add_role(child_role)

    # Test effective roles
    effective_roles = auth_manager._get_effective_roles({child_role.id})
    assert effective_roles == {child_role.id, parent_role.id}


@pytest.mark.asyncio
async def test_role_management(auth_manager, test_role):
    """Test role management operations."""
    # Add role
    await auth_manager.add_role(test_role)
    assert test_role.id in auth_manager._roles

    # Remove role
    await auth_manager.remove_role(test_role.id)
    assert test_role.id not in auth_manager._roles

    # Remove non-existent role
    with pytest.raises(KeyError):
        await auth_manager.remove_role(uuid4())


@pytest.mark.asyncio
async def test_user_role_assignment(auth_manager, test_role):
    """Test user role assignment."""
    user_id = uuid4()

    # Add role
    await auth_manager.add_role(test_role)

    # Assign role to user
    await auth_manager.assign_role(user_id, test_role.id)
    assert user_id in auth_manager._user_roles
    assert test_role.id in auth_manager._user_roles[user_id]

    # Assign non-existent role
    with pytest.raises(KeyError):
        await auth_manager.assign_role(user_id, uuid4())

    # Revoke role
    await auth_manager.revoke_role(user_id, test_role.id)
    assert test_role.id not in auth_manager._user_roles[user_id]


@pytest.mark.asyncio
async def test_resource_policy_management(auth_manager, test_policy):
    """Test resource policy management."""
    # Set policy
    await auth_manager.set_resource_policy(test_policy)
    assert test_policy.resource_id in auth_manager._resource_policies

    # Remove policy
    await auth_manager.remove_resource_policy(test_policy.resource_id)
    assert test_policy.resource_id not in auth_manager._resource_policies

    # Remove non-existent policy (should not raise)
    await auth_manager.remove_resource_policy(uuid4())


@pytest.mark.asyncio
async def test_permission_checking(auth_manager, test_role, test_policy):
    """Test permission checking."""
    user_id = uuid4()

    # Add role and policy
    await auth_manager.add_role(test_role)
    await auth_manager.set_resource_policy(test_policy)
    await auth_manager.assign_role(user_id, test_role.id)

    # Test allowed permissions
    assert await auth_manager.check_permission(
        user_id,
        test_policy.resource_id,
        Permission.READ,
    )
    assert await auth_manager.check_permission(
        user_id,
        test_policy.resource_id,
        Permission.CREATE,
    )

    # Test denied permissions
    assert not await auth_manager.check_permission(
        user_id,
        test_policy.resource_id,
        Permission.UPDATE,
    )
    assert not await auth_manager.check_permission(
        user_id,
        test_policy.resource_id,
        Permission.DELETE,
    )


@pytest.mark.asyncio
async def test_permission_enforcement(auth_manager, test_role, test_policy):
    """Test permission enforcement."""
    user_id = uuid4()

    # Add role and policy
    await auth_manager.add_role(test_role)
    await auth_manager.set_resource_policy(test_policy)
    await auth_manager.assign_role(user_id, test_role.id)

    # Test allowed permission
    await auth_manager.enforce_permission(
        user_id,
        test_policy.resource_id,
        Permission.READ,
    )

    # Test denied permission
    with pytest.raises(PermissionDeniedError):
        await auth_manager.enforce_permission(
            user_id,
            test_policy.resource_id,
            Permission.UPDATE,
        )


@pytest.mark.asyncio
async def test_public_resource_access(auth_manager):
    """Test public resource access."""
    user_id = uuid4()
    resource_id = uuid4()

    # Create public resource policy
    policy = ResourcePolicy(
        resource_id=resource_id,
        resource_type=ResourceType.DOCUMENT,
        owner_id=uuid4(),
        allowed_roles=set(),
        allowed_users=set(),
        public=True,
    )
    await auth_manager.set_resource_policy(policy)

    # Test public read access
    assert await auth_manager.check_permission(
        user_id,
        resource_id,
        Permission.READ,
    )

    # Test other permissions denied
    assert not await auth_manager.check_permission(
        user_id,
        resource_id,
        Permission.CREATE,
    )
    assert not await auth_manager.check_permission(
        user_id,
        resource_id,
        Permission.UPDATE,
    )
    assert not await auth_manager.check_permission(
        user_id,
        resource_id,
        Permission.DELETE,
    )


@pytest.mark.asyncio
async def test_owner_access(auth_manager):
    """Test resource owner access."""
    owner_id = uuid4()
    resource_id = uuid4()

    # Create resource policy
    policy = ResourcePolicy(
        resource_id=resource_id,
        resource_type=ResourceType.DOCUMENT,
        owner_id=owner_id,
        allowed_roles=set(),
        allowed_users=set(),
    )
    await auth_manager.set_resource_policy(policy)

    # Test owner has full access
    for permission in Permission:
        assert await auth_manager.check_permission(
            owner_id,
            resource_id,
            permission,
        )

    # Test non-owner has no access
    other_user_id = uuid4()
    for permission in Permission:
        assert not await auth_manager.check_permission(
            other_user_id,
            resource_id,
            permission,
        )
