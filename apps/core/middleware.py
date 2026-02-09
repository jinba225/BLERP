"""
Core middleware for the ERP system.
"""
import logging
import traceback

import pytz
from django.http import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to set timezone based on user preferences.
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                # Try to get timezone from user profile
                user_timezone = request.user.userprofile.timezone
                timezone.activate(pytz.timezone(user_timezone))
            except:
                # Fall back to default timezone
                timezone.deactivate()
        else:
            timezone.deactivate()


class AIAssistantErrorHandlingMiddleware(MiddlewareMixin):
    """
    AI 助手错误处理中间件

    专门处理AI助手相关请求的错误，提供友好的错误响应
    """

    def process_exception(self, request, exception):
        """
        处理AI助手相关的异常

        Args:
            request: HTTP请求对象
            exception: 异常对象

        Returns:
            JsonResponse或None
        """
        # 只处理 AI 助手相关的请求
        if not (request.path.startswith("/ai_assistant/") or request.path.startswith("/webhook/")):
            return None

        # 记录详细错误信息
        logger.error(
            f"AI Assistant Error: {str(exception)}\n"
            f"Path: {request.path}\n"
            f"Method: {request.method}\n"
            f"User: {request.user if request.user.is_authenticated else 'Anonymous'}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # 返回友好的错误响应
        return JsonResponse(
            {
                "success": False,
                "error": str(exception),
                "error_type": type(exception).__name__,
            },
            status=500,
        )
