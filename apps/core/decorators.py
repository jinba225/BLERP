"""
API 装饰器

提供API认证和权限验证装饰器
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt


def api_auth_required(view_func):
    """
    API 认证装饰器
    
    要求API请求提供有效的认证信息
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            # 尝试从请求头获取认证信息
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return JsonResponse(
                    {
                        'error': '未提供认证信息',
                        'detail': 'Authentication required'
                    },
                    status=401
                )
            
            # 处理Bearer令牌
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # 这里可以添加JWT令牌验证逻辑
                # 暂时返回未实现错误
                return JsonResponse(
                    {
                        'error': '认证方式未实现',
                        'detail': 'Authentication method not implemented'
                    },
                    status=501
                )
            
            # 处理Basic认证
            elif auth_header.startswith('Basic '):
                import base64
                try:
                    auth_str = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
                    username, password = auth_str.split(':', 1)
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                    else:
                        return JsonResponse(
                            {
                                'error': '认证失败',
                                'detail': 'Invalid credentials'
                            },
                            status=401
                        )
                except Exception as e:
                    return JsonResponse(
                        {
                            'error': '认证格式错误',
                            'detail': 'Invalid authentication format'
                        },
                        status=400
                    )
            
            else:
                return JsonResponse(
                    {
                        'error': '不支持的认证方式',
                        'detail': 'Unsupported authentication method'
                    },
                    status=401
                )
        
        # 检查用户是否激活
        if not request.user.is_active:
            return JsonResponse(
                {
                    'error': '账户未激活',
                    'detail': 'Account is inactive'
                },
                status=403
            )
        
        # 检查密码是否过期
        if hasattr(request.user, 'is_password_expired') and request.user.is_password_expired():
            return JsonResponse(
                {
                    'error': '密码已过期',
                    'detail': 'Password has expired'
                },
                status=403
            )
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def api_rate_limit(rate='60/m'):
    """
    API 速率限制装饰器
    
    限制API请求的频率
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django_ratelimit.core import is_ratelimited
            
            is_limited = is_ratelimited(
                request=request,
                group='api',
                key='ip',
                rate=rate,
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
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator