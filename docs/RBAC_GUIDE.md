# RBAC (基于角色的访问控制) 使用指南

## 概述

BetterLaser ERP系统实现了完整的RBAC（Role-Based Access Control）权限控制系统，支持：
- 基于角色的访问控制
- 基于权限代码的访问控制
- 基于部门的数据级权限控制
- 自定义权限装饰器

## 核心组件

### 1. 权限类 (users/permissions.py)

#### RolePermission
检查用户是否具有特定角色。

```python
from users.permissions import RolePermission
from rest_framework import viewsets

class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [RolePermission]
    required_roles = ['admin', 'manager']  # 需要admin或manager角色
```

#### PermissionCodePermission
检查用户是否具有特定权限代码。

```python
from users.permissions import PermissionCodePermission

class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [PermissionCodePermission]
    required_permissions = ['users.manage', 'users.delete']  # 需要特定权限
```

#### DepartmentDataPermission
基于部门的数据级权限控制。

```python
from users.permissions import DepartmentDataPermission

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [DepartmentDataPermission]
    # admin/manager: 可以看到所有数据
    # 其他用户: 只能看到自己部门的数据
    # 无部门用户: 只能看到自己的数据
```

#### IsAdminOrReadOnly
管理员可编辑，其他用户只读。

```python
from users.permissions import IsAdminOrReadOnly

class ConfigViewSet(viewsets.ModelViewSet):
    queryset = SystemConfig.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [IsAdminOrReadOnly]
```

#### IsOwnerOrReadOnly
所有者可编辑，其他用户只读。

```python
from users.permissions import IsOwnerOrReadOnly

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
```

### 2. 装饰器 (utils/rbac.py)

#### @require_roles
检查特定角色。

```python
from utils.rbac import require_roles
from django.http import JsonResponse

@require_roles('admin', 'superadmin')
def sensitive_operation(request):
    # 只有admin或superadmin角色可以访问
    return JsonResponse({'message': '操作成功'})
```

#### @require_permissions
检查特定权限。

```python
from utils.rbac import require_permissions

@require_permissions('users.delete', 'users.manage')
def delete_user(request, user_id):
    # 需要users.delete和users.manage权限
    return JsonResponse({'message': '用户已删除'})
```

### 3. 工具函数 (utils/rbac.py)

#### 检查角色和权限

```python
from utils.rbac import has_role, has_permission, is_admin, is_manager

# 检查用户是否有特定角色
if has_role(user, 'admin'):
    pass

# 检查用户是否有特定权限
if has_permission(user, 'users.manage'):
    pass

# 检查用户是否为管理员
if is_admin(user):
    pass

# 检查用户是否为经理
if is_manager(user):
    pass
```

#### 获取用户角色和权限

```python
from utils.rbac import get_user_roles, get_user_permissions

# 获取用户的所有角色
roles = get_user_roles(user)
for user_role in roles:
    print(user_role.role.name)

# 获取用户的所有权限
permissions = get_user_permissions(user)
for perm in permissions:
    print(perm.name)
```

#### 部门数据权限检查

```python
from utils.rbac import can_access_department_data, get_user_department_id

# 获取用户部门ID
dept_id = get_user_department_id(user)

# 检查用户是否可以访问目标部门的数据
if can_access_department_data(user, target_dept_id):
    pass
```

## 默认角色

系统预定义了以下角色：

### superadmin (超级管理员)
- 拥有所有权限
- 可以访问所有数据和功能

### admin (管理员)
- 拥有大部分管理权限
- 不包括AI助手相关权限

### manager (部门经理)
- 管理本部门的数据
- 包括客户、供应商、产品、库存、销售、采购、财务等模块

### employee (普通员工)
- 基本业务操作权限
- 包括产品、库存、销售、采购、AI助手等模块

### guest (访客)
- 只读权限
- 只能查看客户和产品信息

## 默认权限

系统预定义了以下权限类别：

### 用户管理
- `users.manage` - 用户管理菜单
- `users.view` - 查看用户
- `users.create` - 创建用户
- `users.edit` - 编辑用户
- `users.delete` - 删除用户

### 客户管理
- `customers.manage` - 客户管理菜单
- `customers.view` - 查看客户
- `customers.edit` - 编辑客户

