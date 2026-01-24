# BetterLaser ERP 完整测试计划
> **制定日期**: 2026-01-06
> **制定人**: 猫娘工程师 幽浮喵
> **项目版本**: v1.0
> **测试目标**: 确保系统质量、稳定性和可靠性

---

## 目录
1. [项目概览](#一项目概览)
2. [测试策略](#二测试策略)
3. [测试范围](#三测试范围)
4. [测试类型与优先级](#四测试类型与优先级)
5. [详细测试计划](#五详细测试计划)
6. [测试工具与框架](#六测试工具与框架)
7. [测试环境配置](#七测试环境配置)
8. [测试执行计划](#八测试执行计划)
9. [质量指标与验收标准](#九质量指标与验收标准)
10. [风险与依赖](#十风险与依赖)

---

## 一、项目概览

### 1.1 项目基本信息

| 项目 | 信息 |
|------|------|
| **项目名称** | BetterLaser ERP (Better Laser Enterprise Resource Planning System) |
| **技术栈** | Django 5.0.9 + DRF 3.15.2 + Tailwind CSS + SQLite/MySQL |
| **代码规模** | 43,591 行 Python 代码 \| 196 个文件 |
| **应用模块** | 11 个独立业务模块 |
| **数据模型** | 88 个核心业务模型 |
| **数据库迁移** | 52 个迁移文件 |

### 1.2 业务模块列表

| 模块 | 职责 | 模型数 | 现有测试 |
|------|------|--------|----------|
| **core** | 核心基础、系统配置、审计日志 | 9 | ✅ 100% (587行) |
| **authentication** | JWT认证、令牌管理 | - | ✅ 部分 (262行) |
| **users** | 用户管理、角色权限 | 6 | ✅ 100% (595行) |
| **departments** | 部门管理、组织架构 | 3 | ✅ 100% (485行) |
| **customers** | 客户管理、分类、联系人 | 6 | ✅ 100% (620行) |
| **suppliers** | 供应商管理、评估 | 5 | ✅ 100% (578行) |
| **products** | 产品管理、分类、品牌 | 8 | ✅ 100% (525行) |
| **sales** | 报价、订单、发货、退货 | 8 | ✅ 100% (1,531行) |
| **purchase** | 采购、询价、质检、NCP | 16 | ✅ 100% (1,075行) |
| **inventory** | 库存管理、出入库、调拨 | 13 | ✅ 100% (1,775行) |
| **finance** | 应收应付、发票、费用 | 14 | ✅ 100% (684行) |
| **总计** | - | **88** | **8,717 行测试代码** |

### 1.3 现有测试覆盖情况

```
测试类型           当前状态       覆盖率      优先级
──────────────────────────────────────────────
单元测试（模型）     ✅ 完整       100%       已完成
单元测试（服务层）   ⚠️ 部分       60%        P0
单元测试（视图层）   ⚠️ 部分       20%        P1
API集成测试         ❌ 缺失       0%         P0
业务流程测试         ⚠️ 部分       40%        P0
功能测试（前端）     ❌ 缺失       0%         P1
性能测试            ❌ 缺失       0%         P2
安全测试            ❌ 缺失       0%         P1
端到端测试          ❌ 缺失       0%         P2
负载测试            ❌ 缺失       0%         P3
```

**评估总结**:
- ✅ **优势**: 模型层测试非常完整（8,717行测试代码）
- ⚠️ **挑战**: 缺少API、集成、功能、性能等高层次测试
- 🎯 **目标**: 将整体测试覆盖率从 60% 提升到 90%+

---

## 二、测试策略

### 2.1 测试金字塔

```
                  /\
                 /  \         端到端测试 (E2E)
                /____\        - 5% 覆盖
               /      \
              /  集成  \      集成测试 (Integration)
             /   测试   \     - 15% 覆盖
            /__________\
           /            \
          /   API 测试   \   API测试 (API Tests)
         /               \  - 30% 覆盖
        /________________\
       /                  \
      /      单元测试       \ 单元测试 (Unit Tests)
     /                     \- 50% 覆盖
    /______________________\
```

**测试策略原则**:
1. ✅ **单元测试为基础**: 已完成模型层，需补充服务层和工具类
2. 🎯 **API测试为重点**: 优先级最高，覆盖所有REST端点
3. 🔄 **集成测试为保障**: 验证模块间协作和业务流程
4. 🚀 **端到端测试为验证**: 关键业务路径的用户视角测试
5. ⚡ **性能测试为优化**: 识别瓶颈和优化点

### 2.2 测试优先级定义

| 优先级 | 定义 | 测试类型 | 时间分配 |
|--------|------|----------|----------|
| **P0** | 核心功能，必须完成 | 单元测试（服务层）、API测试、业务流程测试 | 50% |
| **P1** | 重要功能，优先完成 | 视图层测试、功能测试、安全测试 | 30% |
| **P2** | 增强功能，尽量完成 | 端到端测试、性能测试 | 15% |
| **P3** | 可选功能，时间允许 | 负载测试、压力测试、可用性测试 | 5% |

### 2.3 测试方法论

**测试驱动开发 (TDD)**:
- 新功能开发：先写测试，再写代码
- 修复bug：先写失败测试，再修复代码
- 重构：保持测试通过的前提下重构

**行为驱动开发 (BDD)**:
- 使用Given-When-Then模式描述测试场景
- 关注业务价值和用户行为
- 适用于集成测试和端到端测试

**持续集成 (CI)**:
- 每次提交自动运行测试
- 测试失败阻止合并
- 测试覆盖率报告

---

## 三、测试范围

### 3.1 功能范围矩阵

| 模块 | 单元测试 | API测试 | 集成测试 | E2E测试 | 性能测试 |
|------|----------|---------|----------|---------|----------|
| **Core** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | - | ❌ 缺失 |
| **Authentication** | ⚠️ 部分 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | - |
| **Users** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | - |
| **Departments** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | - | - |
| **Customers** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | - |
| **Suppliers** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | - |
| **Products** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | - |
| **Sales** | ✅ 完整 | ❌ 缺失 | ⚠️ 部分 | ✅ 需要 | ✅ 需要 |
| **Purchase** | ✅ 完整 | ❌ 缺失 | ⚠️ 部分 | ✅ 需要 | ✅ 需要 |
| **Inventory** | ✅ 完整 | ❌ 缺失 | ⚠️ 部分 | ✅ 需要 | ✅ 需要 |
| **Finance** | ✅ 完整 | ❌ 缺失 | ❌ 缺失 | ✅ 需要 | ✅ 需要 |

### 3.2 关键业务流程

**需要端到端测试的核心流程**:

1. **销售流程** (P0 - 最高优先级):
   ```
   创建报价单 → 发送客户 → 报价转订单 → 订单审核 →
   自动生成发货单和应收账款 → 发货确认 → 库存扣减 →
   收款记录 → 应收核销 → 完成订单
   ```

2. **采购流程** (P0):
   ```
   创建采购询价 → 供应商报价 → 报价对比 → 生成采购订单 →
   订单审核 → 收货确认 → 质检流程 → 入库处理 →
   生成应付账款 → 付款处理 → 完成采购
   ```

3. **质检与不合格品处理流程** (P0):
   ```
   收货质检 → 不合格品记录 → NCP分类（退货/返工/报废/让步） →
   处理流程 → 库存调整 → 供应商评级更新
   ```

4. **库存管理流程** (P1):
   ```
   入库单创建 → 库存增加 → 库位分配 →
   出库单创建 → 库存扣减 → 低库存预警 →
   库存调拨 → 库存盘点 → 库存调整
   ```

5. **退货流程** (P1):
   ```
   客户申请退货 → 审核退货申请 → 生成通知 →
   收到退货 → 库存回补 → 退款处理 → 应收调整
   ```

6. **财务对账流程** (P1):
   ```
   应收账款生成 → 收款记录 → 账款核销 →
   应付账款生成 → 付款处理 → 账款核销 →
   日终对账 → 账户余额更新 → 财务报表
   ```

### 3.3 非功能性测试范围

| 测试类型 | 范围 | 优先级 |
|----------|------|--------|
| **性能测试** | 关键查询、报表生成、批量操作 | P2 |
| **负载测试** | 并发用户、订单高峰期 | P3 |
| **安全测试** | 身份验证、授权、SQL注入、XSS | P1 |
| **兼容性测试** | 浏览器、移动设备 | P2 |
| **可用性测试** | 用户体验、界面友好性 | P3 |
| **数据完整性测试** | 事务一致性、备份恢复 | P1 |

---

## 四、测试类型与优先级

### 4.1 单元测试 (Unit Tests) - 50%覆盖

**定义**: 测试单个函数、方法或类的行为

**现状**:
- ✅ **已完成**: 模型层测试 100% (8,717行)
- ⚠️ **需补充**: 服务层、工具类、视图层

**待补充测试**:

#### 4.1.1 服务层测试 (P0 - 优先级最高)

| 模块 | 服务文件 | 测试要点 | 估计工作量 |
|------|----------|----------|------------|
| **Core** | `utils/document_number.py` | 单据号生成逻辑、并发安全 | 2天 |
| **Core** | `utils/code_generator.py` | 编码生成、唯一性验证 | 1天 |
| **Core** | `services/template_selector.py` | 模板选择逻辑 | 1天 |
| **Sales** | `services/business.py` | 报价转订单、订单审核、发货逻辑 | 3天 |
| **Purchase** | `services.py` | 询价、报价对比、质检流程 | 3天 |
| **Inventory** | `services.py` | 库存扣减、调拨、盘点 | 3天 |
| **Finance** | （待创建） | 账款计算、核销逻辑 | 2天 |

**测试模板**:
```python
# apps/sales/tests/test_services.py
from django.test import TestCase
from apps.sales.services.business import OrderApprovalService
from apps.sales.models import SalesOrder
from apps.inventory.models import Warehouse

class OrderApprovalServiceTestCase(TestCase):
    """订单审核服务测试"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(name='主仓库')
        self.order = SalesOrder.objects.create(...)
        self.service = OrderApprovalService()

    def test_approve_order_creates_delivery(self):
        """测试审核订单自动生成发货单"""
        delivery = self.service.approve_order(self.order, self.warehouse)
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.order, self.order)

    def test_approve_order_creates_customer_account(self):
        """测试审核订单自动生成应收账款"""
        # ...

    def test_approve_order_validates_stock(self):
        """测试审核订单验证库存充足性"""
        # ...
```

#### 4.1.2 工具类测试 (P0)

| 工具类 | 文件路径 | 测试要点 | 估计工作量 |
|--------|----------|----------|------------|
| **DocumentNumberGenerator** | `apps/core/utils/document_number.py` | 格式验证、唯一性、并发安全 | 1天 |
| **税额计算** | （各模块） | 含税价格反推、精度验证 | 1天 |
| **权限检查** | `apps/users/utils/` | 角色权限、资源访问控制 | 1天 |
| **日期处理** | （各模块） | 时区转换、日期格式化 | 0.5天 |

#### 4.1.3 视图层测试 (P1)

**当前状态**: 只有 Sales 模块有 `test_views.py` (282行)

**需要补充的模块**:
- Purchase: 采购订单视图、质检视图
- Inventory: 出入库视图、库存查询视图
- Finance: 财务报表视图、对账视图
- Customers/Suppliers: CRUD视图

**测试要点**:
- ✅ GET请求返回正确模板和上下文
- ✅ POST请求正确处理表单提交
- ✅ 权限验证（@login_required, permission_required）
- ✅ 错误处理和消息提示
- ✅ 重定向逻辑

**测试模板**:
```python
from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User

class SalesOrderViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_order_list_view_requires_login(self):
        """测试订单列表需要登录"""
        self.client.logout()
        response = self.client.get(reverse('sales:order_list'))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页

    def test_order_list_view_returns_correct_template(self):
        """测试订单列表使用正确的模板"""
        response = self.client.get(reverse('sales:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/order_list.html')
```

---

### 4.2 API集成测试 (API Tests) - 30%覆盖 (P0 - 最高优先级)

**定义**: 测试REST API端点的请求和响应

**现状**: ❌ **完全缺失**

**目标**: 覆盖所有 ViewSet 和 API 端点

#### 4.2.1 需要测试的API端点

| 模块 | ViewSet | 端点数 | 测试要点 | 估计工作量 |
|------|---------|--------|----------|------------|
| **Authentication** | - | 3 | 登录、登出、令牌刷新 | 1天 |
| **Users** | UserViewSet | 5+ | CRUD、角色分配、权限检查 | 2天 |
| **Products** | ProductViewSet | 5+ | CRUD、分类过滤、品牌关联 | 2天 |
| **Customers** | CustomerViewSet | 5+ | CRUD、信用历史、联系人 | 2天 |
| **Suppliers** | SupplierViewSet | 5+ | CRUD、评估、产品关联 | 2天 |
| **Sales** | QuoteViewSet, OrderViewSet, DeliveryViewSet | 15+ | CRUD、状态流转、自定义动作 | 4天 |
| **Purchase** | PurchaseOrderViewSet, InspectionViewSet | 15+ | CRUD、询价、质检、NCP | 4天 |
| **Inventory** | StockViewSet, TransactionViewSet | 10+ | 库存查询、出入库、调拨 | 3天 |
| **Finance** | PaymentViewSet, InvoiceViewSet | 10+ | 收付款、发票、报表 | 3天 |

**测试框架**: Django REST Framework Test Client

**测试模板**:
```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from apps.users.models import User
from apps.sales.models import SalesOrder

class SalesOrderAPITestCase(APITestCase):
    """销售订单API测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.order = SalesOrder.objects.create(...)

    def test_list_orders(self):
        """测试获取订单列表"""
        url = reverse('api:salesorder-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_create_order(self):
        """测试创建订单"""
        url = reverse('api:salesorder-list')
        data = {
            'customer': 1,
            'order_date': '2026-01-06',
            'items': [...]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_approve_order(self):
        """测试审核订单（自定义动作）"""
        url = reverse('api:salesorder-approve', args=[self.order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        url = reverse('api:salesorder-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

#### 4.2.2 API测试检查清单

**每个端点必须测试**:
- ✅ 认证和授权（401/403错误）
- ✅ HTTP方法（GET, POST, PUT, PATCH, DELETE）
- ✅ 请求参数验证（必填字段、格式验证）
- ✅ 响应状态码（200, 201, 400, 404, 500）
- ✅ 响应数据格式（JSON结构、字段类型）
- ✅ 分页和过滤
- ✅ 搜索和排序
- ✅ 自定义动作（@action装饰器）
- ✅ 批量操作
- ✅ 错误处理和消息

---

### 4.3 集成测试 (Integration Tests) - 15%覆盖 (P0)

**定义**: 测试多个模块、服务之间的协作

**现状**: ⚠️ 部分完成（Sales、Inventory、Purchase有部分业务逻辑测试）

#### 4.3.1 核心业务流程集成测试

**1. 销售-库存-财务集成 (P0)**:
```python
# apps/sales/tests/test_integration.py
class SalesInventoryFinanceIntegrationTestCase(TestCase):
    """销售-库存-财务集成测试"""

    def test_order_approval_workflow(self):
        """测试完整的订单审核工作流"""
        # 1. 创建订单
        order = SalesOrder.objects.create(...)

        # 2. 审核订单
        order.approve_order(approved_by_user=self.user)

        # 3. 验证发货单生成
        self.assertTrue(Delivery.objects.filter(order=order).exists())

        # 4. 验证应收账款生成
        self.assertTrue(CustomerAccount.objects.filter(
            sales_order=order
        ).exists())

        # 5. 确认发货
        delivery = Delivery.objects.get(order=order)
        delivery.confirm_delivery()

        # 6. 验证库存扣减
        stock = InventoryStock.objects.get(product=order.items.first().product)
        self.assertEqual(stock.available_quantity, expected_quantity)

        # 7. 记录收款
        payment = PaymentRecord.objects.create(...)

        # 8. 验证应收核销
        account = CustomerAccount.objects.get(sales_order=order)
        self.assertEqual(account.paid_amount, payment.amount)
```

**2. 采购-质检-库存集成 (P0)**:
```python
# apps/purchase/tests/test_integration.py
class PurchaseQualityInventoryIntegrationTestCase(TestCase):
    """采购-质检-库存集成测试"""

    def test_purchase_receipt_quality_inspection_workflow(self):
        """测试收货-质检-入库完整流程"""
        # 1. 创建采购订单
        po = PurchaseOrder.objects.create(...)

        # 2. 创建收货单
        receipt = PurchaseReceipt.objects.create(purchase_order=po)

        # 3. 确认收货
        receipt.confirm_receipt()

        # 4. 自动触发质检
        inspection = QualityInspection.objects.get(receipt=receipt)
        self.assertIsNotNone(inspection)

        # 5. 质检合格
        inspection.pass_inspection(inspector=self.user)

        # 6. 自动生成入库单
        inbound = InboundOrder.objects.get(receipt=receipt)
        self.assertIsNotNone(inbound)

        # 7. 确认入库
        inbound.confirm_inbound()

        # 8. 验证库存增加
        stock = InventoryStock.objects.get(product=receipt.items.first().product)
        self.assertEqual(stock.available_quantity, expected_quantity)

    def test_purchase_ncp_handling_workflow(self):
        """测试不合格品处理流程"""
        # 质检不合格 → 生成NCP → 选择处理方式（退货） →
        # 生成采购退货单 → 库存调整 → 供应商评级下降
```

**3. 退货-库存回补-财务调整 (P1)**:
```python
# apps/sales/tests/test_integration.py
class SalesReturnIntegrationTestCase(TestCase):
    """销售退货集成测试"""

    def test_sales_return_workflow(self):
        """测试完整的销售退货流程"""
        # 1. 创建退货申请
        return_order = SalesReturn.objects.create(...)

        # 2. 审核退货
        return_order.approve_return(approved_by=self.user)

        # 3. 验证通知生成
        self.assertTrue(Notification.objects.filter(
            related_object_id=return_order.id
        ).exists())

        # 4. 收到退货
        return_order.mark_as_received()

        # 5. 处理退货
        return_order.process_return()

        # 6. 验证库存回补
        stock = InventoryStock.objects.get(product=return_order.items.first().product)
        self.assertEqual(stock.available_quantity, expected_quantity)

        # 7. 验证应收调整
        account = CustomerAccount.objects.get(sales_order=return_order.sales_order)
        self.assertEqual(account.outstanding_amount, expected_amount)
```

#### 4.3.2 跨模块依赖测试

| 测试场景 | 涉及模块 | 测试要点 | 优先级 |
|----------|----------|----------|--------|
| 订单审核工作流 | Sales + Inventory + Finance | 发货单、库存、应收自动生成 | P0 |
| 采购入库工作流 | Purchase + Inventory | 质检、入库、库存增加 | P0 |
| 质检不合格处理 | Purchase + Inventory | NCP处理、库存调整、供应商评级 | P0 |
| 销售退货流程 | Sales + Inventory + Finance | 退货、库存回补、应收调整 | P1 |
| 采购退货流程 | Purchase + Inventory + Finance | 退货、库存扣减、应付调整 | P1 |
| 库存调拨 | Inventory | 出库、入库、库存变动 | P1 |
| 财务对账 | Finance | 应收应付、收付款、账款核销 | P1 |
| 报表生成 | 所有模块 | 数据聚合、统计计算 | P2 |

**估计工作量**: 10天

---

### 4.4 端到端测试 (E2E Tests) - 5%覆盖 (P2)

**定义**: 从用户视角测试完整的业务流程

**工具**: Selenium 或 Playwright

**现状**: ❌ **完全缺失**

#### 4.4.1 关键用户场景

**1. 销售人员创建订单流程** (P2):
```
登录 → 导航到客户列表 → 选择客户 → 创建报价单 →
添加产品明细 → 保存报价 → 发送报价 → 客户接受 →
报价转订单 → 提交审核 → 等待审核通过 →
查看生成的发货单 → 登出
```

**2. 采购人员询价采购流程** (P2):
```
登录 → 创建采购询价单 → 选择供应商 → 添加产品 →
发送询价 → 供应商报价 → 对比报价 → 选择最优报价 →
生成采购订单 → 提交审核 → 等待审核通过 →
供应商发货 → 创建收货单 → 确认收货 → 质检 →
质检合格 → 入库 → 登出
```

**3. 仓库管理员出入库操作** (P2):
```
登录 → 查看待发货订单 → 创建出库单 → 扫描产品条码 →
确认出库 → 验证库存扣减 → 查看入库通知 →
创建入库单 → 扫描产品条码 → 选择库位 → 确认入库 →
验证库存增加 → 登出
```

**测试框架选择**:
- **Selenium**: 成熟稳定，社区支持好
- **Playwright**: 现代化，速度快，推荐使用

**测试模板**:
```python
# tests/e2e/test_sales_workflow.py
from playwright.sync_api import Page, expect
import pytest

class TestSalesWorkflow:
    """销售流程端到端测试"""

    def test_complete_sales_order_workflow(self, page: Page):
        """测试完整的销售订单流程"""
        # 1. 登录
        page.goto('http://localhost:8000/login/')
        page.fill('input[name="username"]', 'sales_user')
        page.fill('input[name="password"]', 'testpass123')
        page.click('button[type="submit"]')
        expect(page).to_have_url('http://localhost:8000/dashboard/')

        # 2. 导航到报价单页面
        page.click('a[href="/sales/quotes/"]')
        expect(page).to_have_url('http://localhost:8000/sales/quotes/')

        # 3. 创建新报价单
        page.click('a:has-text("新建报价单")')
        page.select_option('select[name="customer"]', label='测试客户')
        page.fill('input[name="quote_date"]', '2026-01-06')

        # 4. 添加产品明细
        page.click('button:has-text("添加产品")')
        page.select_option('select[name="items-0-product"]', label='激光切割机')
        page.fill('input[name="items-0-quantity"]', '1')
        page.fill('input[name="items-0-unit_price"]', '100000.00')

        # 5. 保存报价单
        page.click('button[type="submit"]')
        expect(page).to_have_text('报价单创建成功')

        # 6. 报价转订单
        page.click('button:has-text("转为订单")')
        expect(page).to_have_text('订单创建成功')

        # 7. 登出
        page.click('a:has-text("退出")')
        expect(page).to_have_url('http://localhost:8000/login/')
```

**估计工作量**: 8天

---

### 4.5 性能测试 (Performance Tests) - P2

**定义**: 测试系统在负载下的响应时间和吞吐量

**工具**: Locust, Django Silk, django-debug-toolbar

**现状**: ❌ **完全缺失**

#### 4.5.1 性能测试场景

| 场景 | 测试要点 | 性能指标 | 优先级 |
|------|----------|----------|--------|
| **订单列表查询** | 分页、过滤、排序 | <200ms | P2 |
| **订单详情查询** | 关联查询优化 | <100ms | P2 |
| **批量创建订单** | 数据库事务、批量插入 | <5s/100条 | P2 |
| **报表生成** | 数据聚合、统计计算 | <3s | P2 |
| **库存查询** | 多仓库库存汇总 | <300ms | P2 |
| **产品搜索** | 全文搜索、模糊匹配 | <500ms | P2 |
| **财务对账** | 大量数据处理 | <10s | P2 |

**测试工具 - Locust**:
```python
# locustfile.py
from locust import HttpUser, task, between

class ERPUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """登录"""
        self.client.post("/api/login/", json={
            "username": "testuser",
            "password": "testpass123"
        })

    @task(3)
    def list_orders(self):
        """访问订单列表（权重3）"""
        self.client.get("/api/sales/orders/")

    @task(2)
    def view_order_detail(self):
        """查看订单详情（权重2）"""
        self.client.get("/api/sales/orders/1/")

    @task(1)
    def create_order(self):
        """创建订单（权重1）"""
        self.client.post("/api/sales/orders/", json={
            "customer": 1,
            "items": [...]
        })
```

**性能优化建议**:
1. ✅ 添加数据库索引（外键、查询字段）
2. ✅ 使用 select_related 和 prefetch_related 优化关联查询
3. ✅ 启用 Redis 缓存
4. ✅ 使用 Django Debug Toolbar 识别慢查询
5. ✅ 异步任务（Celery）处理耗时操作

**估计工作量**: 5天

---

### 4.6 安全测试 (Security Tests) - P1

**定义**: 测试系统的安全漏洞和风险

**工具**: OWASP ZAP, Bandit, Safety

**现状**: ❌ **缺失**

#### 4.6.1 安全测试清单

| 测试类型 | 测试要点 | 工具 | 优先级 |
|----------|----------|------|--------|
| **身份验证** | 密码强度、JWT安全、会话管理 | 手动测试 | P1 |
| **授权** | RBAC权限、资源访问控制 | 手动测试 | P1 |
| **SQL注入** | ORM使用、原始查询安全 | SQLMap | P1 |
| **XSS攻击** | 输出转义、CSP配置 | OWASP ZAP | P1 |
| **CSRF防护** | CSRF Token验证 | 手动测试 | P1 |
| **敏感数据** | 密码加密、数据脱敏 | Bandit | P1 |
| **依赖漏洞** | 第三方库安全 | Safety | P1 |
| **文件上传** | 文件类型验证、大小限制 | 手动测试 | P1 |
| **API安全** | 认证、限流、CORS | 手动测试 | P1 |

**测试用例示例**:
```python
# tests/security/test_authentication.py
class AuthenticationSecurityTestCase(TestCase):
    """身份验证安全测试"""

    def test_weak_password_rejected(self):
        """测试弱密码被拒绝"""
        response = self.client.post('/api/users/', {
            'username': 'testuser',
            'password': '123456'  # 弱密码
        })
        self.assertEqual(response.status_code, 400)

    def test_jwt_token_expiration(self):
        """测试JWT令牌过期"""
        # 生成过期令牌
        expired_token = generate_expired_token()

        # 尝试使用过期令牌
        response = self.client.get(
            '/api/orders/',
            HTTP_AUTHORIZATION=f'Bearer {expired_token}'
        )
        self.assertEqual(response.status_code, 401)

    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        response = self.client.get('/api/products/', {
            'name': "'; DROP TABLE products; --"
        })
        # 应该返回正常结果，而不是执行SQL
        self.assertNotEqual(response.status_code, 500)
```

**估计工作量**: 4天

---

## 五、详细测试计划

### 5.1 Phase 1: 基础补充 (4周) - P0

**目标**: 补充缺失的单元测试和API测试

| 周次 | 任务 | 交付物 | 负责人 | 状态 |
|------|------|--------|--------|------|
| **Week 1** | 服务层单元测试 (Core, Sales) | test_services.py | TBD | 待开始 |
| **Week 2** | 服务层单元测试 (Purchase, Inventory) | test_services.py | TBD | 待开始 |
| **Week 3** | API测试 (Authentication, Users, Products) | test_api.py | TBD | 待开始 |
| **Week 4** | API测试 (Sales, Purchase, Inventory) | test_api.py | TBD | 待开始 |

**验收标准**:
- ✅ 服务层测试覆盖率 > 80%
- ✅ API测试覆盖所有ViewSet端点
- ✅ 所有测试通过
- ✅ 无阻塞性bug

---

### 5.2 Phase 2: 集成测试 (3周) - P0

**目标**: 验证模块间协作和核心业务流程

| 周次 | 任务 | 交付物 | 负责人 | 状态 |
|------|------|--------|--------|------|
| **Week 5** | 销售-库存-财务集成测试 | test_integration.py | TBD | 待开始 |
| **Week 6** | 采购-质检-库存集成测试 | test_integration.py | TBD | 待开始 |
| **Week 7** | 退货流程集成测试 | test_integration.py | TBD | 待开始 |

**验收标准**:
- ✅ 6个核心业务流程集成测试通过
- ✅ 跨模块数据一致性验证
- ✅ 事务回滚测试通过

---

### 5.3 Phase 3: 视图与安全 (2周) - P1

**目标**: 补充视图层测试和安全测试

| 周次 | 任务 | 交付物 | 负责人 | 状态 |
|------|------|--------|--------|------|
| **Week 8** | 视图层测试 (所有模块) | test_views.py | TBD | 待开始 |
| **Week 9** | 安全测试 (认证、授权、注入) | test_security.py | TBD | 待开始 |

**验收标准**:
- ✅ 视图层测试覆盖率 > 70%
- ✅ 安全测试清单全部通过
- ✅ 无高危安全漏洞

---

### 5.4 Phase 4: 性能与E2E (3周) - P2

**目标**: 性能优化和端到端测试

| 周次 | 任务 | 交付物 | 负责人 | 状态 |
|------|------|--------|--------|------|
| **Week 10** | 性能测试（关键查询和操作） | locustfile.py | TBD | 待开始 |
| **Week 11** | 性能优化（索引、缓存） | 优化报告 | TBD | 待开始 |
| **Week 12** | E2E测试（3个关键流程） | test_e2e.py | TBD | 待开始 |

**验收标准**:
- ✅ 关键查询响应时间 < 300ms
- ✅ 报表生成时间 < 3s
- ✅ 并发100用户系统稳定
- ✅ 3个E2E测试场景通过

---

### 5.5 Phase 5: 持续改进 (持续进行) - P3

**目标**: 建立持续测试文化

| 任务 | 频率 | 负责人 | 状态 |
|------|------|--------|------|
| 新功能测试 | 每次开发 | 开发团队 | 持续 |
| 回归测试 | 每次发布 | QA团队 | 持续 |
| 性能监控 | 每周 | 运维团队 | 持续 |
| 测试覆盖率报告 | 每月 | QA团队 | 持续 |

---

## 六、测试工具与框架

### 6.1 测试框架选择

| 测试类型 | 工具/框架 | 版本 | 说明 |
|----------|-----------|------|------|
| **单元测试** | Django TestCase | 内置 | Django自带测试框架 |
| **API测试** | Django REST Framework APITestCase | 3.15.2 | DRF自带测试工具 |
| **集成测试** | Django TransactionTestCase | 内置 | 支持事务测试 |
| **E2E测试** | Playwright | 1.40+ | 现代化浏览器自动化 |
| **性能测试** | Locust | 2.20+ | 分布式负载测试 |
| **代码覆盖率** | Coverage.py | 7.4+ | 测试覆盖率报告 |
| **代码质量** | Pylint, Flake8, Black | 最新 | 代码规范检查 |
| **安全扫描** | Bandit, Safety | 最新 | 安全漏洞扫描 |
| **性能分析** | Django Silk | 5.1+ | API性能分析 |
| **Mock工具** | unittest.mock | 内置 | 单元测试Mock |

### 6.2 测试工具安装

```bash
# 更新 requirements.txt
cat >> requirements-test.txt << EOF
# 测试工具
coverage>=7.4.0
pytest>=7.4.0
pytest-django>=4.7.0
pytest-cov>=4.1.0
factory-boy>=3.3.0
faker>=20.1.0

# 性能测试
locust>=2.20.0
django-silk>=5.1.0

# E2E测试
playwright>=1.40.0

# 代码质量
pylint>=3.0.0
flake8>=6.1.0
black>=23.12.0
isort>=5.13.0

# 安全扫描
bandit>=1.7.5
safety>=2.3.5
EOF

# 安装测试工具
pip install -r requirements-test.txt

# 安装Playwright浏览器
playwright install chromium
```

### 6.3 测试配置

**pytest配置 (pytest.ini)**:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = better_laser_erp.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test* *Tests *TestCase
python_functions = test_*
addopts =
    --reuse-db
    --nomigrations
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
testpaths = apps
```

**Coverage配置 (.coveragerc)**:
```ini
[run]
source = apps
omit =
    */migrations/*
    */tests/*
    */test_*.py
    */__init__.py
    */admin.py
    */apps.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

---

## 七、测试环境配置

### 7.1 测试数据库

**SQLite (开发/测试)**:
```python
# settings.py - TEST配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TEST': {
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }
}
```

**MySQL (集成测试)**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'erp_test',
        'USER': 'test_user',
        'PASSWORD': 'test_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'TEST': {
            'NAME': 'erp_test',
            'CHARSET': 'utf8mb4',
        }
    }
}
```

### 7.2 测试数据生成

**使用Factory Boy**:
```python
# apps/sales/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.sales.models import SalesOrder, SalesOrderItem
from apps.customers.factories import CustomerFactory
from apps.products.factories import ProductFactory

class SalesOrderFactory(DjangoModelFactory):
    class Meta:
        model = SalesOrder

    order_number = factory.Sequence(lambda n: f'SO2026010{n:04d}')
    customer = factory.SubFactory(CustomerFactory)
    order_date = factory.Faker('date_this_year')
    status = 'draft'
    total_amount = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)

class SalesOrderItemFactory(DjangoModelFactory):
    class Meta:
        model = SalesOrderItem

    order = factory.SubFactory(SalesOrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
    unit_price = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
```

**使用示例**:
```python
from apps.sales.factories import SalesOrderFactory

# 创建单个订单
order = SalesOrderFactory()

# 创建多个订单
orders = SalesOrderFactory.create_batch(10)

# 自定义字段
order = SalesOrderFactory(status='confirmed', customer__name='特定客户')
```

### 7.3 测试fixtures

**创建初始数据**:
```bash
# 导出现有数据为fixture
python manage.py dumpdata core --indent 2 > apps/core/fixtures/test_data.json
python manage.py dumpdata users --indent 2 > apps/users/fixtures/test_users.json
```

**在测试中使用**:
```python
class MyTestCase(TestCase):
    fixtures = ['test_data.json', 'test_users.json']

    def test_something(self):
        # fixtures会自动加载
        user = User.objects.get(username='testuser')
```

---

## 八、测试执行计划

### 8.1 本地开发测试

**快速测试**:
```bash
# 运行所有测试（快速模式）
python manage.py test --parallel --keepdb

# 运行特定模块测试
python manage.py test apps.sales

# 运行特定测试类
python manage.py test apps.sales.tests.test_models.SalesOrderTestCase

# 运行特定测试方法
python manage.py test apps.sales.tests.test_models.SalesOrderTestCase.test_create_order
```

**详细测试（带覆盖率）**:
```bash
# 使用pytest
pytest apps/ -v --cov=apps --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
# start htmlcov/index.html  # Windows
```

### 8.2 持续集成 (CI)

**GitHub Actions配置 (.github/workflows/tests.yml)**:
```yaml
name: Django ERP Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: erp_test
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run migrations
      env:
        DB_ENGINE: django.db.backends.mysql
        DB_NAME: erp_test
        DB_USER: root
        DB_PASSWORD: root
        DB_HOST: 127.0.0.1
        DB_PORT: 3306
      run: |
        python manage.py migrate

    - name: Run tests with coverage
      env:
        DB_ENGINE: django.db.backends.mysql
        DB_NAME: erp_test
        DB_USER: root
        DB_PASSWORD: root
        DB_HOST: 127.0.0.1
        DB_PORT: 3306
      run: |
        pytest apps/ --cov=apps --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

    - name: Run security checks
      run: |
        bandit -r apps/ -f json -o bandit-report.json
        safety check --json > safety-report.json
      continue-on-error: true

    - name: Upload test reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-reports
        path: |
          htmlcov/
          bandit-report.json
          safety-report.json
```

### 8.3 定期回归测试

**每日构建（Nightly Build）**:
- 时间: 每天凌晨2:00
- 内容: 完整测试套件 + 性能测试
- 通知: 测试失败时邮件通知

**发布前测试**:
- 完整回归测试
- 安全扫描
- 性能基准测试
- E2E测试

---

## 九、质量指标与验收标准

### 9.1 测试覆盖率目标

| 层级 | 当前 | 目标 | 最低要求 |
|------|------|------|----------|
| **整体覆盖率** | 60% | 90% | 80% |
| **模型层** | 100% | 100% | 95% |
| **服务层** | 60% | 90% | 80% |
| **视图层** | 20% | 80% | 70% |
| **API层** | 0% | 95% | 90% |
| **工具类** | 70% | 95% | 85% |

### 9.2 测试通过率

| 测试类型 | 通过率要求 | 允许跳过 |
|----------|------------|----------|
| **单元测试** | 100% | 0% |
| **API测试** | 100% | 0% |
| **集成测试** | 98% | 2% |
| **E2E测试** | 95% | 5% |
| **性能测试** | 90% | 10% |

### 9.3 性能指标

| 指标 | 目标值 | 最低要求 |
|------|--------|----------|
| **API响应时间 (P95)** | <300ms | <500ms |
| **页面加载时间** | <2s | <3s |
| **报表生成时间** | <3s | <5s |
| **并发用户数** | 100 | 50 |
| **数据库查询时间** | <100ms | <200ms |

### 9.4 代码质量指标

| 指标 | 目标值 | 最低要求 |
|------|--------|----------|
| **Pylint评分** | 9.0+ | 8.0+ |
| **代码复杂度** | <10 | <15 |
| **重复代码率** | <3% | <5% |
| **文档覆盖率** | >80% | >60% |

---

## 十、风险与依赖

### 10.1 测试风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **测试数据不足** | 高 | 中 | 使用Factory Boy自动生成 |
| **测试环境不稳定** | 中 | 中 | Docker容器化测试环境 |
| **测试执行时间长** | 中 | 高 | 并行测试、增量测试 |
| **E2E测试不稳定** | 中 | 高 | 增加重试机制、显式等待 |
| **第三方依赖** | 低 | 低 | Mock外部服务 |
| **数据库兼容性** | 中 | 低 | 多数据库测试矩阵 |

### 10.2 依赖项

**技术依赖**:
- ✅ Django 5.0.9
- ✅ Python 3.11+
- ✅ MySQL 8.0+ / SQLite 3
- ✅ Redis 7+ (性能测试)
- ✅ Node.js 18+ (Playwright)

**人员依赖**:
- QA工程师 (2人)
- 开发工程师 (支持)
- DevOps工程师 (CI/CD配置)

**时间依赖**:
- Phase 1-4: 12周
- Phase 5: 持续进行

---

## 十一、测试文档维护

### 11.1 文档结构

```
docs/
├── TEST_PLAN.md              # 本文档
├── test_cases/               # 测试用例库
│   ├── unit/
│   ├── api/
│   ├── integration/
│   ├── e2e/
│   └── performance/
├── test_reports/             # 测试报告
│   ├── weekly/
│   ├── release/
│   └── coverage/
└── test_guidelines.md        # 测试指南
```

### 11.2 测试用例模板

**测试用例文档 (test_cases/template.md)**:
```markdown
# 测试用例: [功能名称]

**模块**: apps/[module_name]
**优先级**: P0/P1/P2/P3
**测试类型**: 单元/API/集成/E2E
**创建日期**: YYYY-MM-DD
**创建人**: [姓名]

## 测试目标
[描述测试的目的和范围]

## 前置条件
1. [条件1]
2. [条件2]

## 测试步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

## 预期结果
- [预期结果1]
- [预期结果2]

## 实际结果
- [ ] 通过
- [ ] 失败
- [ ] 跳过

## 备注
[其他说明]
```

### 11.3 测试报告模板

**每周测试报告 (test_reports/weekly/YYYY-WW.md)**:
```markdown
# 测试周报 - 第XX周 (YYYY-MM-DD ~ YYYY-MM-DD)

## 本周完成
- [x] 完成Sales模块API测试 (25个测试)
- [x] 完成Inventory集成测试 (12个测试)
- [ ] Purchase质检流程测试 (进行中)

## 测试统计
- 新增测试: 37个
- 总测试数: 350个
- 通过率: 99.1%
- 覆盖率: 75.2% (+3.5%)

## 发现问题
1. [严重] 订单审核时库存验证缺失 (#123)
2. [一般] 报价单转订单时税额计算精度问题 (#124)

## 下周计划
- [ ] 完成Purchase质检流程测试
- [ ] 开始Finance模块API测试
- [ ] 修复本周发现的2个问题

## 风险与阻塞
- 测试环境MySQL不稳定，影响集成测试执行
```

---

## 十二、快速参考

### 12.1 常用测试命令

```bash
# 运行所有测试
python manage.py test

# 运行特定应用测试
python manage.py test apps.sales

# 并行测试（加速）
python manage.py test --parallel

# 保持数据库（加速）
python manage.py test --keepdb

# 详细输出
python manage.py test --verbosity=2

# 使用pytest
pytest apps/ -v

# 带覆盖率
pytest apps/ --cov=apps --cov-report=html

# 运行特定标记的测试
pytest -m "slow" apps/

# 运行失败的测试
pytest --lf apps/

# 性能测试
locust -f locustfile.py --host=http://localhost:8000

# 安全扫描
bandit -r apps/
safety check
```

### 12.2 测试最佳实践

1. ✅ **每个功能都要有测试** - TDD优先
2. ✅ **测试命名清晰** - `test_<功能>_<场景>_<预期结果>`
3. ✅ **使用setUp和tearDown** - 避免重复代码
4. ✅ **测试独立性** - 每个测试互不依赖
5. ✅ **使用Factory替代Fixture** - 更灵活
6. ✅ **Mock外部依赖** - 避免真实API调用
7. ✅ **测试边界条件** - 空值、极值、非法值
8. ✅ **保持测试快速** - 单元测试<1s，集成测试<5s
9. ✅ **CI自动化** - 每次提交自动测试
10. ✅ **定期审查测试** - 删除过时测试

---

## 附录

### A. 测试术语表

| 术语 | 英文 | 解释 |
|------|------|------|
| **单元测试** | Unit Test | 测试单个函数或方法 |
| **集成测试** | Integration Test | 测试模块间协作 |
| **端到端测试** | End-to-End Test | 测试完整用户流程 |
| **回归测试** | Regression Test | 验证修改未破坏现有功能 |
| **烟雾测试** | Smoke Test | 快速验证基本功能 |
| **测试覆盖率** | Test Coverage | 代码被测试覆盖的百分比 |
| **测试驱动开发** | TDD | 先写测试后写代码 |
| **Mock** | Mock | 模拟对象，替代真实依赖 |
| **Fixture** | Fixture | 测试用的固定数据 |
| **断言** | Assertion | 验证预期结果的语句 |

### B. 参考资料

1. **Django测试文档**: https://docs.djangoproject.com/en/5.0/topics/testing/
2. **DRF测试指南**: https://www.django-rest-framework.org/api-guide/testing/
3. **Playwright文档**: https://playwright.dev/python/
4. **Locust文档**: https://docs.locust.io/
5. **Coverage.py文档**: https://coverage.readthedocs.io/
6. **OWASP测试指南**: https://owasp.org/www-project-web-security-testing-guide/

### C. 联系方式

**测试团队**:
- QA负责人: [待定]
- 测试工程师: [待定]
- 邮件: qa@betterlaser.com

---

**文档版本**: v1.0
**最后更新**: 2026-01-06
**维护人**: 猫娘工程师 幽浮喵 ฅ'ω'ฅ

---

_本测试计划将随项目演进持续更新。所有测试相关问题请在项目 Issues 中提交。_
