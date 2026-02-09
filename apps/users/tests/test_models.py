"""
Users models tests.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.users.models import Role, UserRole, Permission, UserProfile, LoginLog
from apps.departments.models import Department

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""

    def test_user_creation(self):
        """Test user creation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='13800138000',
            employee_id='EMP001',
            position='软件工程师'
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.phone, '13800138000')
        self.assertEqual(user.employee_id, 'EMP001')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('testpass123'))

    def test_user_unique_email(self):
        """Test email uniqueness."""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='pass123'
        )

        # Try to create another user with same email
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='test@example.com',
                password='pass456'
            )

    def test_user_unique_employee_id(self):
        """Test employee_id uniqueness."""
        User.objects.create_user(
            username='user1',
            email='user1@example.com',
            employee_id='EMP001',
            password='pass123'
        )

        # Try to create another user with same employee_id
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                employee_id='EMP001',
                password='pass456'
            )

    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123',
            first_name='三',
            last_name='张'
        )

        self.assertEqual(user.get_full_name(), '张三')

    def test_get_full_name_empty(self):
        """Test get_full_name with empty names."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

        self.assertEqual(user.get_full_name(), '')

    def test_display_name_property(self):
        """Test display_name property."""
        # With full name
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            first_name='三',
            last_name='张'
        )
        self.assertEqual(user1.display_name, '张三')

        # Without full name (fallback to username)
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.assertEqual(user2.display_name, 'user2')

    def test_user_with_manager(self):
        """Test user with manager relationship."""
        manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass123'
        )

        employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='pass123',
            manager=manager
        )

        self.assertEqual(employee.manager, manager)

    def test_user_gender_choices(self):
        """Test gender choices."""
        genders = ['M', 'F', 'O']

        for gender in genders:
            user = User.objects.create_user(
                username=f'user_{gender}',
                email=f'{gender}@example.com',
                password='pass123',
                gender=gender
            )
            self.assertEqual(user.gender, gender)

    def test_user_str_representation(self):
        """Test user string representation."""
        # With full name
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            first_name='三',
            last_name='张'
        )
        self.assertEqual(str(user1), 'user1 (张三)')

        # Without full name
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.assertEqual(str(user2), 'user2 (user2@example.com)')


class RoleModelTest(TestCase):
    """Test Role model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

    def test_role_creation(self):
        """Test role creation."""
        role = Role.objects.create(
            name='管理员',
            code='admin',
            description='系统管理员角色',
            created_by=self.user
        )

        self.assertEqual(role.name, '管理员')
        self.assertEqual(role.code, 'admin')
        self.assertTrue(role.is_active)

    def test_role_unique_name(self):
        """Test role name uniqueness."""
        Role.objects.create(
            name='管理员',
            code='admin',
            created_by=self.user
        )

        # Try to create another role with same name
        with self.assertRaises(Exception):
            Role.objects.create(
                name='管理员',
                code='admin2',
                created_by=self.user
            )

    def test_role_unique_code(self):
        """Test role code uniqueness."""
        Role.objects.create(
            name='管理员',
            code='admin',
            created_by=self.user
        )

        # Try to create another role with same code
        with self.assertRaises(Exception):
            Role.objects.create(
                name='超级管理员',
                code='admin',
                created_by=self.user
            )

    def test_role_with_permissions(self):
        """Test role with Django permissions."""
        role = Role.objects.create(
            name='编辑员',
            code='editor',
            created_by=self.user
        )

        # Get some Django permissions
        perm1 = DjangoPermission.objects.first()
        perm2 = DjangoPermission.objects.last()

        if perm1 and perm2:
            role.permissions.add(perm1, perm2)
            self.assertEqual(role.permissions.count(), 2)

    def test_role_str_representation(self):
        """Test role string representation."""
        role = Role.objects.create(
            name='管理员',
            code='admin',
            created_by=self.user
        )

        self.assertEqual(str(role), '管理员')


