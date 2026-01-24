# BetterLaser ERP - 测试开发指南

> **目标**: 帮助开发者编写高质量、可维护的测试代码
> **更新时间**: 2026-01-06

---

## 目录

1. [测试哲学](#一测试哲学)
2. [测试类型](#二测试类型)
3. [编写单元测试](#三编写单元测试)
4. [编写API测试](#四编写api测试)
5. [编写集成测试](#五编写集成测试)
6. [使用Factory Boy](#六使用factory-boy)
7. [Mock和Patch](#七mock和patch)
8. [测试数据管理](#八测试数据管理)
9. [性能测试](#九性能测试)
10. [常见问题](#十常见问题)

---

## 一、测试哲学

### 1.1 核心原则

✅ **测试驱动开发 (TDD)**
```python
# 1. 先写测试（红灯）
def test_order_total_calculation(self):
    order = SalesOrder(...)
    self.assertEqual(order.calculate_total(), Decimal('100.00'))

# 2. 写最少代码让测试通过（绿灯）
def calculate_total(self):
    return Decimal('100.00')

# 3. 重构代码（保持绿灯）
def calculate_total(self):
    return sum(item.line_total for item in self.items.all())
```

✅ **AAA模式 (Arrange-Act-Assert)**
```python
def test_approve_order(self):
    # Arrange - 准备测试数据
    order = SalesOrderFactory(status='draft')
    user = UserFactory()

    # Act - 执行操作
    order.approve_order(approved_by=user)

    # Assert - 验证结果
    self.assertEqual(order.status, 'confirmed')
    self.assertEqual(order.approved_by, user)
```

✅ **FIRST原则**
- **Fast** (快速): 单元测试 < 1s
- **Independent** (独立): 测试间无依赖
- **Repeatable** (可重复): 任何环境都能运行
- **Self-Validating** (自验证): 通过/失败，无需人工检查
- **Timely** (及时): 与代码同步开发

### 1.2 什么时候写测试?

| 场景 | 说明 | 示例 |
|------|------|------|
| **新功能开发** | TDD优先，先写测试 | 添加订单审核功能 |
| **Bug修复** | 先写失败测试，再修复 | 修复税额计算错误 |
| **代码重构** | 保持测试通过 | 优化订单查询性能 |
| **API开发** | 同步编写API测试 | 新增订单列表接口 |
| **业务逻辑** | 必须有测试覆盖 | 含税价格计算 |

---

## 二、测试类型

### 2.1 测试金字塔

```
        E2E (5%)          - Playwright
      /        \
    Integration (15%)     - TransactionTestCase
   /              \
  API (30%)             - APITestCase
 /                  \
Unit (50%)              - TestCase
```

### 2.2 选择合适的测试类型

| 测试对象 | 测试类型 | 基类 |
|----------|----------|------|
| 模型方法 | 单元测试 | `TestCase` |
| 服务函数 | 单元测试 | `TestCase` |
| REST API | API测试 | `APITestCase` |
| 跨模块流程 | 集成测试 | `TransactionTestCase` |
| 用户操作 | E2E测试 | `Playwright` |

---

## 三、编写单元测试

### 3.1 模型测试模板

```python
# apps/sales/tests/test_models.py
from django.test import TestCase
from decimal import Decimal
from apps.sales.models import SalesOrder, SalesOrderItem
from apps.sales.factories import SalesOrderFactory, SalesOrderItemFactory

class SalesOrderModelTestCase(TestCase):
    """销售订单模型测试"""

    def setUp(self):
        """每个测试前执行"""
        self.order = SalesOrderFactory()
        self.item1 = SalesOrderItemFactory(
            order=self.order,
            quantity=2,
            unit_price=Decimal('100.00')
        )
        self.item2 = SalesOrderItemFactory(
            order=self.order,
            quantity=1,
            unit_price=Decimal('200.00')
        )

    def test_order_creation(self):
        """测试订单创建"""
        self.assertIsNotNone(self.order.id)
        self.assertEqual(self.order.status, 'draft')
        self.assertIsNotNone(self.order.order_number)

    def test_order_total_calculation(self):
        """测试订单总金额计算"""
        expected_total = Decimal('400.00')  # 2*100 + 1*200
        self.assertEqual(self.order.calculate_total(), expected_total)

    def test_order_str_representation(self):
        """测试字符串表示"""
        expected = f"{self.order.order_number} - {self.order.customer.name}"
        self.assertEqual(str(self.order), expected)

    def test_order_soft_delete(self):
        """测试软删除"""
        self.order.delete()
        self.assertTrue(self.order.is_deleted)
        self.assertIsNotNone(self.order.deleted_at)

    def tearDown(self):
        """每个测试后执行（可选）"""
        pass
```

### 3.2 服务层测试模板

```python
# apps/sales/tests/test_services.py
from django.test import TestCase
from apps.sales.services import OrderApprovalService
from apps.sales.factories import SalesOrderFactory
from apps.inventory.factories import WarehouseFactory

class OrderApprovalServiceTestCase(TestCase):
    """订单审核服务测试"""

    def setUp(self):
        self.service = OrderApprovalService()
        self.warehouse = WarehouseFactory()
        self.order = SalesOrderFactory(status='draft')

    def test_approve_creates_delivery(self):
        """测试审核创建发货单"""
        delivery = self.service.approve_order(
            order=self.order,
            warehouse=self.warehouse
        )

        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.order, self.order)
        self.assertEqual(delivery.warehouse, self.warehouse)

    def test_approve_creates_customer_account(self):
        """测试审核创建应收账款"""
        result = self.service.approve_order(
            order=self.order,
            warehouse=self.warehouse
        )

        account = CustomerAccount.objects.get(sales_order=self.order)
        self.assertIsNotNone(account)
        self.assertEqual(account.amount, self.order.total_amount)

    def test_approve_validates_stock(self):
        """测试审核验证库存"""
        # 设置库存不足
        self.order.items.first().product.stock = 0

        with self.assertRaises(InsufficientStockError):
            self.service.approve_order(
                order=self.order,
                warehouse=self.warehouse
            )
```

### 3.3 测试命名规范

✅ **好的命名**:
```python
def test_approve_order_creates_delivery(self):           # 清晰描述
def test_calculate_tax_with_13_percent_rate(self):      # 包含场景
def test_order_cancellation_updates_inventory(self):    # 说明预期
```

❌ **不好的命名**:
```python
def test_1(self):                    # 无意义
def test_order(self):                # 太模糊
def test_it_works(self):             # 不明确
```

### 3.4 断言最佳实践

```python
# ✅ 使用具体的断言方法
self.assertEqual(order.status, 'confirmed')
self.assertTrue(order.is_approved)
self.assertIsNone(order.cancelled_at)
self.assertIn('success', response.data)
self.assertGreater(order.total_amount, Decimal('0'))

# ❌ 避免模糊的断言
self.assertTrue(order.status == 'confirmed')  # 用assertEqual更好
self.assertTrue(len(items) > 0)               # 用assertGreater更好
```

---

## 四、编写API测试

### 4.1 API测试模板

```python
# apps/sales/tests/test_api.py
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from apps.users.factories import UserFactory
from apps.sales.factories import SalesOrderFactory

class SalesOrderAPITestCase(APITestCase):
    """销售订单API测试"""

    def setUp(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('api:salesorder-list')

    def test_list_orders_success(self):
        """测试获取订单列表 - 成功"""
        # 创建测试数据
        SalesOrderFactory.create_batch(5)

        # 发送请求
        response = self.client.get(self.list_url)

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)

    def test_list_orders_with_filter(self):
        """测试订单列表过滤"""
        # 创建不同状态的订单
        SalesOrderFactory(status='draft')
        SalesOrderFactory(status='confirmed')

        # 过滤draft状态
        response = self.client.get(self.list_url, {'status': 'draft'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'draft')

    def test_create_order_success(self):
        """测试创建订单 - 成功"""
        data = {
            'customer': 1,
            'order_date': '2026-01-06',
            'items': [
                {
                    'product': 1,
                    'quantity': 2,
                    'unit_price': '100.00'
                }
            ]
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_number', response.data)
        self.assertEqual(response.data['status'], 'draft')

    def test_create_order_invalid_data(self):
        """测试创建订单 - 无效数据"""
        data = {
            'customer': None,  # 缺少必填字段
            'order_date': 'invalid-date'
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer', response.data)

    def test_retrieve_order_success(self):
        """测试获取订单详情 - 成功"""
        order = SalesOrderFactory()
        url = reverse('api:salesorder-detail', args=[order.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], order.id)
        self.assertEqual(response.data['order_number'], order.order_number)

    def test_retrieve_order_not_found(self):
        """测试获取订单详情 - 不存在"""
        url = reverse('api:salesorder-detail', args=[99999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_order_success(self):
        """测试更新订单 - 成功"""
        order = SalesOrderFactory()
        url = reverse('api:salesorder-detail', args=[order.id])

        data = {'notes': '更新的备注'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], '更新的备注')

    def test_delete_order_success(self):
        """测试删除订单 - 成功"""
        order = SalesOrderFactory()
        url = reverse('api:salesorder-detail', args=[order.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        order.refresh_from_db()
        self.assertTrue(order.is_deleted)

    def test_approve_order_custom_action(self):
        """测试订单审核 - 自定义动作"""
        order = SalesOrderFactory(status='draft')
        url = reverse('api:salesorder-approve', args=[order.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

### 4.2 API测试检查清单

每个API端点都应该测试:

- ✅ 认证检查 (401)
- ✅ 权限检查 (403)
- ✅ 成功响应 (200/201)
- ✅ 验证错误 (400)
- ✅ 资源不存在 (404)
- ✅ 分页
- ✅ 过滤
- ✅ 搜索
- ✅ 排序
- ✅ 自定义动作

---

## 五、编写集成测试

### 5.1 集成测试模板

```python
# apps/sales/tests/test_integration.py
from django.test import TransactionTestCase
from apps.sales.factories import SalesOrderFactory
from apps.inventory.factories import WarehouseFactory, InventoryStockFactory
from apps.finance.models import CustomerAccount
from apps.sales.models import Delivery

class SalesOrderIntegrationTestCase(TransactionTestCase):
    """销售订单集成测试"""

    def setUp(self):
        self.warehouse = WarehouseFactory()
        self.order = SalesOrderFactory(status='draft')

        # 创建库存
        for item in self.order.items.all():
            InventoryStockFactory(
                warehouse=self.warehouse,
                product=item.product,
                available_quantity=100
            )

    def test_complete_order_workflow(self):
        """测试完整的订单工作流"""
        # 1. 审核订单
        self.order.approve_order(approved_by=self.user, warehouse=self.warehouse)

        # 2. 验证订单状态
        self.assertEqual(self.order.status, 'confirmed')

        # 3. 验证发货单生成
        delivery = Delivery.objects.get(order=self.order)
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.status, 'pending')

        # 4. 验证应收账款生成
        account = CustomerAccount.objects.get(sales_order=self.order)
        self.assertIsNotNone(account)
        self.assertEqual(account.amount, self.order.total_amount)

        # 5. 确认发货
        delivery.confirm_delivery()

        # 6. 验证库存扣减
        for item in self.order.items.all():
            stock = InventoryStock.objects.get(
                warehouse=self.warehouse,
                product=item.product
            )
            expected_qty = 100 - item.quantity
            self.assertEqual(stock.available_quantity, expected_qty)

        # 7. 验证订单完成
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')
```

---

## 六、使用Factory Boy

### 6.1 基本用法

```python
from apps.sales.factories import SalesOrderFactory

# 创建单个对象
order = SalesOrderFactory()

# 创建多个对象
orders = SalesOrderFactory.create_batch(10)

# 不保存到数据库（仅构建对象）
order = SalesOrderFactory.build()

# 自定义字段
order = SalesOrderFactory(
    status='confirmed',
    customer__name='特定客户名称'  # 级联自定义
)

# 创建相关对象
order = SalesOrderFactory()
items = SalesOrderItemFactory.create_batch(3, order=order)
```

### 6.2 定义Factory

```python
# apps/sales/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.sales.models import SalesOrder

class SalesOrderFactory(DjangoModelFactory):
    class Meta:
        model = SalesOrder

    # Sequence: 自动递增
    order_number = factory.Sequence(lambda n: f'SO2026{n:06d}')

    # SubFactory: 外键关系
    customer = factory.SubFactory(CustomerFactory)

    # LazyAttribute: 动态计算
    delivery_date = factory.LazyAttribute(
        lambda obj: obj.order_date + timedelta(days=30)
    )

    # FuzzyChoice: 随机选择
    status = factory.fuzzy.FuzzyChoice(['draft', 'confirmed'])

    # Faker: 随机生成
    notes = factory.Faker('text', max_nb_chars=200, locale='zh_CN')
```

---

## 七、Mock和Patch

### 7.1 使用unittest.mock

```python
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase

class ExternalAPITestCase(TestCase):
    """外部API调用测试"""

    @patch('apps.sales.services.send_email')
    def test_order_approval_sends_email(self, mock_send_email):
        """测试订单审核发送邮件"""
        order = SalesOrderFactory()

        order.approve_order(approved_by=self.user)

        # 验证邮件发送被调用
        mock_send_email.assert_called_once()

        # 验证调用参数
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[0][0], order.customer.email)

    @patch('requests.post')
    def test_payment_api_call(self, mock_post):
        """测试支付API调用"""
        # 设置Mock返回值
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_post.return_value = mock_response

        # 执行测试
        result = process_payment(order_id=1, amount=100)

        # 验证
        self.assertEqual(result['status'], 'success')
        mock_post.assert_called_once()
```

### 7.2 Mock常见场景

```python
# Mock时间
from freezegun import freeze_time

@freeze_time("2026-01-06 12:00:00")
def test_with_fixed_time(self):
    order = SalesOrderFactory()
    self.assertEqual(order.created_at.date(), date(2026, 1, 6))

# Mock文件上传
from django.core.files.uploadedfile import SimpleUploadedFile

def test_file_upload(self):
    file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
    attachment = Attachment.objects.create(file=file)
    self.assertTrue(attachment.file.name.endswith('.pdf'))

# Mock环境变量
@patch.dict('os.environ', {'DEBUG': 'False'})
def test_production_mode(self):
    self.assertFalse(settings.DEBUG)
```

---

## 八、测试数据管理

### 8.1 使用setUp和tearDown

```python
class MyTestCase(TestCase):
    def setUp(self):
        """每个测试前执行"""
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """每个测试后执行（可选）"""
        # 通常不需要，Django会自动清理
        pass

    @classmethod
    def setUpTestData(cls):
        """所有测试前执行一次（只读数据）"""
        cls.shared_customer = CustomerFactory()
```

### 8.2 使用Fixtures

```python
class MyTestCase(TestCase):
    fixtures = ['initial_data.json', 'test_users.json']

    def test_with_fixtures(self):
        user = User.objects.get(username='testuser')
        self.assertIsNotNone(user)
```

---

## 九、性能测试

### 9.1 使用Locust

参见 `locustfile.py`

```bash
# 启动Locust
locust -f locustfile.py --host=http://localhost:8000

# 命令行模式
locust -f locustfile.py --host=http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 60s --headless
```

### 9.2 使用Django Silk

```python
# settings.py
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']
INSTALLED_APPS += ['silk']

# 访问性能分析面板
# http://localhost:8000/silk/
```

---

## 十、常见问题

### 10.1 测试数据库问题

**问题**: 测试太慢
```python
# 解决方案1: 使用--keepdb保持数据库
python manage.py test --keepdb

# 解决方案2: 在pytest中配置
# pytest.ini
[pytest]
addopts = --reuse-db
```

**问题**: 迁移太慢
```python
# 跳过迁移（仅SQLite）
pytest --nomigrations
```

### 10.2 测试隔离问题

**问题**: 测试互相影响
```python
# 解决方案: 使用TransactionTestCase
from django.test import TransactionTestCase

class MyTestCase(TransactionTestCase):
    # 每个测试都会回滚事务
    pass
```

### 10.3 异步测试

```python
from django.test import TestCase
import asyncio

class AsyncTestCase(TestCase):
    def test_async_function(self):
        async def async_task():
            return "result"

        result = asyncio.run(async_task())
        self.assertEqual(result, "result")
```

---

## 附录: 快速参考

### 常用断言方法

```python
# 相等性
assertEqual(a, b)
assertNotEqual(a, b)

# 真假
assertTrue(x)
assertFalse(x)

# 存在性
assertIsNone(x)
assertIsNotNone(x)

# 包含
assertIn(a, b)
assertNotIn(a, b)

# 比较
assertGreater(a, b)
assertGreaterEqual(a, b)
assertLess(a, b)
assertLessEqual(a, b)

# 异常
assertRaises(Exception)
assertRaisesMessage(Exception, "message")

# 查询集
assertQuerysetEqual(qs1, qs2)

# HTTP响应
assertEqual(response.status_code, 200)
assertContains(response, "text")
assertRedirects(response, "/url/")
```

### 测试运行命令

```bash
# Django测试
python manage.py test
python manage.py test apps.sales
python manage.py test apps.sales.tests.test_models.SalesOrderTestCase

# Pytest
pytest apps/
pytest apps/sales/
pytest apps/sales/tests/test_models.py::TestClass::test_method
pytest -k "order"  # 运行匹配的测试
pytest -m "slow"   # 运行标记的测试
pytest -x          # 遇到失败停止
pytest --pdb       # 失败时进入调试器

# 覆盖率
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

**更新时间**: 2026-01-06
**维护人**: 测试团队
