"""
Users management views for the ERP system.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from .models import User, Role, UserRole, Permission, UserProfile, LoginLog

# 配置日志
logger = logging.getLogger(__name__)


# ============================================
# User Management Views (用户管理)
# ============================================

@login_required
def user_list(request):
    """
    List all users with search and filter capabilities.
    """
    users = User.objects.all()

    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_id__icontains=search)
        )

    # Filter by department
    department_id = request.GET.get('department', '')
    if department_id:
        users = users.filter(department_id=department_id)

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        users = users.filter(is_active=is_active == 'true')

    # Filter by staff status
    is_staff = request.GET.get('is_staff', '')
    if is_staff:
        users = users.filter(is_staff=is_staff == 'true')

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    users = users.order_by(sort)

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get departments for filter
    from departments.models import Department
    departments = Department.objects.filter(is_deleted=False)

    # Calculate statistics for the current queryset
    all_users = users  # The filtered queryset before pagination
    active_count = all_users.filter(is_active=True).count()
    staff_count = all_users.filter(is_staff=True).count()
    inactive_count = all_users.filter(is_active=False).count()

    context = {
        'page_obj': page_obj,
        'search': search,
        'department_id': department_id,
        'is_active': is_active,
        'is_staff': is_staff,
        'total_count': paginator.count,
        'active_count': active_count,
        'staff_count': staff_count,
        'inactive_count': inactive_count,
        'departments': departments,
    }
    return render(request, 'modules/users/user_list.html', context)


@login_required
def user_detail(request, pk):
    """
    Display user details.
    """
    user = get_object_or_404(User, pk=pk)

    # Get user roles
    user_roles = UserRole.objects.filter(user=user, is_deleted=False).select_related('role')

    # Get recent login logs
    recent_logins = LoginLog.objects.filter(user=user).order_by('-login_time')[:10]

    context = {
        'user': user,
        'user_roles': user_roles,
        'recent_logins': recent_logins,
    }
    return render(request, 'modules/users/user_detail.html', context)


@login_required
@transaction.atomic
def user_create(request):
    """
    Create a new user.
    """
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'phone': request.POST.get('phone', ''),
            'employee_id': request.POST.get('employee_id', ''),
            'position': request.POST.get('position', ''),
            'gender': request.POST.get('gender', ''),
            'is_active': request.POST.get('is_active') == 'on',
            'is_staff': request.POST.get('is_staff') == 'on',
        }

        # Handle optional fields
        department_id = request.POST.get('department')
        if department_id:
            data['department_id'] = department_id

        manager_id = request.POST.get('manager')
        if manager_id:
            data['manager_id'] = manager_id

        hire_date = request.POST.get('hire_date')
        if hire_date:
            data['hire_date'] = hire_date

        birth_date = request.POST.get('birth_date')
        if birth_date:
            data['birth_date'] = birth_date

        # Password
        password = request.POST.get('password')
        if not password:
            messages.error(request, '密码不能为空')
            return redirect('users:user_create')

        try:
            user = User(**data)
            user.password = make_password(password)
            user.save()

            messages.success(request, f'用户 {user.username} 创建成功！请前往角色管理为用户分配角色。')
            return redirect('users:user_detail', pk=user.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request
    from departments.models import Department
    departments = Department.objects.filter(is_deleted=False)
    managers = User.objects.filter(is_active=True, is_staff=True)
    roles = Role.objects.filter(is_deleted=False, is_active=True)

    context = {
        'action': 'create',
        'departments': departments,
        'managers': managers,
        'roles': roles,
        'gender_choices': User.GENDER_CHOICES,
    }
    return render(request, 'modules/users/user_form.html', context)


@login_required
@transaction.atomic
def user_update(request, pk):
    """
    Update an existing user.
    """
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.employee_id = request.POST.get('employee_id', '')
        user.position = request.POST.get('position', '')
        user.gender = request.POST.get('gender', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'

        # Handle optional fields
        department_id = request.POST.get('department')
        user.department_id = department_id if department_id else None

        manager_id = request.POST.get('manager')
        user.manager_id = manager_id if manager_id else None

        hire_date = request.POST.get('hire_date')
        user.hire_date = hire_date if hire_date else None

        birth_date = request.POST.get('birth_date')
        user.birth_date = birth_date if birth_date else None

        # Update password if provided
        password = request.POST.get('password')
        if password:
            user.password = make_password(password)

        try:
            user.save()

            messages.success(request, f'用户 {user.username} 更新成功！')
            return redirect('users:user_detail', pk=user.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request
    from departments.models import Department
    departments = Department.objects.filter(is_deleted=False)
    managers = User.objects.filter(is_active=True, is_staff=True).exclude(pk=user.pk)
    roles = Role.objects.filter(is_deleted=False, is_active=True)

    # Get current user roles
    current_role_ids = UserRole.objects.filter(user=user, is_deleted=False).values_list('role_id', flat=True)

    context = {
        'user': user,
        'action': 'update',
        'departments': departments,
        'managers': managers,
        'roles': roles,
        'current_role_ids': list(current_role_ids),
        'gender_choices': User.GENDER_CHOICES,
    }
    return render(request, 'modules/users/user_form.html', context)


@login_required
@transaction.atomic
def user_delete(request, pk):
    """
    Delete a user.
    Only inactive users can be deleted.
    """
    user = get_object_or_404(User, pk=pk)

    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, '不能删除自己的账号')
        return redirect('users:user_detail', pk=pk)

    # Only allow deleting inactive users
    if user.is_active:
        messages.error(request, '只能删除已停用的用户，请先停用该用户后再删除')
        return redirect('users:user_detail', pk=pk)

    if request.method == 'POST':
        username = user.username
        user.delete()

        messages.success(request, f'用户 {username} 已删除')
        return redirect('users:user_list')

    context = {
        'user': user,
    }
    return render(request, 'modules/users/user_confirm_delete.html', context)


@login_required
@transaction.atomic
def user_toggle_status(request, pk):
    """
    Toggle user active status.
    """
    user = get_object_or_404(User, pk=pk)

    # Prevent disabling yourself
    if user.id == request.user.id and user.is_active:
        messages.error(request, '不能停用自己的账号')
        return redirect('users:user_detail', pk=pk)

    user.is_active = not user.is_active
    user.save()

    status = '启用' if user.is_active else '停用'
    messages.success(request, f'用户 {user.username} 已{status}')
    return redirect('users:user_detail', pk=pk)


# ============================================
# Role Management Views (角色管理)
# ============================================

@login_required
def role_list(request):
    """
    List all roles with search and filter capabilities.
    """
    roles = Role.objects.filter(is_deleted=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        roles = roles.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        roles = roles.filter(is_active=is_active == 'true')

    # Annotate with user count
    roles = roles.annotate(user_count=Count('userrole'))

    # Sorting
    sort = request.GET.get('sort', 'name')
    roles = roles.order_by(sort)

    # Pagination
    paginator = Paginator(roles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate statistics for the current queryset
    all_roles = roles  # The filtered queryset before pagination
    active_count = all_roles.filter(is_active=True).count()
    inactive_count = all_roles.filter(is_active=False).count()

    context = {
        'page_obj': page_obj,
        'search': search,
        'is_active': is_active,
        'total_count': paginator.count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }
    return render(request, 'modules/users/role_list.html', context)


@login_required
def role_detail(request, pk):
    """
    Display role details.
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)

    # Get users with this role
    user_roles = UserRole.objects.filter(role=role, is_deleted=False).select_related('user')[:20]

    context = {
        'role': role,
        'user_roles': user_roles,
        'user_count': UserRole.objects.filter(role=role, is_deleted=False).count(),
    }
    return render(request, 'modules/users/role_detail.html', context)


