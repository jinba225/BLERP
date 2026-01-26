"""
自定义认证后端

支持自定义权限模型
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.db.models import Q
from typing import List, Optional

User = get_user_model()


class CustomBackend(ModelBackend):
    """
    自定义认证后端
    
    支持自定义 Permission 模型（apps.users.models.Permission）
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """认证用户"""
        return super().authenticate(request, username, password, **kwargs)
    
    def _get_user_permissions(self, user_obj: User) -> dict:
        """
        获取用户的所有权限（缓存优化）
        
        Returns:
            权限字典 {permission_code: permission_name}
        """
        if not user_obj or user_obj.is_anonymous:
            return {}
        
        # 尝试从缓存获取
        cache_key = f'user_permissions:{user_obj.id}'
        cached_perms = cache.get(cache_key)
        if cached_perms:
            return cached_perms
        
        # 从数据库获取用户的自定义权限
        from apps.users.models import Permission, UserRole, Role
        
        try:
            permissions = {}
            
            # 获取用户的所有角色
            user_roles = UserRole.objects.filter(
                user=user_obj,
                is_active=True,
                is_deleted=False
            ).select_related('role')
            
            for user_role in user_roles:
                role = user_role.role
                if not role:
                    continue
                
                # 获取角色的所有权限
                role_perms = role.permissions.filter(is_active=True, is_deleted=False)
                for perm in role_perms:
                    if perm.is_active:
                        permissions[perm.code] = perm.name
            
            # 保存到缓存（缓存 1 小时）
            cache.set(cache_key, permissions, 3600)
            
            return permissions
        except Exception as e:
            print(f"获取用户权限失败: {str(e)}")
            return {}
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        检查用户是否有指定权限（自定义 Permission 模型）
        
        Args:
            user_obj: 用户对象
            perm: 权限字符串，格式："app_label.permission_code"，如 "sales.add_order"
            obj: 被查对象（用于对象级权限检查）
        
        Returns:
            bool: 是否有权限
        """
        if not user_obj or user_obj.is_anonymous:
            return user_obj and user_obj.is_superuser
        
        if not user_obj.is_active:
            return False
        
        # 获取用户权限
        user_perms = self._get_user_permissions(user_obj)
        
        # 检查权限
        perm_code = f"{perm.app_label}.{perm.codename}"
        return perm_code in user_perms
    
    def has_module_perms(self, user_obj):
        """检查用户是否有指定模块的权限"""
        if not user_obj or user_obj.is_anonymous:
            return user_obj and user_obj.is_superuser
        
        if not user_obj.is_active:
            return False
        
        user_perms = self._get_user_permissions(user_obj)
        
        # 检查模块级权限
        module_perms = [p for p in user_perms.keys() if '.' in p]
        
        return len(module_perms) > 0
    
    def get_all_permissions(self, user_obj: User) -> List[dict]:
        """
        获取用户的所有权限列表
        
        Args:
            user_obj: 用户对象
        
        Returns:
            权限列表，每个元素格式：{code: 'sales.add_order', name: '销售订单添加', module: 'sales'}
        """
        if not user_obj or user_obj.is_anonymous:
            return []
        
        from apps.users.models import Permission
        
        user_perms = self._get_user_permissions(user_obj)
        
        permissions_list = []
        for code, name in user_perms.items():
            try:
                app_label, perm_codename = code.rsplit('.', 1)
                perm_obj = Permission.objects.filter(
                    code=perm_codename,
                    module__in=[app_label],
                    is_active=True,
                    is_deleted=False
                ).first()
                
                if perm_obj:
                    permissions_list.append({
                        'code': code,
                        'name': perm_obj.name,
                        'module': app_label,
                        'permission_type': perm_obj.permission_type,
                    })
            except Exception:
                pass
        
        return sorted(permissions_list, key=lambda x: (x['module'], x['code']))
    
    def has_module_perm(self, user_obj, app_label: str, codename: str):
        """
        检查用户是否有指定模块的权限
        
        Args:
            user_obj: 用户对象
            app_label: 应用标签，如 'sales', 'customers', 'products', 'inventory', 'finance', 'reports'
            codename: 权限代号，如 'add_order', 'query_customer'
        
        Returns:
            bool: 是否有权限
        """
        if not user_obj or user_obj.is_anonymous:
            return user_obj and user_obj.is_superuser
        
        perm_code = f"{app_label}.{codename}"
        user_perms = self._get_user_permissions(user_obj)
        
        return perm_code in user_perms
    
    def get_user_roles(self, user_obj: User) -> List[dict]:
        """获取用户的所有角色"""
        if not user_obj or user_obj.is_anonymous:
            return []
        
        from apps.users.models import Role, UserRole, Permission
        
        try:
            # 获取用户的所有角色
            user_roles = UserRole.objects.filter(
                user=user_obj,
                is_active=True,
                is_deleted=False
            ).select_related('role__permissions').all()
            
            roles_list = []
            for user_role in user_roles:
                role = user_role.role
                if not role or not role.is_active:
                    continue
                
                # 获取角色的所有权限
                permissions = role.permissions.filter(is_active=True, is_deleted=False)
                
                perms_list.append({
                    'role_name': role.name,
                    'role_code': role.code,
                    'permission_count': permissions.count(),
                    'permissions': [
                        {
                            'code': perm.code,
                            'name': perm.name,
                            'module': perm.module,
                            'permission_type': perm.permission_type,
                        }
                        for perm in permissions
                    ]
                })
            
            return sorted(roles_list, key=lambda x: x['role_name'])
        
        except Exception as e:
            print(f"获取用户角色失败: {str(e)}")
            return []
