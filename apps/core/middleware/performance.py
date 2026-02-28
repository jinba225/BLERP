"""
性能监控中间件

监控页面响应时间和数据库查询性能，识别慢请求。
"""

import logging
import time

from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("django_erp.performance")


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    性能监控中间件

    功能：
    1. 记录每个请求的响应时间
    2. 记录慢请求（超过1秒）
    3. 统计数据库查询次数
    4. 在开发环境下添加响应头显示性能数据
    5. 保存API性能数据到数据库
    """

    def process_request(self, request):
        """请求开始时记录开始时间"""
        request.start_time = time.time()
        # 记录请求大小
        if hasattr(request, "body"):
            request.request_size = len(request.body)
        else:
            request.request_size = 0

    def process_response(self, request, response):
        """请求结束时计算性能指标"""
        # 只有在设置了start_time的请求上才执行
        if not hasattr(request, "start_time"):
            return response

        # 计算响应时间
        duration = time.time() - request.start_time

        # 获取数据库查询次数
        query_count = len(connection.queries) if settings.DEBUG else 0

        # 计算数据库查询总时间
        db_query_time = 0
        if settings.DEBUG and connection.queries:
            db_query_time = (
                sum(float(query.get("time", 0)) for query in connection.queries) * 1000
            )  # 转换为毫秒

        # 记录慢请求（超过1秒）
        if duration > 1.0:
            logger.warning(
                f"慢请求检测: {request.method} {request.path} "
                f"耗时 {duration:.2f}s | 查询次数: {query_count}"
            )

        # 在开发环境下添加性能响应头
        if settings.DEBUG:
            response["X-Page-Generation-Time"] = f"{duration:.3f}s"
            response["X-DB-Query-Count"] = str(query_count)

        # 记录所有请求的性能数据（info级别）
        logger.info(
            f"{request.method} {request.path} - " f"{duration:.3f}s | {query_count} queries"
        )

        # 保存API性能数据到数据库
        try:
            # 延迟导入，避免循环导入
            from apps.bi.models import ApiPerformance

            # 计算响应大小
            response_size = 0
            if hasattr(response, "content"):
                response_size = len(response.content)

            # 提取错误信息
            error_message = ""
            if response.status_code >= 400:
                error_message = str(response.content[:500])  # 只保存前500个字符

            # 创建API性能记录
            ApiPerformance.objects.create(
                endpoint=request.path,
                method=request.method,
                response_time=duration * 1000,  # 转换为毫秒
                status_code=response.status_code,
                error_message=error_message,
                request_size=getattr(request, "request_size", 0),
                response_size=response_size,
            )

        except Exception as e:
            logger.error(f"保存API性能数据失败: {e}")

        return response
