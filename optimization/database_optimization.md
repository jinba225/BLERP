# 数据库性能优化方案

## 1. 索引优化

### 1.1 现有索引分析
- **SalesOrder**: 已有的索引包括 (status, order_date), (payment_status, order_date), (customer, status), (sales_rep, order_date)
- **SalesOrderItem**: 已有的索引包括 (order, product), (product, delivered_quantity), (order, delivered_quantity)
- **Quote**: 已有的索引包括 (status, quote_date), (customer, status), (valid_until, status)
- **Delivery**: 已有的索引包括 (status, planned_date), (sales_order, status), (warehouse, status), (tracking_number)

### 1.2 建议添加的索引

#### SalesOrder
- `(customer, order_date)`: 优化按客户和日期查询的场景
- `(order_number)`: 虽然 order_number 是唯一的，但明确添加索引可以提高查询性能
- `(created_at)`: 优化按创建时间排序的查询

#### SalesOrderItem
- `(product, order)`: 与现有 (order, product) 索引互补，优化按产品查询订单的场景
- `(line_total)`: 优化按金额排序的查询

#### Quote
- `(quote_number)`: 明确添加索引提高查询性能
- `(customer, quote_date)`: 优化按客户和报价日期查询的场景

#### Delivery
- `(actual_date)`: 优化按实际发货日期查询的场景
- `(delivered_date)`: 优化按送达日期查询的场景

## 2. 查询优化

### 2.1 批量查询优化
- **问题**: 在 `calculate_totals` 方法中使用 `self.items.all()` 触发多次数据库查询
- **解决方案**: 使用 `aggregate` 函数减少数据库查询

```python
# 优化前
self.subtotal = sum([item.line_total for item in self.items.all()])

# 优化后
from django.db.models import Sum
result = self.items.aggregate(total=Sum('line_total'))
self.subtotal = result['total'] or 0
```

### 2.2 预加载优化
- **问题**: 在 `approve_order` 等方法中，多次访问关联对象导致 N+1 查询问题
- **解决方案**: 使用 `select_related` 和 `prefetch_related` 预加载关联数据

```python
# 优化前
for order_item in self.items.all():
    product = order_item.product  # 每次访问都会触发新的查询

# 优化后
for order_item in self.items.select_related('product').all():
    product = order_item.product  # 已预加载，无额外查询
```

### 2.3 批量操作优化
- **问题**: 在 `approve_order` 方法中，创建多个对象时每个都单独保存
- **解决方案**: 使用批量创建减少数据库操作次数

```python
# 优化前
for order_item in self.items.all():
    DeliveryItem.objects.create(
        delivery=delivery,
        order_item=order_item,
        quantity=order_item.remaining_quantity,
        created_by=approved_by_user,
    )

# 优化后
delivery_items = []
for order_item in self.items.all():
    delivery_items.append(DeliveryItem(
        delivery=delivery,
        order_item=order_item,
        quantity=order_item.remaining_quantity,
        created_by=approved_by_user,
    ))
DeliveryItem.objects.bulk_create(delivery_items)
```

## 3. 数据库连接池配置

### 3.1 PostgreSQL 连接池优化
- **现有配置**: CONN_MAX_AGE=600 (10分钟)
- **建议优化**:
  - 增加 CONN_MAX_AGE 到 1800 (30分钟)，减少连接创建开销
  - 调整连接池大小，根据服务器内存和并发请求数设置
  - 启用连接健康检查，确保连接有效性

### 3.2 连接池参数调整
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'CONN_MAX_AGE': 1800,  # 30分钟连接重用
        'CONN_HEALTH_CHECKS': True,  # 启用连接健康检查
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30秒查询超时
            'sslmode': 'prefer',  # 优先使用SSL连接
            'pool_size': 20,  # 连接池大小
            'max_overflow': 10,  # 最大溢出连接数
        },
    }
}
```

## 4. 事务优化

### 4.1 事务使用
- **问题**: 在 `approve_order` 和 `unapprove_order` 方法中，没有使用数据库事务
- **解决方案**: 使用事务确保数据一致性和提高性能

```python
from django.db import transaction

@transaction.atomic
def approve_order(self, approved_by_user, warehouse=None, auto_create_delivery=None):
    # 现有代码...
    pass

@transaction.atomic
def unapprove_order(self):
    # 现有代码...
    pass
```

## 5. 数据冗余优化

### 5.1 计算字段优化
- **问题**: 一些计算字段（如 `total_amount`）在数据库中存储，可能导致数据不一致
- **解决方案**: 考虑使用计算字段或视图来减少数据冗余

```python
# 可以考虑使用@property方法计算，而不是存储在数据库中
@property
def total_amount(self):
    """计算总金额"""
    from django.db.models import Sum
    result = self.items.aggregate(total=Sum('line_total'))
    subtotal = result['total'] or 0
    discount_amount = subtotal * (self.discount_rate / Decimal('100'))
    discounted_total = subtotal - discount_amount
    return discounted_total + self.shipping_cost
```

## 6. 分区表策略

### 6.1 大型表分区
- **建议**: 对于大型表（如销售订单、发货单），考虑使用时间分区
- **实施**: 使用 PostgreSQL 的分区表功能，按年或季度分区

```sql
-- 示例：按年分区销售订单表
CREATE TABLE sales_order (
    id BIGSERIAL PRIMARY KEY,
    order_number VARCHAR(100) UNIQUE,
    customer_id INTEGER REFERENCES customers_customer(id),
    order_date DATE,
    -- 其他字段...
)
PARTITION BY RANGE (order_date);

-- 创建分区
CREATE TABLE sales_order_2024 PARTITION OF sales_order
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE sales_order_2025 PARTITION OF sales_order
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

## 7. 性能监控

### 7.1 慢查询监控
- **建议**: 启用 PostgreSQL 的慢查询日志
- **配置**:
  ```
  log_min_duration_statement = 1000  # 记录执行时间超过1秒的查询
  log_statement = 'all'  # 记录所有SQL语句
  ```

### 7.2 数据库性能指标
- **建议**: 监控以下指标
  - 连接数
  - 查询执行时间
  - 缓存命中率
  - 索引使用情况

## 8. 实施计划

### 8.1 短期优化（1-2周）
1. 添加建议的索引
2. 优化批量查询和预加载
3. 调整连接池配置
4. 添加事务支持

### 8.2 中期优化（2-4周）
1. 实施批量操作优化
2. 优化计算字段
3. 启用慢查询监控
4. 分析并优化现有查询

### 8.3 长期优化（1-3个月）
1. 实施分区表策略
2. 优化数据模型结构
3. 建立数据库性能监控系统
4. 定期进行数据库维护

## 9. 预期效果

- **查询性能提升**: 预计查询速度提升 30-50%
- **数据库负载降低**: 预计数据库负载降低 20-30%
- **系统响应时间改善**: 预计系统响应时间改善 25-40%
- **数据一致性提高**: 通过事务和优化的数据模型，提高数据一致性

## 10. 风险评估

- **索引增加**: 可能会增加写操作的开销，但对于读多写少的场景是值得的
- **分区表**: 实施复杂度较高，需要谨慎规划
- **代码修改**: 需要确保所有修改都经过充分测试，避免引入新问题

## 11. 监控和验证

- **性能基准测试**: 在优化前后进行性能基准测试
- **监控工具**: 使用 PostgreSQL 的内置工具和第三方监控工具
- **用户反馈**: 收集用户对系统性能的反馈
- **持续优化**: 根据监控结果持续调整优化策略
