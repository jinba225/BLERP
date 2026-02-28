# 安全优化方案

## 1. 安全漏洞扫描

### 1.1 扫描工具
- **静态代码分析**: 使用 Bandit、Pylint 等工具进行静态代码分析
- **依赖项扫描**: 使用 Safety、OWASP Dependency-Check 等工具扫描依赖项漏洞
- **动态扫描**: 使用 OWASP ZAP、Burp Suite 等工具进行动态安全扫描
- **容器安全扫描**: 使用 Trivy、Clair 等工具扫描容器镜像漏洞

### 1.2 扫描配置

```python
# 安全扫描配置
SECURITY_SCANNING = {
    'static_analysis': {
        'enabled': True,
        'tools': ['bandit', 'pylint'],
        'exclude_paths': ['venv', 'node_modules'],
        'severity_threshold': 'medium',
    },
    'dependency_scanning': {
        'enabled': True,
        'tools': ['safety', 'dependency-check'],
        'severity_threshold': 'medium',
    },
    'dynamic_scanning': {
        'enabled': True,
        'tools': ['owasp-zap'],
        'target_urls': ['http://localhost:8000'],
        'severity_threshold': 'medium',
    },
    'container_scanning': {
        'enabled': True,
        'tools': ['trivy'],
        'images': ['django_erp:latest'],
        'severity_threshold': 'medium',
    },
}
```

### 1.3 扫描流程
1. **代码提交时扫描**: 在代码提交时执行静态代码分析和依赖项扫描
2. **构建时扫描**: 在构建过程中执行容器安全扫描
3. **部署前扫描**: 在部署前执行动态安全扫描
4. **定期扫描**: 定期执行全面的安全扫描

### 1.4 漏洞管理
- **漏洞跟踪**: 使用漏洞跟踪系统记录和管理发现的漏洞
- **修复优先级**: 根据漏洞的严重程度和影响范围确定修复优先级
- **修复验证**: 修复漏洞后进行验证扫描
- **安全报告**: 定期生成安全扫描报告

## 2. 权限管理加强

### 2.1 基于角色的访问控制 (RBAC)
- **角色定义**: 定义系统角色，如管理员、经理、普通用户等
- **权限分配**: 为每个角色分配适当的权限
- **权限继承**: 支持权限的继承和覆盖
- **最小权限原则**: 确保用户只拥有完成任务所需的最小权限

### 2.2 权限管理实现

```python
# 权限管理实现
class RBACManager:
    """基于角色的访问控制管理器"""
    
    def __init__(self):
        self.roles = {
            'admin': {
                'permissions': ['view_all', 'edit_all', 'delete_all', 'administer'],
                'description': '系统管理员',
            },
            'manager': {
                'permissions': ['view_all', 'edit_own', 'delete_own'],
                'description': '部门经理',
            },
            'user': {
                'permissions': ['view_own', 'edit_own'],
                'description': '普通用户',
            },
        }
        self.user_roles = {}
    
    def assign_role(self, user_id, role_name):
        """为用户分配角色
        
        Args:
            user_id: 用户ID
            role_name: 角色名称
        """
        if role_name in self.roles:
            self.user_roles[user_id] = role_name
    
    def has_permission(self, user_id, permission):
        """检查用户是否具有权限
        
        Args:
            user_id: 用户ID
            permission: 权限名称
        
        Returns:
            bool: 是否具有权限
        """
        role_name = self.user_roles.get(user_id)
        if not role_name:
            return False
        
        role = self.roles.get(role_name)
        if not role:
            return False
        
        return permission in role['permissions']
    
    def get_user_permissions(self, user_id):
        """获取用户的所有权限
        
        Args:
            user_id: 用户ID
        
        Returns:
            list: 权限列表
        """
        role_name = self.user_roles.get(user_id)
        if not role_name:
            return []
        
        role = self.roles.get(role_name)
        if not role:
            return []
        
        return role['permissions']
```

### 2.3 权限审计
- **权限变更审计**: 记录权限变更的历史
- **权限使用审计**: 记录权限的使用情况
- **权限分析**: 分析权限分配的合理性
- **权限回收**: 定期回收未使用的权限

### 2.4 权限验证中间件

