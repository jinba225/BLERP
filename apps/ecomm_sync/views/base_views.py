"""基础视图类"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View


@method_decorator(login_required)
class LoginRequiredMixin:
    """登录RequiredMixin"""

    pass


class JsonResponseMixin:
    """JSON响应混入类"""

    def json_response(
        self, success: bool = True, data: any = None, message: str = "", error: str = None
    ):
        """返回JSON响应"""
        response_data = {
            "success": success,
            "data": data,
            "message": message,
            "error": error,
        }
        return JsonResponse(response_data)


class BaseListView(JsonResponseMixin, LoginRequiredMixin, View):
    """基础列表视图"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = "电商同步"
        return context


class BaseDetailView(JsonResponseMixin, LoginRequiredMixin, View):
    """基础详情视图"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = "电商同步"
        return context


class BaseFormView(JsonResponseMixin, LoginRequiredMixin, View):
    """基础表单视图"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = "电商同步"
        return context
