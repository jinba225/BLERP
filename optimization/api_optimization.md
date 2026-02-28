# API性能优化方案

## 1. API请求批处理

### 1.1 批量请求处理
- **问题**: 前端频繁发送多个API请求，导致网络开销和服务器负载增加
- **解决方案**: 实现批量请求处理端点，允许前端在一个请求中发送多个操作

```python
# 批量请求处理视图
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class BatchRequestView(APIView):
    """批量请求处理视图"""

    def post(self, request, *args, **kwargs):
        """处理批量请求"""
        operations = request.data.get('operations', [])
        results = []

        for operation in operations:
            method = operation.get('method', 'GET').upper()
            url = operation.get('url')
            data = operation.get('data', {})
            headers = operation.get('headers', {})

            # 处理请求
            try:
                # 使用内部请求处理
                from django.test import Client
                client = Client()

                if method == 'GET':
                    response = client.get(url, data, headers=headers)
                elif method == 'POST':
                    response = client.post(url, data, content_type='application/json', headers=headers)
                elif method == 'PUT':
                    response = client.put(url, data, content_type='application/json', headers=headers)
                elif method == 'DELETE':
                    response = client.delete(url, headers=headers)
                else:
                    response = Response({'error': 'Invalid method'}, status=status.HTTP_400_BAD_REQUEST)

                results.append({
                    'id': operation.get('id'),
                    'status': response.status_code,
                    'data': response.json() if response.content else None
                })
            except Exception as e:
                results.append({
                    'id': operation.get('id'),
                    'status': 500,
                    'data': {'error': str(e)}
                })

        return Response({'results': results})
```

### 1.2 批量查询优化
- **问题**: 前端需要获取多个相关资源时，需要发送多个请求
- **解决方案**: 实现批量查询端点，支持一次性获取多个资源

```python
# 批量查询视图
class BatchRetrieveView(APIView):
    """批量查询视图"""

    def get(self, request, *args, **kwargs):
        """批量查询资源"""
        model_name = request.query_params.get('model')
        ids = request.query_params.getlist('ids')

        if not model_name or not ids:
            return Response({'error': 'Model and ids are required'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据模型名称获取对应的模型和序列化器
        model_map = {
            'company': (Company, CompanySerializer),
            'system_config': (SystemConfig, SystemConfigSerializer),
            'attachment': (Attachment, AttachmentSerializer),
            'audit_log': (AuditLog, AuditLogSerializer),
        }

        if model_name not in model_map:
            return Response({'error': 'Invalid model name'}, status=status.HTTP_400_BAD_REQUEST)

        model, serializer_class = model_map[model_name]

        # 批量查询
        instances = model.objects.filter(id__in=ids)
        serializer = serializer_class(instances, many=True)

        return Response(serializer.data)
```

## 2. 序列化过程优化

### 2.1 字段选择优化
- **问题**: 序列化器默认返回所有字段，即使前端只需要部分字段
- **解决方案**: 实现更灵活的字段选择机制，允许前端指定需要的字段

```python
# 优化后的序列化器基类
class OptimizedSerializer(serializers.ModelSerializer):
    """优化的序列化器基类"""

    def __init__(self, *args, **kwargs):
        # 支持字段选择
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        super().__init__(*args, **kwargs)

        # 处理字段选择
        if fields:
            allowed = set(fields.split(','))
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        # 处理字段排除
        if exclude:
            excluded = set(exclude.split(','))
            for field_name in excluded:
                if field_name in self.fields:
                    self.fields.pop(field_name)
```

### 2.2 序列化器缓存
- **问题**: 序列化过程可能会重复计算相同的数据
- **解决方案**: 实现序列化器结果缓存，避免重复序列化

```python
# 序列化器缓存装饰器
from functools import lru_cache

class CachedSerializerMixin:
    """序列化器缓存混入"""

    @lru_cache(maxsize=1024)
    def to_representation(self, instance):
        """缓存序列化结果"""
        return super().to_representation(instance)
```

### 2.3 异步序列化
- **问题**: 复杂序列化操作可能会阻塞请求处理
- **解决方案**: 实现异步序列化，提高并发处理能力

```python
# 异步序列化器
class AsyncSerializer(serializers.ModelSerializer):
    """异步序列化器"""

    async def to_representation_async(self, instance):
        """异步序列化"""
        # 异步处理耗时操作
        return await asyncio.to_thread(self.to_representation, instance)
```

## 3. API响应缓存优化