### 供应商管理
- `suppliers.manage` - 供应商管理

### 产品管理
- `products.manage` - 产品管理

### 库存管理
- `inventory.manage` - 库存管理

### 销售管理
- `sales.manage` - 销售管理

### 采购管理
- `purchase.manage` - 采购管理

### 财务管理
- `finance.manage` - 财务管理

### 部门管理
- `departments.manage` - 部门管理

### AI助手
- `ai_assistant.use` - 使用AI助手

## 使用示例

### 示例1: 创建需要管理员权限的API

```python
from rest_framework import viewsets
from users.permissions import RolePermission
from customers.models import Customer
from customers.serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [RolePermission]
    required_roles = ['admin', 'manager']

    def get_queryset(self):
        queryset = super().get_queryset()

        # 部门经理只能看到自己部门的客户
        if not is_admin(self.request.user):
            queryset = queryset.filter(department=self.request.user.department)

        return queryset
```

### 示例2: 创建需要特定权限的API

```python
from rest_framework import viewsets
from users.permissions import PermissionCodePermission

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [PermissionCodePermission]
    required_permissions = ['users.manage']

    def perform_create(self, serializer):
        # 只有users.manage权限才能创建用户
        serializer.save(created_by=self.request.user)
```

### 示例3: 在视图中使用装饰器

```python
from django.views import View
from django.http import JsonResponse
from utils.rbac import require_roles

class AdminDashboardView(View):
    @require_roles('admin', 'superadmin')
    def get(self, request):
        return JsonResponse({'message': '欢迎进入管理后台'})
```

### 示例4: 获取并检查用户权限

```python
from utils.rbac import get_user_permissions, has_permission

def my_view(request):
    permissions = get_user_permissions(request.user)
    user_permissions = [p.code for p in permissions]

    if 'users.delete' in user_permissions:
        # 显示删除按钮
        pass

    if 'finance.manage' in user_permissions:
        # 显示财务菜单
        pass
```

## 数据库迁移

运行以下命令创建默认角色和权限：

```bash
python manage.py migrate users
```

这将执行 `0002_create_default_roles_permissions` 迁移，创建：
- 5个默认角色
- 18个默认权限
- 角色与权限的关联关系

## 自定义角色和权限

### 创建自定义角色

```python
from users.models import Role

# 创建新角色
role = Role.objects.create(
    name='财务总监',
    code='finance_director',
    description='财务总监，拥有高级财务权限',
    is_active=True
)

# 添加权限
from users.models import Permission
finance_perms = Permission.objects.filter(module='finance')
role.permissions.add(*finance_perms)
```

### 创建自定义权限

```python
from users.models import Permission

# 创建新权限
permission = Permission.objects.create(
    name='财务审批',
    code='finance.approve',
    permission_type='operation',
    module='finance',
    description='审批财务单据',
    is_active=True
)
```

### 分配用户角色

```python
from users.models import UserRole, Role

# 为用户分配角色
user_role = UserRole.objects.create(
    user=user_instance,
    role=role_instance,
    is_active=True
)
```

## 最佳实践

1. **使用最严格的权限原则**
   - 默认拒绝访问
   - 只授予必要的最小权限

2. **优先使用权限代码而非角色**
   - 角色可能变化，但权限代码更稳定
   - 便于权限的细粒度控制

3. **在API层面和业务逻辑层面都做权限检查**
   - API层：使用permission_classes
   - 业务逻辑层：使用装饰器或工具函数

4. **记录权限检查日志**
   - 记录权限拒绝的访问尝试
   - 便于安全审计

5. **定期审查用户权限**
   - 定期检查用户角色和权限是否合理
   - 及时回收不必要的高权限

## 故障排查

### 权限检查失败

1. 检查用户是否登录
2. 检查用户是否分配了角色
3. 检查角色是否激活（is_active=True）
4. 检查角色是否分配了所需权限
5. 检查权限是否激活（is_active=True）

### 数据权限问题

1. 检查用户是否属于某个部门
2. 检查用户的部门是否正确
3. 检查数据对象的部门字段是否正确设置
4. 检查是否使用了DepartmentDataPermission

### 迁移问题

如果迁移失败，检查：
1. 数据库是否可以访问
2. users应用是否正确注册
3. Django和数据库版本是否兼容