```python
# 权限验证中间件
class PermissionMiddleware:
    """权限验证中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 跳过静态文件和媒体文件
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # 跳过登录和注册页面
        if request.path in ['/login/', '/register/']:
            return self.get_response(request)
        
        # 检查用户是否登录
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('/login/')
        
        # 检查用户权限
        rbac_manager = RBACManager()
        user_id = request.user.id
        
        # 检查API权限
        if request.path.startswith('/api/'):
            api_permission = self._get_api_permission(request.path, request.method)
            if api_permission and not rbac_manager.has_permission(user_id, api_permission):
                from rest_framework.response import Response
                from rest_framework import status
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查视图权限
        view_permission = self._get_view_permission(request.path)
        if view_permission and not rbac_manager.has_permission(user_id, view_permission):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Permission denied')
        
        return self.get_response(request)
    
    def _get_api_permission(self, path, method):
        """获取API权限
        
        Args:
            path: API路径
            method: HTTP方法
        
        Returns:
            str: 权限名称
        """
        # 这里根据实际API路径和方法映射权限
        # 示例实现
        if path.startswith('/api/admin/'):
            return 'administer'
        elif path.startswith('/api/users/'):
            if method in ['POST', 'PUT', 'DELETE']:
                return 'edit_all'
            else:
                return 'view_all'
        else:
            return None
    
    def _get_view_permission(self, path):
        """获取视图权限
        
        Args:
            path: 视图路径
        
        Returns:
            str: 权限名称
        """
        # 这里根据实际视图路径映射权限
        # 示例实现
        if path.startswith('/admin/'):
            return 'administer'
        elif path.startswith('/manager/'):
            return 'view_all'
        else:
            return None
```

## 3. 安全配置优化

### 3.1 HTTPS配置
- **SSL证书**: 配置有效的SSL证书
- **TLS版本**: 启用TLS 1.2和TLS 1.3，禁用旧版本
- **密码套件**: 配置安全的密码套件
- **HSTS**: 启用HTTP Strict Transport Security

### 3.2 安全头部
- **Content Security Policy (CSP)**: 配置内容安全策略
- **X-Content-Type-Options**: 防止MIME类型嗅探
- **X-Frame-Options**: 防止点击劫持
- **X-XSS-Protection**: 启用XSS保护
- **Referrer-Policy**: 配置引用策略

### 3.3 安全配置实现

```python
# 安全配置
SECURITY_CONFIG = {
    # HTTPS配置
    'https': {
        'enabled': True,
        'ssl_certificate': '/path/to/certificate.pem',
        'ssl_key': '/path/to/private.key',
        'tls_versions': ['TLSv1.2', 'TLSv1.3'],
        'cipher_suites': [
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'DHE-RSA-AES256-GCM-SHA384',
            'DHE-RSA-AES128-GCM-SHA256',
        ],
    },
    # 安全头部
    'headers': {
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self';",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    },
    # 会话安全
    'session': {
        'cookie_httponly': True,
        'cookie_secure': True,
        'cookie_samesite': 'Strict',
        'session_timeout': 86400,  # 24小时
        'session_expire_at_browser_close': False,
    },
    # CSRF保护
    'csrf': {
        'enabled': True,
        'cookie_httponly': True,
        'cookie_secure': True,
        'cookie_samesite': 'Strict',
    },
    # 密码策略
    'password': {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_symbols': True,
        'max_age': 90,  # 90天
        'history_count': 5,  # 记住最近5个密码
    },
    # 登录安全
    'login': {
        'max_attempts': 5,  # 最大尝试次数
        'lockout_duration': 300,  # 锁定时间（秒）
        'two_factor_auth': True,  # 双因素认证
        'session_limit': 5,  # 最大会话数
    },
}
```

### 3.4 安全中间件

```python
# 安全中间件
class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # 添加安全头部
        headers = SECURITY_CONFIG['headers']
        for key, value in headers.items():
            response[key] = value
        
        # 设置会话安全
        if hasattr(request, 'session'):
            request.session.set_expiry(SECURITY_CONFIG['session']['session_timeout'])
        
        return response
```

## 4. 安全审计

### 4.1 审计日志
- **登录审计**: 记录用户登录和登出事件
- **操作审计**: 记录用户的关键操作
- **权限审计**: 记录权限变更事件
- **安全事件**: 记录安全相关事件

### 4.2 审计日志实现

