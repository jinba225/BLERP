"""
自定义权限检查帮助函数

提供统一的权限检查接口，支持自定义 Permission 模型
"""

from django.contrib.auth import get_user_model
from typing import List, Optional, Dict
from django.core.cache import cache

User = get_user_model()


def has_custom_permission(user: User, permission_code: str) -> bool:
    """
    检查用户是否有指定权限（自定义 Permission 模型）
    
    Args:
        user: 用户对象
        permission_code: 权限代码，格式："sales.add_order"
    
    Returns:
        bool: 是否有权限
    """
    if not user or user.is_anonymous:
        return False
    
    if user.is_superuser:
        return True
    
    if not user.is_active:
        return False
    
    try:
        from users.models import Permission, UserRole, Role
        
        # 尝试从缓存获取
        cache_key = f'user_custom_perms:{user.id}'
        cached_perms = cache.get(cache_key)
        
        if cached_perms is None:
            # 从数据库获取用户权限
            user_roles = UserRole.objects.filter(
                user=user,
                is_active=True,
                is_deleted=False
            ).select_related('role').all()
            
            perms = set()
            for user_role in user_roles:
                role = user_role.role
                if not role or not role.is_active:
                    continue
                
                # 获取角色的所有权限
                role_perms = role.permissions.filter(
                    is_active=True,
                    is_deleted=False
                ).values_list('code', flat=True)
                perms.update(role_perms)
            
            # 保存到缓存（缓存 1 小时）
            cache.set(cache_key, list(perms), 3600)
            cached_perms = list(perms)
        
        # 检查权限
        return permission_code in cached_perms
    
    except Exception as e:
        print(f"权限检查失败: {str(e)}")
        return False


def get_user_permissions(user: User) -> List[Dict[str, str]]:
    """
    获取用户的所有权限列表
    
    Args:
        user: 用户对象
    
    Returns:
        权限列表，每个元素格式：{code: 'sales.add_order', name: '销售订单添加', module: 'sales', type: 'operation'}
    """
    if not user or user.is_anonymous:
        return []
    
    if user.is_superuser:
        # 超级用户拥有所有权限
        from users.models import Permission
        return [
            {
                'code': perm.code,
                'name': perm.name,
                'module': perm.module,
                'type': perm.permission_type,
            }
            for perm in Permission.objects.filter(is_active=True, is_deleted=False)
        ]
    
    try:
        from users.models import Permission, UserRole, Role
        
        # 获取用户的所有角色
        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False
        ).select_related('role__permissions').all()
        
        # 获取权限（去重）
        perm_dict = {}
        for user_role in user_roles:
            role = user_role.role
            if not role or not role.is_active:
                continue
            
            for perm in role.permissions.filter(is_active=True, is_deleted=False):
                if perm.code not in perm_dict:
                    perm_dict[perm.code] = {
                        'code': perm.code,
                        'name': perm.name,
                        'module': perm.module,
                        'type': perm.permission_type,
                    }
        
        return sorted(perm_dict.values(), key=lambda x: (x['module'], x['code']))
    
    except Exception as e:
        print(f"获取用户权限失败: {str(e)}")
        return []


def get_user_roles(user: User) -> List[Dict[str, any]]:
    """
    获取用户的所有角色
    
    Args:
        user: 用户对象
    
    Returns:
        角色列表
    """
    if not user or user.is_anonymous:
        return []
    
    try:
        from users.models import UserRole, Role
        
        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False
        ).select_related('role').all()
        
        return [
            {
                'id': user_role.role.id,
                'name': user_role.role.name,
                'code': user_role.role.code,
                'description': user_role.role.description,
                'permission_count': user_role.role.permissions.filter(
                    is_active=True, 
                    is_deleted=False
                ).count(),
            }
            for user_role in user_roles
        ]
    
    except Exception as e:
        print(f"获取用户角色失败: {str(e)}")
        return []


def clear_user_permission_cache(user: User):
    """清除用户权限缓存"""
    cache_key = f'user_custom_perms:{user.id}'
    cache.delete(cache_key)