### 3.1 智能缓存策略
- **问题**: 静态缓存策略可能导致缓存过期或缓存未命中
- **解决方案**: 实现基于业务场景的智能缓存策略

```python
# 智能缓存装饰器
from core.services.cache_manager import get_cache_manager

async def smart_cached_api_response(timeout=300, cache_key=None, cache_type="api_response"):
    """智能API响应缓存装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        async def wrapper(self, request, *args, **kwargs):
            # 生成缓存键
            if cache_key:
                key = cache_key
            else:
                # 基于请求路径和参数生成缓存键
                path = request.path
                params = sorted(request.query_params.items())
                key = f"api:{path}:{hash(str(params))}"

            # 检查缓存
            cache_manager = get_cache_manager()
            cached_data = await cache_manager.get(key, cache_type)

            if cached_data:
                return Response(cached_data)

            # 执行视图函数
            response = await view_func(self, request, *args, **kwargs)

            # 缓存响应
            if response.status_code == 200:
                await cache_manager.set(key, response.data, cache_type)

            return response
        return wrapper
    return decorator
```

### 3.2 条件缓存
- **问题**: 相同请求可能返回不同结果，导致缓存不一致
- **解决方案**: 实现基于ETag和Last-Modified的条件缓存

```python
# 条件缓存装饰器
from django.utils.http import http_date
from hashlib import md5

class ConditionalCacheMixin:
    """条件缓存混入"""

    def dispatch(self, request, *args, **kwargs):
        # 生成ETag
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 200:
            # 生成内容哈希作为ETag
            content_hash = md5(str(response.data).encode()).hexdigest()
            etag = f'"{content_hash}"'

            # 设置ETag和Last-Modified
            response['ETag'] = etag
            response['Last-Modified'] = http_date()

            # 检查If-None-Match
            if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
            if if_none_match == etag:
                return Response(status=304)

        return response
```

### 3.3 缓存分层
- **问题**: 单一缓存策略无法满足不同类型API的需求
- **解决方案**: 实现多层缓存策略，根据API类型选择合适的缓存策略

```python
# 缓存分层策略
CACHE_STRATEGIES = {
    'api_response': {
        'strategy': 'write_through',
        'ttl': 300,  # 5分钟
        'enable_local_cache': True
    },
    'api_response_stable': {
        'strategy': 'write_through',
        'ttl': 3600,  # 1小时
        'enable_local_cache': True
    },
    'api_response_dynamic': {
        'strategy': 'cache_aside',
        'ttl': 60,  # 1分钟
        'enable_local_cache': False
    }
}
```

## 4. API性能监控

### 4.1 请求性能跟踪
- **问题**: 无法实时了解API请求的性能状况
- **解决方案**: 实现API请求性能跟踪，记录响应时间和资源使用情况

```python
# API性能监控中间件
class APIPerformanceMiddleware:
    """API性能监控中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = self.get_response(request)

        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 毫秒

        # 记录性能指标
        if request.path.startswith('/api/'):
            from core.services.monitor import get_monitor
            monitor = get_monitor()
            monitor.record_api_call(
                platform='internal',
                endpoint=request.path,
                success=200 <= response.status_code < 400,
                duration=response_time / 1000
            )

        # 添加响应时间头
        response['X-Response-Time'] = f'{response_time:.2f}ms'

        return response
```

### 4.2 错误率监控
- **问题**: 无法及时发现API错误率异常
- **解决方案**: 实现API错误率监控，当错误率超过阈值时触发告警

```python
# API错误率监控
class APIErrorMonitor:
    """API错误率监控"""

    def __init__(self):
        self.error_counts = defaultdict(int)
        self.total_counts = defaultdict(int)
        self.error_threshold = 0.1  # 10%错误率阈值

    def record_request(self, endpoint, success):
        """记录请求"""
        self.total_counts[endpoint] += 1
        if not success:
            self.error_counts[endpoint] += 1

        # 检查错误率
        error_rate = self.error_counts[endpoint] / self.total_counts[endpoint]
        if error_rate > self.error_threshold:
            # 触发告警
            from core.services.alerting import get_alert_service
            alert_service = get_alert_service()
            alert_service.send_alert(
                alert_type='api_high_error_rate',
                severity='warning',
                message=f'API {endpoint} error rate ({error_rate:.2f}) exceeds threshold',
                data={'endpoint': endpoint, 'error_rate': error_rate}
            )
```

## 5. API限流优化

### 5.1 智能限流
- **问题**: 固定限流策略可能影响正常用户的访问
- **解决方案**: 实现基于用户类型和行为的智能限流

