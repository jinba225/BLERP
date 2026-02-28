"""
API 速率限制中间件

限制API请求的频率，防止滥用
"""
from django_ratelimit.core import is_ratelimited
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class APIRateLimitMiddleware(MiddlewareMixin):
    """
    API 速率限制中间件
    
    限制API请求的频率，防止滥用
    """
    
    def process_request(self, request):
        """
        处理请求，应用速率限制
        """
        # 只对API请求应用速率限制
        if request.path.startswith('/api/'):
            # 基于IP地址的速率限制
            # 每分钟最多60个请求
            is_limited = is_ratelimited(
                request=request,
                group='api',
                key='ip',
                rate='60/m',
                method=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
                increment=True
            )
            
            if is_limited:
                return JsonResponse(
                    {
                        'error': '请求过于频繁，请稍后再试',
                        'detail': 'API rate limit exceeded'
                    },
                    status=429
                )
        
        return None