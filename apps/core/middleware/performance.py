"""
性能监控中间件

监控页面响应时间和数据库查询性能，识别慢请求。
"""
import time
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger("django_erp.performance")


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    性能监控中间件

    功能：
    1. 记录每个请求的响应时间
    2. 记录慢请求（超过1秒）
    3. 统计数据库查询次数
    4. 在开发环境下添加响应头显示性能数据
    """

    def process_request(self, request):
        """请求开始时记录开始时间"""
        request.start_time = time.time()

    def process_response(self, request, response):
        """请求结束时计算性能指标"""
        # 只有在设置了start_time的请求上才执行
        if not hasattr(request, "start_time"):
            return response

        # 计算响应时间
        duration = time.time() - request.start_time

        # 获取数据库查询次数
        query_count = len(connection.queries) if settings.DEBUG else 0

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

        return response