@login_required
@transaction.atomic
def role_create(request):
    """
    Create a new role.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'code': request.POST.get('code'),
            'description': request.POST.get('description', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }

        try:
            role = Role(**data)
            role.created_by = request.user
            role.save()

            messages.success(request, f'角色 {role.name} 创建成功！')
            return redirect('users:role_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    context = {
        'action': 'create',
    }
    return render(request, 'modules/users/role_form.html', context)


@login_required
@transaction.atomic
def role_update(request, pk):
    """
    Update an existing role.
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)

    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.code = request.POST.get('code')
        role.description = request.POST.get('description', '')
        role.is_active = request.POST.get('is_active') == 'on'
        role.updated_by = request.user

        try:
            role.save()
            messages.success(request, f'角色 {role.name} 更新成功！')
            return redirect('users:role_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    context = {
        'role': role,
        'action': 'update',
    }
    return render(request, 'modules/users/role_form.html', context)


@login_required
def role_delete(request, pk):
    """
    Delete (soft delete) a role.
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)

    # Check if role is being used
    user_count = UserRole.objects.filter(role=role, is_deleted=False).count()

    if request.method == 'POST':
        if user_count > 0:
            messages.error(request, f'无法删除：该角色正在被 {user_count} 个用户使用')
            return redirect('users:role_detail', pk=pk)

        role.is_deleted = True
        role.deleted_at = timezone.now()
        role.deleted_by = request.user
        role.save()

        messages.success(request, f'角色 {role.name} 已删除')
        return redirect('users:role_list')

    context = {
        'role': role,
        'user_count': user_count,
    }
    return render(request, 'modules/users/role_confirm_delete.html', context)


@login_required
def role_permissions(request, pk):
    """
    Manage permissions and users for a role (统一管理角色权限和用户).
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)

    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    if request.method == 'POST':
        # Determine which form was submitted
        action = request.POST.get('action', 'save_permissions')

        if action == 'save_permissions':
            # Handle permission updates
            selected_permissions = request.POST.getlist('permissions')

            try:
                # Clear existing permissions
                role.permissions.clear()

                # Add new permissions
                if selected_permissions:
                    permissions = Permission.objects.filter(id__in=selected_permissions)
                    role.permissions.add(*permissions)

                # Update permissions for all users with this role
                user_roles = UserRole.objects.filter(role=role).select_related('user')
                for user_role in user_roles:
                    user = user_role.user
                    # Clear and re-add permissions from all active roles
                    user.user_permissions.clear()
                    active_roles = UserRole.objects.filter(user=user).select_related('role').filter(role__is_active=True)

                    for ur in active_roles:
                        user.user_permissions.add(*ur.role.permissions.all())

                messages.success(request, f'角色 {role.name} 的权限已更新！')
                return redirect('users:role_permissions', pk=role.pk)
            except Exception as e:
                messages.error(request, f'权限更新失败：{str(e)}')

        elif action == 'add_users':
            # Handle adding users to role
            selected_users = request.POST.getlist('users')

            try:
                added_count = 0
                for user_id in selected_users:
                    # Check if relationship already exists
                    if not UserRole.objects.filter(user_id=user_id, role=role).exists():
                        user = User.objects.get(pk=user_id)
                        UserRole.objects.create(
                            user=user,
                            role=role,
                            created_by=request.user
                        )
                        # Add role permissions to user
                        user.user_permissions.add(*role.permissions.all())
                        added_count += 1

                messages.success(request, f'成功为角色 {role.name} 添加了 {added_count} 个用户！')
                return redirect('users:role_permissions', pk=role.pk)
            except Exception as e:
                messages.error(request, f'添加用户失败：{str(e)}')

        elif action == 'remove_user':
            # Handle removing a user from role
            user_id = request.POST.get('user_id')

            try:
                user = User.objects.get(pk=user_id)
                # Remove user-role relationship
                UserRole.objects.filter(user=user, role=role).delete()

                # Recalculate user permissions from remaining roles
                user.user_permissions.clear()
                remaining_roles = UserRole.objects.filter(user=user).select_related('role')
                for user_role in remaining_roles:
                    if user_role.role.is_active:
                        user.user_permissions.add(*user_role.role.permissions.all())

                messages.success(request, f'已将用户 {user.username} 从角色 {role.name} 中移除！')
                return redirect('users:role_permissions', pk=role.pk)
            except Exception as e:
                messages.error(request, f'移除用户失败：{str(e)}')

    # GET request - organize permissions by app and model
    all_permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label',
        'content_type__model',
        'codename'
    )

    # Group permissions by app
    permissions_by_app = {}
    for perm in all_permissions:
        app_label = perm.content_type.app_label
        model_name = perm.content_type.model

        # Skip some system apps
        if app_label in ['admin', 'contenttypes', 'sessions']:
            continue

        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = {}

        if model_name not in permissions_by_app[app_label]:
            permissions_by_app[app_label][model_name] = []

        permissions_by_app[app_label][model_name].append(perm)

    # Get current role permissions
    current_permission_ids = list(role.permissions.values_list('id', flat=True))

    # Get current users with this role
    current_users = UserRole.objects.filter(role=role).select_related('user').order_by('user__username')

    # Get users that don't have this role yet (for adding)
    assigned_user_ids = UserRole.objects.filter(role=role).values_list('user_id', flat=True)
    available_users = User.objects.filter(is_active=True).exclude(id__in=assigned_user_ids).order_by('username')

    # Search functionality for available users
    search = request.GET.get('search', '')
    if search:
        available_users = available_users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_id__icontains=search)
        )

    context = {
        'role': role,
        'permissions_by_app': permissions_by_app,
        'current_permission_ids': current_permission_ids,
        'current_users': current_users,
        'available_users': available_users,
        'search': search,
        'user_count': current_users.count(),
    }
    return render(request, 'modules/users/role_permissions.html', context)


