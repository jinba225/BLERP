"""
安全审计中间件

记录安全相关的事件和操作，包括：
- 用户登录/注销
- 权限变更
- 敏感操作
- 安全异常
"""
import logging
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from apps.core.models import AuditLog

logger = logging.getLogger("django_erp.security")


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    安全审计中间件

    功能：
    1. 记录用户登录/注销事件
    2. 记录权限变更操作
    3. 记录敏感操作
    4. 检测和记录安全异常
    5. 记录API访问频率异常
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.request_counts = {}
        self.api_rate_limit = 100  # 每分钟API请求限制

    def process_request(self, request):
        """处理请求开始"""
        # 记录请求开始时间
        request.start_time = time.time()
        
        # 检查API访问频率
        self._check_api_rate_limit(request)
        
        # 记录敏感操作
        self._log_sensitive_operations(request)
        
        return None

    def process_response(self, request, response):
        """处理请求结束"""
        # 计算响应时间
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # 记录慢请求
            if duration > 5.0:
                logger.warning(
                    f"慢请求检测: {request.method} {request.path} "
                    f"耗时 {duration:.2f}s | 状态码: {response.status_code}"
                )
        
        # 记录安全相关的响应
        self._log_security_responses(request, response)
        
        return response

    def _check_api_rate_limit(self, request):
        """检查API访问频率"""
        # 只检查API请求
        if not request.path.startswith('/api/'):
            return
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        current_time = int(time.time() / 60)  # 按分钟计算
        
        # 初始化计数器
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        if current_time not in self.request_counts[client_ip]:
            self.request_counts[client_ip][current_time] = 0
        
        # 增加计数
        self.request_counts[client_ip][current_time] += 1
        
        # 检查是否超过限制
        if self.request_counts[client_ip][current_time] > self.api_rate_limit:
            logger.warning(
                f"API访问频率超限: IP={client_ip}, 计数={self.request_counts[client_ip][current_time]}"
            )
            
            # 记录审计日志
            if request.user.is_authenticated:
                AuditLog.objects.create(
                    user=request.user,
                    action="api_rate_limit_exceeded",
                    model_name="security",
                    object_repr=f"API rate limit exceeded for IP: {client_ip}",
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
        
        # 清理过期的计数
        self._cleanup_old_counts()

    def _cleanup_old_counts(self):
        """清理过期的计数"""
        current_time = int(time.time() / 60)
        for client_ip in list(self.request_counts.keys()):
            for timestamp in list(self.request_counts[client_ip].keys()):
                if timestamp < current_time - 5:  # 保留5分钟的记录
                    del self.request_counts[client_ip][timestamp]
            
            # 如果该IP没有记录了，删除整个条目
            if not self.request_counts[client_ip]:
                del self.request_counts[client_ip]

    def _log_sensitive_operations(self, request):
        """记录敏感操作"""
        sensitive_paths = [
            '/admin/',
            '/api/auth/',
            '/api/users/',
            '/api/settings/',
            '/api/security/',
        ]
        
        # 检查是否是敏感路径
        for path in sensitive_paths:
            if request.path.startswith(path):
                # 记录敏感操作
                if request.user.is_authenticated:
                    AuditLog.objects.create(
                        user=request.user,
                        action="sensitive_operation",
                        model_name="security",
                        object_repr=f"Sensitive operation: {request.method} {request.path}",
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    )
                break

    def _log_security_responses(self, request, response):
        """记录安全相关的响应"""
        # 记录401和403响应
        if response.status_code in [401, 403]:
            logger.warning(
                f"权限错误: {request.method} {request.path} "
                f"状态码: {response.status_code} | IP: {self._get_client_ip(request)}"
            )
            
            # 记录审计日志
            if request.user.is_authenticated:
                AuditLog.objects.create(
                    user=request.user,
                    action="permission_denied",
                    model_name="security",
                    object_repr=f"Permission denied: {request.method} {request.path}",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
        
        # 记录500错误
        elif response.status_code >= 500:
            logger.error(
                f"服务器错误: {request.method} {request.path} "
                f"状态码: {response.status_code} | IP: {self._get_client_ip(request)}"
            )

    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    内容安全策略（CSP）中间件
    """

    def process_response(self, request, response):
        """添加CSP头部"""
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            csp_headers = [
                f"default-src {settings.CSP_DEFAULT_SRC}",
                f"script-src {settings.CSP_SCRIPT_SRC}",
                f"style-src {settings.CSP_STYLE_SRC}",
                f"img-src {settings.CSP_IMG_SRC}",
                f"font-src {settings.CSP_FONT_SRC}",
                f"connect-src {settings.CSP_CONNECT_SRC}",
                f"object-src {settings.CSP_OBJECT_SRC}",
                f"base-uri {settings.CSP_BASE_URI}",
                f"frame-ancestors {settings.CSP_FRAME_ANCESTORS}",
                f"form-action {settings.CSP_FORM_ACTION}",
            ]
            
            csp_header = '; '.join(csp_headers)
            response['Content-Security-Policy'] = csp_header
        
        return response