"""
API 访问日志中间件

记录API访问的详细信息，用于监控和审计
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django_erp.api')


class APILoggingMiddleware(MiddlewareMixin):
    """
    API 访问日志中间件
    
    记录API访问的详细信息，包括请求方法、路径、状态码、响应时间等
    """
    
    def process_request(self, request):
        """
        处理请求，记录请求开始时间
        """
        # 只对API请求进行日志记录
        if request.path.startswith('/api/'):
            # 记录请求开始时间
            request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        处理响应，记录API访问日志
        """
        # 只对API请求进行日志记录
        if request.path.startswith('/api/'):
            # 计算响应时间
            if hasattr(request, 'start_time'):
                response_time = time.time() - request.start_time
            else:
                response_time = 0
            
            # 获取请求信息
            method = request.method
            path = request.path
            status_code = response.status_code
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
            
            # 获取用户信息
            user = request.user
            if user.is_authenticated:
                username = user.username
            else:
                username = 'anonymous'
            
            # 记录API访问日志
            logger.info(
                f'API Access: {method} {path} {status_code} {response_time:.3f}s ' 
                f'User: {username} IP: {client_ip} Agent: {user_agent}'
            )
        
        return response