# ============================================
# Login Log Views (登录日志)
# ============================================

@login_required
def role_assign_users(request, pk):
    """
    Assign users to a role (批量分配用户到角色).
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)

    if request.method == 'POST':
        # Get selected users
        selected_users = request.POST.getlist('users')

        try:
            # Add new user-role relationships
            added_count = 0
            for user_id in selected_users:
                # Check if relationship already exists
                if not UserRole.objects.filter(user_id=user_id, role=role).exists():
                    user = User.objects.get(pk=user_id)
                    UserRole.objects.create(
                        user=user,
                        role=role,
                        created_by=request.user
                    )
                    # Add role permissions to user
                    user.user_permissions.add(*role.permissions.all())
                    added_count += 1

            messages.success(request, f'成功为角色 {role.name} 添加了 {added_count} 个用户！')
            return redirect('users:role_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f'添加失败：{str(e)}')

    # GET request - show user selection page
    # Get users that don't have this role yet
    assigned_user_ids = UserRole.objects.filter(role=role).values_list('user_id', flat=True)
    available_users = User.objects.filter(is_active=True).exclude(id__in=assigned_user_ids).order_by('username')

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        available_users = available_users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(employee_id__icontains=search)
        )

    context = {
        'role': role,
        'available_users': available_users,
        'search': search,
    }
    return render(request, 'modules/users/role_assign_users.html', context)


@login_required
def role_remove_user(request, pk, user_id):
    """
    Remove a user from a role (从角色移除用户).
    """
    role = get_object_or_404(Role, pk=pk, is_deleted=False)
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        try:
            # Remove user-role relationship
            UserRole.objects.filter(user=user, role=role).delete()

            # Recalculate user permissions from remaining roles
            user.user_permissions.clear()
            remaining_roles = UserRole.objects.filter(user=user).select_related('role')
            for user_role in remaining_roles:
                if user_role.role.is_active:
                    user.user_permissions.add(*user_role.role.permissions.all())

            messages.success(request, f'已将用户 {user.username} 从角色 {role.name} 中移除！')
            return redirect('users:role_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f'移除失败：{str(e)}')

    context = {
        'role': role,
        'user': user,
    }
    return render(request, 'modules/users/role_remove_user_confirm.html', context)


@login_required
def login_log_list(request):
    """
    List login logs with filter capabilities.
    """
    logs = LoginLog.objects.all().select_related('user')

    # Filter by user
    user_id = request.GET.get('user', '')
    if user_id:
        logs = logs.filter(user_id=user_id)

    # Filter by success status
    is_successful = request.GET.get('is_successful', '')
    if is_successful:
        logs = logs.filter(is_successful=is_successful == 'true')

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(login_time__gte=date_from)
    if date_to:
        logs = logs.filter(login_time__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get users for filter
    users = User.objects.filter(is_active=True).order_by('username')[:100]

    # Calculate statistics for the current queryset
    all_logs = logs  # The filtered queryset before pagination
    successful_count = all_logs.filter(is_successful=True).count()
    failed_count = all_logs.filter(is_successful=False).count()
    current_page_count = len(page_obj)

    context = {
        'page_obj': page_obj,
        'user_id': user_id,
        'is_successful': is_successful,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': paginator.count,
        'successful_count': successful_count,
        'failed_count': failed_count,
        'current_page_count': current_page_count,
        'users': users,
    }
    return render(request, 'modules/users/login_log_list.html', context)