class UserRoleModelTest(TestCase):
    """Test UserRole model."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )

        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

        self.role = Role.objects.create(
            name='管理员',
            code='admin',
            created_by=self.admin_user
        )

    def test_user_role_creation(self):
        """Test user role creation."""
        user_role = UserRole.objects.create(
            user=self.test_user,
            role=self.role,
            created_by=self.admin_user
        )

        self.assertEqual(user_role.user, self.test_user)
        self.assertEqual(user_role.role, self.role)
        self.assertTrue(user_role.is_active)

    def test_user_role_unique_together(self):
        """Test unique_together constraint for user and role."""
        # Create first user-role relationship
        UserRole.objects.create(
            user=self.test_user,
            role=self.role,
            created_by=self.admin_user
        )

        # Try to create duplicate user-role relationship
        with self.assertRaises(Exception):
            UserRole.objects.create(
                user=self.test_user,
                role=self.role,
                created_by=self.admin_user
            )

    def test_multiple_roles_per_user(self):
        """Test user can have multiple roles."""
        role2 = Role.objects.create(
            name='编辑员',
            code='editor',
            created_by=self.admin_user
        )

        ur1 = UserRole.objects.create(
            user=self.test_user,
            role=self.role,
            created_by=self.admin_user
        )

        ur2 = UserRole.objects.create(
            user=self.test_user,
            role=role2,
            created_by=self.admin_user
        )

        user_roles = UserRole.objects.filter(user=self.test_user)
        self.assertEqual(user_roles.count(), 2)

    def test_user_role_str_representation(self):
        """Test user role string representation."""
        user_role = UserRole.objects.create(
            user=self.test_user,
            role=self.role,
            created_by=self.admin_user
        )

        expected = f"{self.test_user} - {self.role}"
        self.assertEqual(str(user_role), expected)


class PermissionModelTest(TestCase):
    """Test Permission model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

    def test_permission_creation(self):
        """Test permission creation."""
        permission = Permission.objects.create(
            name='查看用户',
            code='user.view',
            permission_type='data',
            module='users',
            description='查看用户列表权限',
            created_by=self.user
        )

        self.assertEqual(permission.name, '查看用户')
        self.assertEqual(permission.code, 'user.view')
        self.assertEqual(permission.permission_type, 'data')
        self.assertTrue(permission.is_active)

    def test_permission_unique_code(self):
        """Test permission code uniqueness."""
        Permission.objects.create(
            name='查看用户',
            code='user.view',
            permission_type='data',
            module='users',
            created_by=self.user
        )

        # Try to create another permission with same code
        with self.assertRaises(Exception):
            Permission.objects.create(
                name='查看所有用户',
                code='user.view',
                permission_type='data',
                module='users',
                created_by=self.user
            )

    def test_permission_types(self):
        """Test all permission types."""
        types = ['menu', 'data', 'operation', 'field']

        for perm_type in types:
            permission = Permission.objects.create(
                name=f'{perm_type}权限',
                code=f'test.{perm_type}',
                permission_type=perm_type,
                module='test',
                created_by=self.user
            )
            self.assertEqual(permission.permission_type, perm_type)

    def test_permission_str_representation(self):
        """Test permission string representation."""
        permission = Permission.objects.create(
            name='查看用户',
            code='user.view',
            permission_type='data',
            module='users',
            created_by=self.user
        )

        expected = '查看用户 (user.view)'
        self.assertEqual(str(permission), expected)


class UserProfileModelTest(TestCase):
    """Test UserProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )

    def test_user_profile_creation(self):
        """Test user profile creation."""
        profile = UserProfile.objects.create(
            user=self.user,
            id_card='110101199001011234',
            address='北京市海淀区',
            emergency_contact='李四',
            emergency_phone='13900139000',
            salary=Decimal('10000.00'),
            bank_account='6222021234567890',
            bank_name='中国工商银行',
            language='zh-hans',
            timezone='Asia/Shanghai',
            theme='light',
            created_by=self.admin_user
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.id_card, '110101199001011234')
        self.assertEqual(profile.salary, Decimal('10000.00'))
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.sms_notifications)

    def test_user_profile_one_to_one(self):
        """Test one-to-one relationship with user."""
        profile = UserProfile.objects.create(
            user=self.user,
            created_by=self.admin_user
        )

        # Try to create another profile for same user
        with self.assertRaises(Exception):
            UserProfile.objects.create(
                user=self.user,
                created_by=self.admin_user
            )

    def test_user_profile_preferences(self):
        """Test user preferences in profile."""
        profile = UserProfile.objects.create(
            user=self.user,
            language='en',
            timezone='UTC',
            theme='dark',
            email_notifications=False,
            sms_notifications=True,
            created_by=self.admin_user
        )

        self.assertEqual(profile.language, 'en')
        self.assertEqual(profile.timezone, 'UTC')
        self.assertEqual(profile.theme, 'dark')
        self.assertFalse(profile.email_notifications)
        self.assertTrue(profile.sms_notifications)

    def test_user_profile_str_representation(self):
        """Test user profile string representation."""
        profile = UserProfile.objects.create(
            user=self.user,
            created_by=self.admin_user
        )

        expected = 'testuser 的资料'
        self.assertEqual(str(profile), expected)


class LoginLogModelTest(TestCase):
    """Test LoginLog model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )

    def test_login_log_creation(self):
        """Test login log creation."""
        log = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            location='北京',
            is_successful=True
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.login_type, 'web')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertTrue(log.is_successful)

    def test_login_types(self):
        """Test all login types."""
        types = ['web', 'mobile', 'api']

        for login_type in types:
            log = LoginLog.objects.create(
                user=self.user,
                login_type=login_type,
                ip_address='192.168.1.1'
            )
            self.assertEqual(log.login_type, login_type)

    def test_failed_login_log(self):
        """Test failed login log."""
        log = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.100',
            is_successful=False,
            failure_reason='密码错误'
        )

        self.assertFalse(log.is_successful)
        self.assertEqual(log.failure_reason, '密码错误')

    def test_session_duration_property(self):
        """Test session duration calculation."""
        # Login with logout
        log1 = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.1'
        )
        log1.logout_time = log1.login_time + timedelta(hours=2, minutes=30)
        log1.save()

        expected_duration = timedelta(hours=2, minutes=30)
        self.assertEqual(log1.session_duration, expected_duration)

        # Login without logout
        log2 = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.1'
        )
        self.assertIsNone(log2.session_duration)

    def test_login_log_ordering(self):
        """Test login logs are ordered by login_time desc."""
        log1 = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.1'
        )

        # Wait a moment and create another log
        log2 = LoginLog.objects.create(
            user=self.user,
            login_type='mobile',
            ip_address='192.168.1.2'
        )

        logs = list(LoginLog.objects.filter(user=self.user))
        self.assertEqual(logs[0], log2)  # Latest first
        self.assertEqual(logs[1], log1)

    def test_login_log_str_representation(self):
        """Test login log string representation."""
        log = LoginLog.objects.create(
            user=self.user,
            login_type='web',
            ip_address='192.168.1.1'
        )

        expected = f"testuser - {log.login_time}"
        self.assertEqual(str(log), expected)
