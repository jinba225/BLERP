"""
User models for the ERP system.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from core.models import BaseModel


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    ]

    # Override email to be required and unique
    email = models.EmailField('邮箱', unique=True)
    
    # Additional fields
    phone = models.CharField(
        '手机号', 
        max_length=20, 
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message='请输入有效的手机号')]
    )
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True)
    gender = models.CharField('性别', max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField('出生日期', null=True, blank=True)
    employee_id = models.CharField('员工编号', max_length=50, unique=True, null=True, blank=True)
    hire_date = models.DateField('入职日期', null=True, blank=True)
    department = models.ForeignKey(
        'departments.Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='部门'
    )
    position = models.CharField('职位', max_length=100, blank=True)
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='直属上级'
    )
    
    # Status fields
    is_active = models.BooleanField('是否激活', default=True)
    last_login_ip = models.GenericIPAddressField('最后登录IP', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users_user'

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.last_name}{self.first_name}".strip()

    @property
    def display_name(self):
        """Return display name for the user."""
        full_name = self.get_full_name()
        return full_name if full_name else self.username


class Role(BaseModel):
    """
    Role model for role-based access control.
    """
    name = models.CharField('角色名称', max_length=100, unique=True)
    code = models.CharField('角色代码', max_length=50, unique=True)
    description = models.TextField('角色描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    
    # Permissions
    permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        verbose_name='权限'
    )

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        db_table = 'users_role'

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    """
    User-Role relationship model.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        db_table = 'users_user_role'
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user} - {self.role}"


class Permission(BaseModel):
    """
    Custom permission model for fine-grained access control.
    """
    PERMISSION_TYPES = [
        ('menu', '菜单权限'),
        ('data', '数据权限'),
        ('operation', '操作权限'),
        ('field', '字段权限'),
    ]

    name = models.CharField('权限名称', max_length=100)
    code = models.CharField('权限代码', max_length=100, unique=True)
    permission_type = models.CharField('权限类型', max_length=20, choices=PERMISSION_TYPES)
    module = models.CharField('所属模块', max_length=50)
    description = models.TextField('权限描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'
        db_table = 'users_permission'

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserProfile(BaseModel):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    
    # Personal information
    id_card = models.CharField('身份证号', max_length=18, blank=True)
    address = models.TextField('地址', blank=True)
    emergency_contact = models.CharField('紧急联系人', max_length=100, blank=True)
    emergency_phone = models.CharField('紧急联系电话', max_length=20, blank=True)
    
    # Work information
    salary = models.DecimalField('薪资', max_digits=10, decimal_places=2, null=True, blank=True)
    bank_account = models.CharField('银行账号', max_length=50, blank=True)
    bank_name = models.CharField('开户银行', max_length=100, blank=True)
    
    # Preferences
    language = models.CharField('语言偏好', max_length=10, default='zh-hans')
    timezone = models.CharField('时区', max_length=50, default='Asia/Shanghai')
    theme = models.CharField('主题', max_length=20, default='light')
    
    # Settings
    email_notifications = models.BooleanField('邮件通知', default=True)
    sms_notifications = models.BooleanField('短信通知', default=False)

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
        db_table = 'users_user_profile'

    def __str__(self):
        return f"{self.user.username} 的资料"


class LoginLog(models.Model):
    """
    User login log model.
    """
    LOGIN_TYPES = [
        ('web', 'Web登录'),
        ('mobile', '移动端登录'),
        ('api', 'API登录'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    login_type = models.CharField('登录类型', max_length=20, choices=LOGIN_TYPES, default='web')
    ip_address = models.GenericIPAddressField('IP地址')
    user_agent = models.TextField('用户代理', blank=True)
    location = models.CharField('登录地点', max_length=200, blank=True)
    is_successful = models.BooleanField('是否成功', default=True)
    failure_reason = models.CharField('失败原因', max_length=200, blank=True)
    login_time = models.DateTimeField('登录时间', auto_now_add=True)
    logout_time = models.DateTimeField('登出时间', null=True, blank=True)

    class Meta:
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        db_table = 'users_login_log'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"

    @property
    def session_duration(self):
        """Calculate session duration."""
        if self.logout_time:
            return self.logout_time - self.login_time
        return None