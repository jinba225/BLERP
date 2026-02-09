"""
RBAC decorators and utility functions.

This module provides decorators for role and permission checking.
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from users.models import UserRole, Permission

User = get_user_model()


def require_roles(*role_codes):
    """
    Decorator to require specific roles.

    Usage:
        @require_roles('admin', 'manager')
        def my_view(request):
            return JsonResponse({'message': 'Authorized'})
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({"error": "未登录或认证失败"}, status=401)

            user_roles = UserRole.objects.filter(
                user=request.user, role__code__in=role_codes, is_active=True
            )

            if not user_roles.exists():
                return JsonResponse({"error": f'需要 {", ".join(role_codes)} 角色'}, status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def require_permissions(*permission_codes):
    """
    Decorator to require specific permissions.

    Usage:
        @require_permissions('users.manage', 'users.delete')
        def my_view(request):
            return JsonResponse({'message': 'Authorized'})
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({"error": "未登录或认证失败"}, status=401)

            user_permissions = Permission.objects.filter(
                userrole__user=request.user,
                userrole__is_active=True,
                role__permissions__code__in=permission_codes,
                is_active=True,
            )

            if not user_permissions.exists():
                return JsonResponse({"error": f'需要 {", ".join(permission_codes)} 权限'}, status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def has_role(user, role_code):
    """
    Check if user has a specific role.

    Args:
        user: User instance
        role_code: Role code to check

    Returns:
        bool: True if user has the role
    """
    return UserRole.objects.filter(user=user, role__code=role_code, is_active=True).exists()


def has_permission(user, permission_code):
    """
    Check if user has a specific permission.

    Args:
        user: User instance
        permission_code: Permission code to check

    Returns:
        bool: True if user has the permission
    """
    return Permission.objects.filter(
        userrole__user=user,
        userrole__is_active=True,
        role__permissions__code=permission_code,
        is_active=True,
    ).exists()


def get_user_roles(user):
    """
    Get all active roles for a user.

    Args:
        user: User instance

    Returns:
        QuerySet: User's active roles
    """
    return UserRole.objects.filter(user=user, is_active=True).select_related("role")


def get_user_permissions(user):
    """
    Get all permissions for a user.

    Args:
        user: User instance

    Returns:
        QuerySet: User's permissions
    """
    return Permission.objects.filter(
        userrole__user=user,
        userrole__is_active=True,
        role__permissions__is_active=True,
        is_active=True,
    ).distinct()


def is_admin(user):
    """Check if user is an admin."""
    return has_role(user, "admin") or has_role(user, "superadmin")


def is_manager(user):
    """Check if user is a manager."""
    return has_role(user, "manager") or is_admin(user)


def get_user_department_id(user):
    """
    Get user's department ID.

    Args:
        user: User instance

    Returns:
        int: Department ID or None
    """
    return user.department_id if user.department else None


def can_access_department_data(user, target_department_id):
    """
    Check if user can access data from target department.

    Args:
        user: User instance
        target_department_id: Department ID to check

    Returns:
        bool: True if user can access the department data
    """
    if is_admin(user):
        return True

    if is_manager(user) and get_user_department_id(user) == target_department_id:
        return True

    if get_user_department_id(user) == target_department_id:
        return True

    return False