```python
# 审计日志服务
class AuditLogService:
    """审计日志服务"""
    
    def __init__(self):
        self.log_types = {
            'login': '登录事件',
            'logout': '登出事件',
            'create': '创建操作',
            'update': '更新操作',
            'delete': '删除操作',
            'permission': '权限变更',
            'security': '安全事件',
        }
    
    def log_event(self, user, log_type, object_type=None, object_id=None, details=None):
        """记录审计事件
        
        Args:
            user: 用户对象
            log_type: 日志类型
            object_type: 对象类型
            object_id: 对象ID
            details: 详细信息
        """
        from core.models import AuditLog
        
        # 创建审计日志
        audit_log = AuditLog(
            user=user,
            action=log_type,
            model_name=object_type,
            object_id=object_id,
            object_repr=str(object_id),
            changes=details,
            ip_address=self._get_client_ip(user),
            user_agent=self._get_user_agent(user),
        )
        audit_log.save()
    
    def _get_client_ip(self, request):
        """获取客户端IP
        
        Args:
            request: 请求对象
        
        Returns:
            str: 客户端IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_user_agent(self, request):
        """获取用户代理
        
        Args:
            request: 请求对象
        
        Returns:
            str: 用户代理
        """
        return request.META.get('HTTP_USER_AGENT', '')
    
    def get_audit_logs(self, user=None, log_type=None, start_date=None, end_date=None):
        """获取审计日志
        
        Args:
            user: 用户对象
            log_type: 日志类型
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            queryset: 审计日志查询集
        """
        from core.models import AuditLog
        
        queryset = AuditLog.objects.all()
        
        if user:
            queryset = queryset.filter(user=user)
        
        if log_type:
            queryset = queryset.filter(action=log_type)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')
```

### 4.3 审计报告
- **定期审计报告**: 生成定期审计报告
- **异常行为检测**: 检测异常的用户行为
- **安全事件分析**: 分析安全事件的模式
- **合规性检查**: 检查系统的合规性

### 4.4 审计日志分析

```python
# 审计日志分析服务
class AuditLogAnalyzer:
    """审计日志分析服务"""
    
    def __init__(self, audit_log_service):
        self.audit_log_service = audit_log_service
    
    def detect_anomalies(self, time_range='7d'):
        """检测异常行为
        
        Args:
            time_range: 时间范围
        
        Returns:
            list: 异常行为列表
        """
        # 计算时间范围
        import datetime
        end_date = datetime.datetime.now()
        if time_range == '7d':
            start_date = end_date - datetime.timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - datetime.timedelta(days=30)
        else:
            start_date = end_date - datetime.timedelta(days=7)
        
        # 获取审计日志
        logs = self.audit_log_service.get_audit_logs(start_date=start_date, end_date=end_date)
        
        # 分析异常行为
        anomalies = []
        
        # 检测异常登录
        login_logs = logs.filter(action='login')
        login_counts = login_logs.values('user', 'ip_address').annotate(count=models.Count('id'))
        for login in login_counts:
            if login['count'] > 10:  # 登录次数超过10次
                anomalies.append({
                    'type': 'login_anomaly',
                    'user': login['user'],
                    'ip_address': login['ip_address'],
                    'count': login['count'],
                    'message': f'用户 {login["user"]} 在 {time_range} 内登录次数异常: {login["count"]} 次',
                })
        
        # 检测异常操作
        action_logs = logs.filter(action__in=['create', 'update', 'delete'])
        action_counts = action_logs.values('user', 'action').annotate(count=models.Count('id'))
        for action in action_counts:
            if action['count'] > 50:  # 操作次数超过50次
                anomalies.append({
                    'type': 'action_anomaly',
                    'user': action['user'],
                    'action': action['action'],
                    'count': action['count'],
                    'message': f'用户 {action["user"]} 在 {time_range} 内 {action["action"]} 操作次数异常: {action["count"]} 次',
                })
        
        return anomalies
    
    def generate_report(self, time_range='30d'):
        """生成审计报告
        
        Args:
            time_range: 时间范围
        
        Returns:
            dict: 审计报告
        """
        # 计算时间范围
        import datetime
        end_date = datetime.datetime.now()
        if time_range == '7d':
            start_date = end_date - datetime.timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - datetime.timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - datetime.timedelta(days=90)
        else:
            start_date = end_date - datetime.timedelta(days=30)
        
        # 获取审计日志
        logs = self.audit_log_service.get_audit_logs(start_date=start_date, end_date=end_date)
        
        # 统计数据
        total_logs = logs.count()
        login_logs = logs.filter(action='login').count()
        logout_logs = logs.filter(action='logout').count()
        create_logs = logs.filter(action='create').count()
        update_logs = logs.filter(action='update').count()
        delete_logs = logs.filter(action='delete').count()
        permission_logs = logs.filter(action='permission').count()
        security_logs = logs.filter(action='security').count()
        
        # 检测异常
        anomalies = self.detect_anomalies(time_range)
        
        # 生成报告
        report = {
            'time_range': time_range,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_logs': total_logs,
            'log_summary': {
                'login': login_logs,
                'logout': logout_logs,
                'create': create_logs,
                'update': update_logs,
                'delete': delete_logs,
                'permission': permission_logs,
                'security': security_logs,
            },
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(anomalies),
        }
        
        return report
    
    def _generate_recommendations(self, anomalies):
        """生成安全建议
        
        Args:
            anomalies: 异常行为列表
        
        Returns:
            list: 安全建议列表
        """
        recommendations = []
        
        if anomalies:
            recommendations.append('检查异常登录和操作行为，确认是否为合法用户操作')
            recommendations.append('考虑为高风险用户启用双因素认证')
            recommendations.append('审查用户权限，确保最小权限原则')
        
        recommendations.append('定期备份审计日志，确保数据安全')
        recommendations.append('更新安全配置，应对最新的安全威胁')
        recommendations.append('对员工进行安全意识培训，提高安全意识')
        
        return recommendations
```

