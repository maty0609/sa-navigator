"""Application role hierarchy and authorization dependencies."""

from enum import IntEnum, StrEnum


class AppRole(StrEnum):
    """User roles with implicit hierarchy: viewer < editor < admin."""

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class _RoleLevel(IntEnum):
    """Numeric levels for role comparison."""

    VIEWER = 0
    EDITOR = 1
    ADMIN = 2


def role_level(role: AppRole) -> int:
    """Return the numeric level for a role."""
    return _RoleLevel[role.name].value


def has_required_role(user_role: AppRole, required: AppRole) -> bool:
    """Check if *user_role* meets or exceeds *required*."""
    return role_level(user_role) >= role_level(required)