```python
# 智能限流类
class SmartRateThrottle(throttling.BaseThrottle):
    """智能限流"""

    def allow_request(self, request, view):
        """判断是否允许请求"""
        # 根据用户类型设置不同的限流策略
        if request.user.is_staff:
            # 管理员用户，更高的限流
            return True

        # 普通用户，基于Token Bucket算法的限流
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        key = f'rate_limit:{user_id}'

        # 使用Redis实现Token Bucket
        from django.core.cache import cache

        # 获取当前令牌数
        current_tokens = cache.get(key, 100)  # 初始100个令牌

        if current_tokens > 0:
            # 消耗一个令牌
            cache.set(key, current_tokens - 1, 3600)  # 1小时窗口
            return True

        return False
```

### 5.2 批量请求限流
- **问题**: 批量请求可能被滥用，导致服务器负载过高
- **解决方案**: 实现基于请求复杂度的限流

```python
# 批量请求限流
class BatchRequestThrottle(throttling.BaseThrottle):
    """批量请求限流"""

    def allow_request(self, request, view):
        """判断是否允许批量请求"""
        if request.method == 'POST' and request.path == '/api/batch/':
            operations = request.data.get('operations', [])
            operation_count = len(operations)

            # 限制批量操作数量
            if operation_count > 10:
                return False

            # 计算请求复杂度
            complexity = sum(self._calculate_complexity(op) for op in operations)

            # 限制复杂度
            if complexity > 50:
                return False

        return True

    def _calculate_complexity(self, operation):
        """计算操作复杂度"""
        method = operation.get('method', 'GET').upper()
        if method in ['POST', 'PUT', 'DELETE']:
            return 5
        return 1
```

## 6. API响应优化

### 6.1 分页优化
- **问题**: 大列表查询可能导致响应时间过长
- **解决方案**: 优化分页实现，支持游标分页和部分字段加载

```python
# 优化的分页类
class OptimizedPagination(PageNumberPagination):
    """优化的分页类"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """优化的分页响应"""
        return Response({
            'results': data,
            'pagination': {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'page_size': self.page_size,
                'total_pages': self.page.paginator.num_pages,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            }
        })
```

### 6.2 响应压缩
- **问题**: 大响应体可能导致网络传输时间过长
- **解决方案**: 实现响应压缩，减少传输数据量

```python
# 响应压缩中间件
class ResponseCompressionMiddleware:
    """响应压缩中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 检查是否支持压缩
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

        if 'gzip' in accept_encoding and response.status_code == 200:
            # 压缩响应内容
            import gzip
            import io

            content = response.content
            if len(content) > 1024:  # 只压缩大于1KB的内容
                compressed_content = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed_content, mode='w') as f:
                    f.write(content)

                response.content = compressed_content.getvalue()
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = str(len(response.content))

        return response
```

### 6.3 预加载关联数据
- **问题**: N+1查询问题导致响应时间过长
- **解决方案**: 实现智能预加载，减少数据库查询次数

```python
# 智能预加载装饰器
def preload_related(*related_fields):
    """智能预加载装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # 检查是否需要预加载
            if hasattr(self, 'queryset'):
                # 应用预加载
                self.queryset = self.queryset.select_related(*related_fields)
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator
```

## 7. 实施计划

### 7.1 短期优化（1-2周）
1. 实现API请求批处理端点
2. 优化序列化器字段选择
3. 实现智能缓存策略
4. 部署API性能监控中间件

### 7.2 中期优化（2-4周）
1. 实现条件缓存和缓存分层
2. 优化分页实现
3. 部署响应压缩中间件
4. 实现智能限流

### 7.3 长期优化（1-3个月）
1. 实现异步序列化
2. 优化批量请求处理
3. 建立API性能监控 dashboard
4. 持续优化API响应时间

## 8. 预期效果

- **API响应时间**: 预计减少 40-60%
- **网络传输量**: 预计减少 30-50%
- **服务器负载**: 预计降低 25-40%
- **并发处理能力**: 预计提高 50-100%

## 9. 风险评估

- **缓存一致性**: 需要确保缓存与数据库数据的一致性
- **开发复杂度**: 增加了代码复杂度，需要更多的测试和维护
- **兼容性**: 可能需要前端配合调整，以充分利用新的API特性

## 10. 监控和验证

- **性能测试**: 使用压测工具测试API性能
- **监控指标**: 监控API响应时间、错误率、吞吐量等指标
- **用户反馈**: 收集用户对API性能的反馈
- **持续优化**: 根据监控结果持续调整优化策略