## 5. 安全培训和意识

### 5.1 安全培训
- **开发人员培训**: 培训开发人员安全编码实践
- **运维人员培训**: 培训运维人员安全配置和管理
- **用户培训**: 培训用户安全使用系统
- **管理层培训**: 培训管理层安全意识和责任

### 5.2 安全意识提升
- **安全公告**: 定期发布安全公告
- **安全提醒**: 在系统中添加安全提醒
- **安全测试**: 定期进行安全测试和演练
- **安全奖励**: 建立安全奖励机制

## 6. 实施计划

### 6.1 短期优化（1-2周）
1. 执行安全漏洞扫描，识别系统中的安全漏洞
2. 加强权限管理，实现基于角色的访问控制
3. 优化安全配置，加强HTTPS和安全头部配置
4. 实现基本的安全审计功能

### 6.2 中期优化（2-4周）
1. 修复识别的安全漏洞
2. 完善权限管理，实现权限继承和最小权限原则
3. 部署安全中间件，加强安全防护
4. 实现全面的安全审计和监控

### 6.3 长期优化（1-3个月）
1. 建立安全培训和意识提升计划
2. 实现自动化安全扫描和监控
3. 建立安全事件响应机制
4. 定期进行安全评估和改进

## 7. 预期效果

- **安全漏洞减少**: 预计减少 80-90% 的安全漏洞
- **权限管理改进**: 预计提高 95% 的权限管理准确性
- **安全事件减少**: 预计减少 70-80% 的安全事件
- **合规性提高**: 预计达到 95% 以上的合规性
- **安全意识提升**: 预计提高 80-90% 的安全意识

## 8. 风险评估

- **实施成本**: 安全优化需要投入一定的人力和资源
- **系统影响**: 安全措施可能会影响系统的性能和用户体验
- **误报率**: 安全扫描和告警可能会产生误报
- **维护成本**: 安全系统需要持续的维护和更新

## 9. 监控和验证

- **安全扫描验证**: 定期验证安全扫描的有效性
- **权限管理验证**: 定期验证权限管理的正确性
- **安全配置验证**: 定期验证安全配置的有效性
- **审计日志验证**: 定期验证审计日志的完整性和准确性

## 10. 结论

通过实施上述安全优化方案，可以显著提高系统的安全性和可靠性，减少安全漏洞和安全事件的发生，提高系统的合规性和用户的安全意识。安全优化是一个持续的过程，需要根据最新的安全威胁和最佳实践不断调整和改进，以确保系统的安全状态始终保持在最佳水平。