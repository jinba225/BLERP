"""
Users模块 - API测试
测试UserViewSet, RoleViewSet, UserRoleViewSet, PermissionViewSet, UserProfileViewSet, LoginLogViewSet的REST API端点
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.departments.models import Department
from apps.users.models import LoginLog, Permission, Role, UserProfile, UserRole

User = get_user_model()


class UsersAPITestCaseBase(APITestCase):
    """Users API测试基类 - 准备测试数据"""

    def setUp(self):
        """测试前准备 - 创建测试用户和认证"""
        # 创建部门
        self.department = Department.objects.create(
            name="技术部",
            code="TECH",
        )

        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            employee_id="EMP001",
            department=self.department,
            first_name="测试",
            last_name="用户",
        )

        # 创建管理员用户
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@example.com",
            employee_id="ADMIN001",
            department=self.department,
            first_name="管理",
            last_name="员",
        )

        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


class UserViewSetTestCase(UsersAPITestCaseBase):
    """UserViewSet API测试"""

    def setUp(self):
        super().setUp()
        # 创建更多测试用户
        self.user2 = User.objects.create_user(
            username="testuser2",
            password="testpass123",
            email="test2@example.com",
            employee_id="EMP002",
            department=self.department,
            is_active=False,
        )

    def test_list_users(self):
        """测试获取用户列表"""
        url = reverse("users:user-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 3)  # testuser, admin, testuser2

    def test_list_users_filter_by_is_active(self):
        """测试按激活状态过滤用户"""
        url = reverse("users:user-list")
        response = self.client.get(url, {"is_active": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证返回的用户都是激活状态
        for user in response.data["results"]:
            self.assertTrue(user["is_active"])

    def test_list_users_filter_by_department(self):
        """测试按部门过滤用户"""
        url = reverse("users:user-list")
        response = self.client.get(url, {"department": self.department.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 3)

    def test_list_users_search_by_username(self):
        """测试按用户名搜索用户"""
        url = reverse("users:user-list")
        response = self.client.get(url, {"search": "testuser2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "testuser2")

    def test_list_users_ordering(self):
        """测试用户列表排序"""
        url = reverse("users:user-list")
        response = self.client.get(url, {"ordering": "username"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证按用户名升序
        usernames = [u["username"] for u in response.data["results"]]
        self.assertEqual(usernames, sorted(usernames))

    def test_retrieve_user(self):
        """测试获取单个用户详情"""
        url = reverse("users:user-detail", args=[self.user.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["employee_id"], "EMP001")
        self.assertIn("display_name", response.data)
        self.assertIn("full_name", response.data)
        self.assertIn("department_name", response.data)

    def test_create_user(self):
        """测试创建用户"""
        url = reverse("users:user-list")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
            "employee_id": "EMP003",
            "department": self.department.pk,
            "first_name": "新",
            "last_name": "用户",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 验证数据库记录
        self.assertTrue(User.objects.filter(username="newuser").exists())
        new_user = User.objects.get(username="newuser")
        self.assertEqual(new_user.email, "newuser@example.com")

    def test_create_user_with_password_mismatch(self):
        """测试创建用户时密码不匹配"""
        url = reverse("users:user-list")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "different123",
            "employee_id": "EMP003",
            "department": self.department.pk,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_duplicate_email(self):
        """测试创建重复邮箱的用户（应该失败）"""
        url = reverse("users:user-list")
        data = {
            "username": "newuser",
            "email": "test@example.com",  # 已存在
            "password": "newpass123",
            "password_confirm": "newpass123",
            "employee_id": "EMP003",
            "department": self.department.pk,
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user(self):
        """测试更新用户信息"""
        url = reverse("users:user-detail", args=[self.user2.pk])
        data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "employee_id": "EMP002",
            "first_name": "更新",
            "last_name": "姓名",
            "phone": "13800138000",
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], "13800138000")

        # 验证数据库更新
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.phone, "13800138000")

    def test_partial_update_user(self):
        """测试部分更新用户信息"""
        url = reverse("users:user-detail", args=[self.user2.pk])
        data = {"position": "高级工程师"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["position"], "高级工程师")

    def test_delete_user(self):
        """测试删除用户"""
        url = reverse("users:user-detail", args=[self.user2.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # User模型不支持软删除，验证记录已被删除
        self.assertFalse(User.objects.filter(pk=self.user2.pk).exists())

    def test_set_password_action(self):
        """测试设置密码自定义动作"""
        url = reverse("users:user-set-password", args=[self.user2.pk])
        data = {"password": "newpassword123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # 验证密码已更改
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.check_password("newpassword123"))

    def test_set_password_action_empty_password(self):
        """测试设置空密码（应该失败）"""
        url = reverse("users:user-set-password", args=[self.user2.pk])
        data = {}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_user_action(self):
        """测试激活用户动作"""
        url = reverse("users:user-activate", args=[self.user2.pk])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # 验证用户已激活
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.is_active)

    def test_deactivate_user_action(self):
        """测试停用用户动作"""
        url = reverse("users:user-deactivate", args=[self.user.pk])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证用户已停用
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class RoleViewSetTestCase(UsersAPITestCaseBase):
    """RoleViewSet API测试"""

    def setUp(self):
        super().setUp()
        # 创建测试角色
        self.role1 = Role.objects.create(
            name="管理员", code="ADMIN", description="系统管理员角色", created_by=self.user
        )

        self.role2 = Role.objects.create(
            name="销售员", code="SALES", description="销售人员角色", is_active=False, created_by=self.user
        )

    def test_list_roles(self):
        """测试获取角色列表"""
        url = reverse("users:role-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_list_roles_filter_by_is_active(self):
        """测试按激活状态过滤角色"""
        url = reverse("users:role-list")
        response = self.client.get(url, {"is_active": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证都是激活状态
        for role in response.data["results"]:
            self.assertTrue(role["is_active"])

    def test_list_roles_search(self):
        """测试搜索角色"""
        url = reverse("users:role-list")
        response = self.client.get(url, {"search": "管理员"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_retrieve_role(self):
        """测试获取单个角色详情"""
        url = reverse("users:role-detail", args=[self.role1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "管理员")
        self.assertEqual(response.data["code"], "ADMIN")
        self.assertIn("permissions_count", response.data)

    def test_create_role(self):
        """测试创建角色"""
        url = reverse("users:role-list")
        data = {"name": "财务", "code": "FINANCE", "description": "财务人员角色", "is_active": True}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "财务")

        # 验证数据库记录
        self.assertTrue(Role.objects.filter(code="FINANCE").exists())

    def test_create_role_with_duplicate_code(self):
        """测试创建重复代码的角色（应该失败）"""
        url = reverse("users:role-list")
        data = {
            "name": "重复角色",
            "code": "ADMIN",  # 已存在
            "description": "测试重复",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_role(self):
        """测试更新角色信息"""
        url = reverse("users:role-detail", args=[self.role1.pk])
        data = {
            "name": "管理员",
            "code": "ADMIN",
            "description": "更新后的描述",
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "更新后的描述")

    def test_delete_role(self):
        """测试删除角色"""
        url = reverse("users:role-detail", args=[self.role2.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        self.role2.refresh_from_db()
        self.assertTrue(self.role2.is_deleted)

    def test_role_users_action(self):
        """测试获取角色下的用户"""
        # 先创建用户角色关联
        UserRole.objects.create(user=self.user, role=self.role1, created_by=self.user)

        url = reverse("users:role-users", args=[self.role1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)


class UserRoleViewSetTestCase(UsersAPITestCaseBase):
    """UserRoleViewSet API测试"""

    def setUp(self):
        super().setUp()
        # 创建测试角色
        self.role = Role.objects.create(name="测试角色", code="TEST", created_by=self.user)

        # 创建用户角色关联
        self.user_role1 = UserRole.objects.create(
            user=self.user, role=self.role, created_by=self.user
        )

    def test_list_user_roles(self):
        """测试获取用户角色列表"""
        url = reverse("users:userrole-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_list_user_roles_filter_by_user(self):
        """测试按用户过滤"""
        url = reverse("users:userrole-list")
        response = self.client.get(url, {"user": self.user.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_user_role(self):
        """测试获取单个用户角色详情"""
        url = reverse("users:userrole-detail", args=[self.user_role1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user_name", response.data)
        self.assertIn("role_name", response.data)

    def test_create_user_role(self):
        """测试创建用户角色关联"""
        role2 = Role.objects.create(name="角色2", code="ROLE2", created_by=self.user)

        url = reverse("users:userrole-list")
        data = {"user": self.admin_user.pk, "role": role2.pk, "is_active": True}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证数据库记录
        self.assertTrue(UserRole.objects.filter(user=self.admin_user, role=role2).exists())

    def test_delete_user_role(self):
        """测试删除用户角色关联"""
        url = reverse("users:userrole-detail", args=[self.user_role1.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        self.user_role1.refresh_from_db()
        self.assertTrue(self.user_role1.is_deleted)


class PermissionViewSetTestCase(UsersAPITestCaseBase):
    """PermissionViewSet API测试"""

    def setUp(self):
        super().setUp()
        # 创建测试权限
        self.permission1 = Permission.objects.create(
            name="查看用户",
            code="USER_VIEW",
            permission_type="data",  # 修正：使用正确的权限类型
            module="users",
            created_by=self.user,
        )

        self.permission2 = Permission.objects.create(
            name="编辑用户",
            code="USER_EDIT",
            permission_type="operation",  # 修正：使用正确的权限类型
            module="users",
            is_active=False,
            created_by=self.user,
        )

    def test_list_permissions(self):
        """测试获取权限列表"""
        url = reverse("users:permission-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_list_permissions_filter_by_module(self):
        """测试按模块过滤权限"""
        url = reverse("users:permission-list")
        response = self.client.get(url, {"module": "users"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证所有结果都是users模块
        for perm in response.data["results"]:
            self.assertEqual(perm["module"], "users")

    def test_list_permissions_search(self):
        """测试搜索权限"""
        url = reverse("users:permission-list")
        response = self.client.get(url, {"search": "查看"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_retrieve_permission(self):
        """测试获取单个权限详情"""
        url = reverse("users:permission-detail", args=[self.permission1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "查看用户")
        self.assertEqual(response.data["code"], "USER_VIEW")

    def test_create_permission(self):
        """测试创建权限"""
        url = reverse("users:permission-list")
        data = {
            "name": "删除用户",
            "code": "USER_DELETE",
            "permission_type": "operation",  # 修正：使用正确的权限类型
            "module": "users",
            "description": "删除用户权限",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证数据库记录
        self.assertTrue(Permission.objects.filter(code="USER_DELETE").exists())

    def test_update_permission(self):
        """测试更新权限"""
        url = reverse("users:permission-detail", args=[self.permission1.pk])
        data = {
            "name": "查看用户",
            "code": "USER_VIEW",
            "permission_type": "data",  # 修正：使用正确的权限类型
            "module": "users",
            "description": "更新后的描述",
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "更新后的描述")

    def test_delete_permission(self):
        """测试删除权限"""
        url = reverse("users:permission-detail", args=[self.permission2.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        self.permission2.refresh_from_db()
        self.assertTrue(self.permission2.is_deleted)


class UserProfileViewSetTestCase(UsersAPITestCaseBase):
    """UserProfileViewSet API测试"""

    def setUp(self):
        super().setUp()
        # 创建测试用户档案
        self.profile1 = UserProfile.objects.create(
            user=self.user,
            id_card="110101199001011234",
            address="北京市朝阳区",
            emergency_contact="紧急联系人",
            emergency_phone="13900139000",
            created_by=self.user,
        )

    def test_list_profiles(self):
        """测试获取用户档案列表"""
        url = reverse("users:userprofile-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_list_profiles_filter_by_user(self):
        """测试按用户过滤档案"""
        url = reverse("users:userprofile-list")
        response = self.client.get(url, {"user": self.user.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_profile(self):
        """测试获取单个用户档案详情"""
        url = reverse("users:userprofile-detail", args=[self.profile1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id_card"], "110101199001011234")
        self.assertIn("user_name", response.data)

    def test_create_profile(self):
        """测试创建用户档案"""
        url = reverse("users:userprofile-list")
        data = {
            "user": self.admin_user.pk,
            "id_card": "110101199002021234",
            "address": "上海市浦东新区",
            "language": "zh-cn",
            "timezone": "Asia/Shanghai",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证数据库记录
        self.assertTrue(UserProfile.objects.filter(user=self.admin_user).exists())

    def test_update_profile(self):
        """测试更新用户档案"""
        url = reverse("users:userprofile-detail", args=[self.profile1.pk])
        data = {
            "user": self.user.pk,
            "id_card": "110101199001011234",
            "address": "北京市海淀区",  # 更新地址
            "emergency_contact": "紧急联系人",
            "emergency_phone": "13900139000",
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["address"], "北京市海淀区")

    def test_delete_profile(self):
        """测试删除用户档案"""
        url = reverse("users:userprofile-detail", args=[self.profile1.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        self.profile1.refresh_from_db()
        self.assertTrue(self.profile1.is_deleted)

    def test_me_action_get(self):
        """测试获取当前用户档案"""
        url = reverse("users:userprofile-me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.pk)

    def test_me_action_put(self):
        """测试更新当前用户档案"""
        url = reverse("users:userprofile-me")
        data = {
            "theme": "dark",
            "email_notifications": False,
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["theme"], "dark")
        self.assertFalse(response.data["email_notifications"])


class LoginLogViewSetTestCase(UsersAPITestCaseBase):
    """LoginLogViewSet API测试（只读）"""

    def setUp(self):
        super().setUp()
        # 创建测试登录日志
        self.log1 = LoginLog.objects.create(
            user=self.user,
            login_type="web",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            is_successful=True,
        )

        self.log2 = LoginLog.objects.create(
            user=self.admin_user,
            login_type="api",
            ip_address="192.168.1.100",
            is_successful=False,
            failure_reason="密码错误",
        )

    def test_list_login_logs(self):
        """测试获取登录日志列表"""
        url = reverse("users:loginlog-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_list_login_logs_filter_by_user(self):
        """测试按用户过滤日志"""
        url = reverse("users:loginlog-list")
        response = self.client.get(url, {"user": self.user.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证所有日志都属于该用户
        for log in response.data["results"]:
            self.assertEqual(log["user"], self.user.pk)

    def test_list_login_logs_filter_by_success(self):
        """测试按成功状态过滤日志"""
        url = reverse("users:loginlog-list")
        response = self.client.get(url, {"is_successful": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证所有日志都是成功的
        for log in response.data["results"]:
            self.assertTrue(log["is_successful"])

    def test_retrieve_login_log(self):
        """测试获取单个登录日志详情"""
        url = reverse("users:loginlog-detail", args=[self.log1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["login_type"], "web")
        self.assertTrue(response.data["is_successful"])
        self.assertIn("user_name", response.data)
        self.assertIn("session_duration", response.data)

    def test_create_login_log_not_allowed(self):
        """测试创建登录日志（只读ViewSet，应该失败）"""
        url = reverse("users:loginlog-list")
        data = {
            "user": self.user.pk,
            "login_type": "web",
            "ip_address": "127.0.0.1",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_login_log_not_allowed(self):
        """测试更新登录日志（只读ViewSet，应该失败）"""
        url = reverse("users:loginlog-detail", args=[self.log1.pk])
        data = {"is_successful": False}
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_login_log_not_allowed(self):
        """测试删除登录日志（只读ViewSet，应该失败）"""
        url = reverse("users:loginlog-detail", args=[self.log1.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
