"""
RBAC (Role-Based Access Control) permissions for the ERP system.

This module provides fine-grained access control based on:
- User roles (Role)
- Custom permissions (Permission)
- Data-level permissions (department-based)
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class RolePermission(permissions.BasePermission):
    """
    Role-based permission check.

    Checks if user has the required role.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_roles = getattr(view, 'required_roles', None)
        if not required_roles:
            return True

        user_roles = UserRole.objects.filter(
            user=request.user,
            role__code__in=required_roles,
            is_active=True
        )

        return user_roles.exists()


class PermissionCodePermission(permissions.BasePermission):
    """
    Permission code-based check.

    Checks if user has the required permission code.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_permissions = getattr(view, 'required_permissions', None)
        if not required_permissions:
            return True

        user_permissions = Permission.objects.filter(
            userrole__user=request.user,
            userrole__is_active=True,
            role__permissions__code__in=required_permissions,
            is_active=True
        ).select_related('role')

        return user_permissions.exists()


class DepartmentDataPermission(permissions.BasePermission):
    """
    Department-based data permission.

    Allows users to:
    - See all data if they're in 'admin' or 'manager' role
    - See only their department's data otherwise
    - See only their own data if they don't belong to any department
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return self._can_read(request, obj)
        else:
            return self._can_write(request, obj)

    def _can_read(self, request, obj):
        """Check if user can read the object."""
        admin_roles = ['admin', 'superadmin', 'manager']
        has_admin_role = UserRole.objects.filter(
            user=request.user,
            role__code__in=admin_roles,
            is_active=True
        ).exists()

        if has_admin_role:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'department'):
            return obj.department == request.user.department

        return False

    def _can_write(self, request, obj):
        """Check if user can modify the object."""
        admin_roles = ['admin', 'superadmin']
        has_admin_role = UserRole.objects.filter(
            user=request.user,
            role__code__in=admin_roles,
            is_active=True
        ).exists()

        if has_admin_role:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'department'):
            manager_roles = ['manager', 'department_manager']
            is_manager = UserRole.objects.filter(
                user=request.user,
                role__code__in=manager_roles,
                is_active=True
            ).exists()

            if is_manager and obj.department == request.user.department:
                return True

            return obj.user == request.user

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows admin users to edit,
    but only allows read-only access for non-admin users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        admin_roles = ['admin', 'superadmin']
        has_admin_role = UserRole.objects.filter(
            user=request.user,
            role__code__in=admin_roles,
            is_active=True
        ).exists()

        return has_admin_role


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows owners to edit their own objects,
    but only allows read-only access for others.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False
