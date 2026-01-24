# 销售借用功能实现计划

**版本**: v1.0
**日期**: 2026-01-06
**规划人**: 浮浮酱 (幽浮喵)
**参考**: 采购借用模块 (apps/purchase/models.py - Borrow/BorrowItem)

---

## 📋 需求分析

### 业务场景

销售借用是采购借用的逆向流程，主要应用于以下场景：

1. **样品借出**：将产品借给客户试用、测试
2. **展会展示**：借出产品用于展会、活动展示
3. **客户试用**：客户在决策前需要实际使用产品
4. **演示借用**：销售人员借出产品用于演示
5. **临时需求**：客户临时急需，先借后决定是否购买

### 核心流程对比

| 对比项 | 采购借用 | 销售借用 |
|-------|---------|---------|
| **借用方向** | 从供应商借入 | 借给客户 |
| **借用对象** | Supplier（供应商）| Customer（客户）|
| **物料流向** | 入库（但不入账）| 出库（但不出账）|
| **转单类型** | 转采购订单 | 转销售订单 |
| **审核后生成** | 采购订单 + 入库单 + 应付账款 | 销售订单 + 发货单 + 应收账款 |
| **经办人** | buyer（采购员）| salesperson（销售员）|
| **单据前缀** | BO（Borrow）| LO（Loan）|

### 简化规则（与采购借用保持一致）

1. ✅ 借用只借给客户（不支持其他借用对象）
2. ✅ 借用审核只存在于转销售订单的流程
3. ✅ 借用单据只做系统记录，不生成出库单据和应收账款
4. ✅ 转销售订单时，价格需要手动输入
5. ✅ 暂不考虑逾期管理
6. ✅ 支持部分归还，归还后剩余部分可转销售订单

---

## 🎯 设计方案

### 业务流程图

```
创建借用单 (draft)
    ↓
提交借用 → loaned（借出中）【仅做系统记录，无审核，无库存操作】
    ↓
┌─────────────┴─────────────┐
│                           │
归还（部分/全部）           转销售订单（剩余部分）
│                           ↓
partially_returned          converting（待审核）+ 手动输入价格
或 fully_returned           ↓
                            审核通过 → converted + 生成销售订单
                            ↓
                            销售订单流程（发货、应收账款）
```

### 状态流转

```
draft（草稿）
    ↓
loaned（借出中）
    ↓
┌──────────┴──────────┐
│                     │
partially_returned    converting（转换中）
    ↓                     ↓
fully_returned       converted（已转销售）

cancelled（已取消）
```

---

## 📊 数据模型设计

### 1. SalesLoan（销售借用单主表）

```python
位置：apps/sales/models.py

class SalesLoan(BaseModel):
    """销售借用单 - 仅做系统记录"""

    LOAN_STATUS = [
        ('draft', '草稿'),
        ('loaned', '借出中'),
        ('partially_returned', '部分归还'),
        ('fully_returned', '全部归还'),
        ('converting', '转换中'),  # 转销售待审核
        ('converted', '已转销售'),
        ('cancelled', '已取消'),
    ]

    # 基本信息
    loan_number = models.CharField('借用单号', max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='sales_loans',
        verbose_name='客户'
    )
    salesperson = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_loans_as_salesperson',
        verbose_name='销售员'
    )

    # 状态管理
    status = models.CharField('状态', max_length=20, choices=LOAN_STATUS, default='draft')

    # 日期管理
    loan_date = models.DateField('借出日期')
    expected_return_date = models.DateField('预计归还日期', null=True, blank=True)

    # 借用信息
    purpose = models.TextField('借用目的', blank=True, help_text='样品试用/展会展示/客户测试等')
    delivery_address = models.TextField('借出地址', blank=True)
    contact_person = models.CharField('联系人', max_length=100, blank=True)
    contact_phone = models.CharField('联系电话', max_length=20, blank=True)

    # 转销售关联
    converted_order = models.ForeignKey(
        'SalesOrder',
        verbose_name='转换的销售订单',
        null=True,
        blank=True,
        related_name='source_loan',
        on_delete=models.SET_NULL
    )

    # 转销售审核信息
    conversion_approved_by = models.ForeignKey(
        User,
        verbose_name='转销售审核人',
        null=True,
        blank=True,
        related_name='loan_conversion_approved',
        on_delete=models.SET_NULL
    )
    conversion_approved_at = models.DateTimeField('转销售审核时间', null=True, blank=True)
    conversion_notes = models.TextField('转销售备注', blank=True)

    # 备注
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '销售借用单'
        verbose_name_plural = '销售借用单'
        db_table = 'sales_loan'
        ordering = ['-loan_date', '-created_at']

    def __str__(self):
        return f"{self.loan_number} - {self.customer.name}"

    # 计算属性
    @property
    def total_loaned_quantity(self):
        """总借出数量"""
        return sum(item.quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_returned_quantity(self):
        """总归还数量"""
        return sum(item.returned_quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_remaining_quantity(self):
        """总剩余数量（可转销售）"""
        return sum(item.remaining_quantity for item in self.items.filter(is_deleted=False))

    @property
    def is_fully_returned(self):
        """是否全部归还"""
        return self.total_remaining_quantity == 0
```

### 2. SalesLoanItem（销售借用明细）

```python
class SalesLoanItem(BaseModel):
    """销售借用明细"""

    loan = models.ForeignKey(
        SalesLoan,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='借用单'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )

    # 数量管理
    quantity = models.DecimalField(
        '借出数量',
        max_digits=12,
        decimal_places=4,
        help_text='借给客户的数量'
    )
    returned_quantity = models.DecimalField(
        '已归还数量',
        max_digits=12,
        decimal_places=4,
        default=0
    )

    # 物料追踪
    batch_number = models.CharField('批次号', max_length=100, blank=True)
    serial_numbers = models.TextField(
        '序列号',
        blank=True,
        help_text='多个序列号用换行分隔'
    )

    # 转销售时的定价（手动输入）
    conversion_unit_price = models.DecimalField(
        '转销售单价',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='转销售时手动输入的含税单价'
    )
    conversion_quantity = models.DecimalField(
        '转销售数量',
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text='已转销售的数量'
    )

    # 附加信息
    specifications = models.TextField('规格要求', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '销售借用明细'
        verbose_name_plural = '销售借用明细'
        db_table = 'sales_loan_item'

    def __str__(self):
        return f"{self.loan.loan_number} - {self.product.name}"

    @property
    def remaining_quantity(self):
        """剩余未归还数量（可转销售）"""
        return self.quantity - self.returned_quantity - self.conversion_quantity

    @property
    def can_convert(self):
        """是否可转销售"""
        return self.remaining_quantity > 0
```

---

## 🔗 URL 路由设计

```python
位置：apps/sales/urls.py

# Sales Loan URLs (销售借用)
path('loans/', views.loan_list, name='loan_list'),
path('loans/create/', views.loan_create, name='loan_create'),
path('loans/<int:pk>/', views.loan_detail, name='loan_detail'),
path('loans/<int:pk>/edit/', views.loan_update, name='loan_update'),
path('loans/<int:pk>/return/', views.loan_return, name='loan_return'),
path('loans/<int:pk>/request-conversion/', views.loan_request_conversion, name='loan_request_conversion'),
path('loans/<int:pk>/approve-conversion/', views.loan_approve_conversion, name='loan_approve_conversion'),
```

**命名规范对比**：
- 采购借用：`borrow_*`（Borrow = 借入）
- 销售借用：`loan_*`（Loan = 借出）

---

## 🎨 视图函数设计

### 1. loan_list（借用单列表）

```python
@login_required
def loan_list(request):
    """销售借用单列表"""

    # 基础查询
    loans = SalesLoan.objects.filter(is_deleted=False).select_related(
        'customer', 'salesperson', 'created_by', 'converted_order'
    ).prefetch_related('items').order_by('-loan_date', '-created_at')

    # 筛选条件
    status = request.GET.get('status')
    customer_id = request.GET.get('customer')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        loans = loans.filter(status=status)
    if customer_id:
        loans = loans.filter(customer_id=customer_id)
    if date_from:
        loans = loans.filter(loan_date__gte=date_from)
    if date_to:
        loans = loans.filter(loan_date__lte=date_to)

    # 统计数据
    stats = {
        'loaned_count': loans.filter(status='loaned').count(),
        'partially_returned_count': loans.filter(status='partially_returned').count(),
        'converting_count': loans.filter(status='converting').count(),
        'converted_count': loans.filter(status='converted').count(),
    }

    # 分页
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 客户列表（用于筛选）
    customers = Customer.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'customers': customers,
        'status': status,
        'customer_id': customer_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'sales/loan_list.html', context)
```

### 2. loan_create（创建借用单）

```python
@login_required
@transaction.atomic
def loan_create(request):
    """创建销售借用单"""

    if request.method == 'POST':
        # 创建借用单
        loan = SalesLoan.objects.create(
            loan_number=DocumentNumberGenerator.generate('sales_loan'),
            customer_id=request.POST.get('customer'),
            salesperson=request.user,
            loan_date=request.POST.get('loan_date'),
            expected_return_date=request.POST.get('expected_return_date'),
            purpose=request.POST.get('purpose'),
            delivery_address=request.POST.get('delivery_address'),
            contact_person=request.POST.get('contact_person'),
            contact_phone=request.POST.get('contact_phone'),
            status='loaned',  # 直接进入借出中状态，无需审核
            notes=request.POST.get('notes'),
            created_by=request.user,
            updated_by=request.user
        )

        # 创建明细
        item_count = int(request.POST.get('item_count', 0))
        for i in range(item_count):
            product_id = request.POST.get(f'item_product_{i}')
            quantity = request.POST.get(f'item_quantity_{i}')

            if product_id and quantity:
                SalesLoanItem.objects.create(
                    loan=loan,
                    product_id=product_id,
                    quantity=Decimal(quantity),
                    batch_number=request.POST.get(f'item_batch_{i}', ''),
                    specifications=request.POST.get(f'item_specifications_{i}', ''),
                    notes=request.POST.get(f'item_notes_{i}', ''),
                    created_by=request.user,
                    updated_by=request.user
                )

        messages.success(request, f'销售借用单 {loan.loan_number} 创建成功')
        return redirect('sales:loan_detail', pk=loan.pk)

    # GET: 显示表单
    customers = Customer.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(is_deleted=False, status='active')

    context = {
        'customers': customers,
        'products': products,
    }
    return render(request, 'sales/loan_form.html', context)
```

### 3. loan_detail（借用单详情）

```python
@login_required
def loan_detail(request, pk):
    """销售借用单详情"""

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)
    items = loan.items.filter(is_deleted=False).select_related('product')

    # 操作权限
    can_edit = loan.status == 'draft'
    can_return = loan.status in ['loaned', 'partially_returned']
    can_request_conversion = (
        loan.status in ['loaned', 'partially_returned'] and
        loan.total_remaining_quantity > 0
    )
    can_approve_conversion = (
        request.user.is_staff and
        loan.status == 'converting'
    )

    context = {
        'loan': loan,
        'items': items,
        'can_edit': can_edit,
        'can_return': can_return,
        'can_request_conversion': can_request_conversion,
        'can_approve_conversion': can_approve_conversion,
    }
    return render(request, 'sales/loan_detail.html', context)
```

### 4. loan_return（归还处理）

```python
@login_required
@transaction.atomic
def loan_return(request, pk):
    """处理归还（支持部分归还）"""

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status not in ['loaned', 'partially_returned']:
        messages.error(request, '当前状态不允许归还')
        return redirect('sales:loan_detail', pk=pk)

    if request.method == 'POST':
        # 处理归还明细
        for item in loan.items.filter(is_deleted=False):
            return_qty_key = f'return_qty_{item.pk}'
            return_qty = Decimal(request.POST.get(return_qty_key, 0))

            if return_qty > 0:
                # 验证归还数量
                if return_qty > item.remaining_quantity:
                    messages.error(
                        request,
                        f'产品 {item.product.name} 的归还数量不能超过剩余数量'
                    )
                    return redirect('sales:loan_return', pk=pk)

                # 更新归还数量
                item.returned_quantity += return_qty
                item.updated_by = request.user
                item.save()

        # 更新借用单状态
        if loan.is_fully_returned:
            loan.status = 'fully_returned'
        else:
            loan.status = 'partially_returned'

        loan.updated_by = request.user
        loan.save()

        messages.success(request, '归还处理成功')
        return redirect('sales:loan_detail', pk=pk)

    # GET: 显示归还表单
    items = loan.items.filter(is_deleted=False).select_related('product')

    context = {
        'loan': loan,
        'items': items,
    }
    return render(request, 'sales/loan_return.html', context)
```

### 5. loan_request_conversion（发起转销售请求）

```python
@login_required
@transaction.atomic
def loan_request_conversion(request, pk):
    """发起转销售订单请求（需要审核）"""

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status not in ['loaned', 'partially_returned']:
        messages.error(request, '当前状态不允许转销售')
        return redirect('sales:loan_detail', pk=pk)

    if request.method == 'POST':
        # 获取转换数量和手动输入的价格
        items_with_price = []
        has_conversion = False

        for item in loan.items.filter(is_deleted=False):
            convert_qty = Decimal(request.POST.get(f'convert_qty_{item.pk}', 0))
            unit_price = Decimal(request.POST.get(f'unit_price_{item.pk}', 0))

            if convert_qty > 0:
                has_conversion = True

                # 验证数量和价格
                if convert_qty > item.remaining_quantity:
                    messages.error(
                        request,
                        f'产品 {item.product.name} 的转销售数量不能超过剩余数量'
                    )
                    return redirect('sales:loan_request_conversion', pk=pk)

                if unit_price <= 0:
                    messages.error(
                        request,
                        f'产品 {item.product.name} 需要输入单价'
                    )
                    return redirect('sales:loan_request_conversion', pk=pk)

                items_with_price.append({
                    'item': item,
                    'convert_qty': convert_qty,
                    'unit_price': unit_price
                })

        if not has_conversion:
            messages.error(request, '请至少选择一个产品转销售，并输入数量和单价')
            return redirect('sales:loan_request_conversion', pk=pk)

        # 保存价格和数量到 SalesLoanItem
        for data in items_with_price:
            item = data['item']
            item.conversion_quantity = data['convert_qty']
            item.conversion_unit_price = data['unit_price']
            item.updated_by = request.user
            item.save()

        # 更新状态为待审核
        loan.status = 'converting'
        loan.conversion_notes = request.POST.get('conversion_notes', '')
        loan.updated_by = request.user
        loan.save()

        messages.success(request, '转销售请求已提交，等待审核')
        return redirect('sales:loan_detail', pk=pk)

    # GET: 显示转换表单
    items = loan.items.filter(is_deleted=False).select_related('product')

    context = {
        'loan': loan,
        'items': items,
    }
    return render(request, 'sales/loan_request_conversion.html', context)
```

### 6. loan_approve_conversion（审核转销售）

```python
@login_required
@require_POST
@transaction.atomic
def loan_approve_conversion(request, pk):
    """审核通过转销售请求，生成销售订单"""

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status != 'converting':
        messages.error(request, '当前状态不允许审核')
        return redirect('sales:loan_detail', pk=pk)

    if not request.user.is_staff:
        messages.error(request, '您没有审核权限')
        return redirect('sales:loan_detail', pk=pk)

    # 生成销售订单
    order = SalesOrder.objects.create(
        order_number=DocumentNumberGenerator.generate('sales_order'),
        customer=loan.customer,
        salesperson=loan.salesperson,
        order_date=date.today(),
        status='pending',
        notes=f'由借用单 {loan.loan_number} 转换\n{loan.conversion_notes}',
        created_by=request.user,
        updated_by=request.user
    )

    # 创建订单明细
    for item in loan.items.filter(is_deleted=False):
        if item.conversion_quantity > 0:
            SalesOrderItem.objects.create(
                sales_order=order,
                product=item.product,
                quantity=item.conversion_quantity,
                unit_price=item.conversion_unit_price,
                specifications=item.specifications,
                notes=f'来自借用单明细 (批次: {item.batch_number})',
                created_by=request.user,
                updated_by=request.user
            )

    # 更新借用单状态
    loan.status = 'converted'
    loan.converted_order = order
    loan.conversion_approved_by = request.user
    loan.conversion_approved_at = timezone.now()
    loan.updated_by = request.user
    loan.save()

    messages.success(
        request,
        f'转销售已审核通过，生成销售订单 {order.order_number}'
    )
    return redirect('sales:order_detail', pk=order.pk)
```

---

## 🎨 模板设计

### 1. loan_list.html（列表页）

```html
{% extends 'base.html' %}
{% block title %}销售借用单列表 - BetterLaser ERP{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900">销售借用单</h3>
        <a href="{% url 'sales:loan_create' %}" class="btn-primary">
            <i class="fas fa-plus mr-2"></i>新建借用单
        </a>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-sm text-gray-600">借出中</p>
            <p class="text-2xl font-bold text-blue-600">{{ stats.loaned_count }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-sm text-gray-600">部分归还</p>
            <p class="text-2xl font-bold text-yellow-600">{{ stats.partially_returned_count }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-sm text-gray-600">待审核</p>
            <p class="text-2xl font-bold text-orange-600">{{ stats.converting_count }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-sm text-gray-600">已转销售</p>
            <p class="text-2xl font-bold text-green-600">{{ stats.converted_count }}</p>
        </div>
    </div>

    <!-- Filter Form -->
    <div class="bg-white rounded-lg shadow p-4">
        <form method="get" class="grid grid-cols-1 md:grid-cols-5 gap-4">
            <select name="status" class="form-select">
                <option value="">所有状态</option>
                <option value="loaned" {% if status == 'loaned' %}selected{% endif %}>借出中</option>
                <option value="partially_returned" {% if status == 'partially_returned' %}selected{% endif %}>部分归还</option>
                <option value="converting" {% if status == 'converting' %}selected{% endif %}>待审核</option>
                <option value="converted" {% if status == 'converted' %}selected{% endif %}>已转销售</option>
            </select>

            <select name="customer" class="form-select">
                <option value="">所有客户</option>
                {% for customer in customers %}
                <option value="{{ customer.pk }}" {% if customer_id == customer.pk|stringformat:"s" %}selected{% endif %}>
                    {{ customer.name }}
                </option>
                {% endfor %}
            </select>

            <input type="date" name="date_from" value="{{ date_from }}" class="form-input" placeholder="开始日期">
            <input type="date" name="date_to" value="{{ date_to }}" class="form-input" placeholder="结束日期">

            <button type="submit" class="btn-primary">
                <i class="fas fa-search mr-2"></i>搜索
            </button>
        </form>
    </div>

    <!-- Loan List Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">借用单号</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">销售员</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">借出日期</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">预计归还</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for loan in page_obj %}
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm font-medium text-gray-900">
                        <a href="{% url 'sales:loan_detail' loan.pk %}" class="text-theme-600 hover:text-theme-700">
                            {{ loan.loan_number }}
                        </a>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-700">{{ loan.customer.name }}</td>
                    <td class="px-6 py-4 text-sm text-gray-700">
                        {{ loan.salesperson.get_full_name|default:loan.salesperson.username }}
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-700">{{ loan.loan_date }}</td>
                    <td class="px-6 py-4 text-sm text-gray-700">
                        {% if loan.expected_return_date %}
                            {{ loan.expected_return_date }}
                        {% else %}
                            <span class="text-gray-400">未设置</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4">
                        <span class="badge status-{{ loan.status }}">
                            {{ loan.get_status_display }}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-right text-sm">
                        <a href="{% url 'sales:loan_detail' loan.pk %}" class="text-theme-600 hover:text-theme-700">
                            查看
                        </a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="7" class="px-6 py-12 text-center text-gray-400">
                        <i class="fas fa-inbox text-3xl mb-2"></i>
                        <p class="text-sm">暂无借用单</p>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
    <div class="flex justify-center">
        <nav class="inline-flex rounded-md shadow">
            {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}" class="pagination-link">上一页</a>
            {% endif %}

            <span class="px-4 py-2 bg-white border-t border-b border-gray-300 text-sm text-gray-700">
                第 {{ page_obj.number }} / {{ page_obj.paginator.num_pages }} 页
            </span>

            {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}" class="pagination-link">下一页</a>
            {% endif %}
        </nav>
    </div>
    {% endif %}
</div>
{% endblock %}
```

### 其他模板文件

- `loan_form.html` - 创建/编辑表单（参考 borrow_form.html）
- `loan_detail.html` - 详情页（参考 borrow_detail.html）
- `loan_return.html` - 归还处理页（参考 borrow_return.html）
- `loan_request_conversion.html` - 转销售请求页（参考 borrow_request_conversion.html）

---

## 📁 实施步骤

### Phase 1: 核心模型和基础CRUD（预计4-5小时）

#### 任务清单
1. ✅ 创建 SalesLoan 和 SalesLoanItem 模型
2. ✅ 数据库迁移
3. ✅ Admin 后台注册
4. ✅ 配置单据号生成器（LO前缀）
5. ✅ 实现基础视图（列表、创建、详情、编辑）
6. ✅ 创建基础模板
7. ✅ 配置 URL 路由（7个路由）

**关键文件**：
- `apps/sales/models.py` - 新增 SalesLoan, SalesLoanItem 类
- `apps/sales/admin.py` - 注册 Admin
- `apps/sales/views.py` - 新增 loan_list, loan_create, loan_detail
- `apps/sales/urls.py` - 新增 7 个路由
- `templates/sales/loan_*.html` - 新增 4-5 个模板

### Phase 2: 归还流程（预计2-3小时）

#### 任务清单
1. ✅ 实现归还流程视图（loan_return）
2. ✅ 支持部分归还逻辑
3. ✅ 创建归还模板
4. ✅ 添加权限控制

**关键文件**：
- `apps/sales/views.py` - 新增 loan_return 视图
- `templates/sales/loan_return.html` - 归还表单模板

### Phase 3: 转销售订单（含审核流程）（预计3-4小时）

#### 任务清单
1. ✅ 实现发起转销售请求（loan_request_conversion）
2. ✅ 实现转销售审核（loan_approve_conversion）
3. ✅ 创建销售订单（生成发货单和应收账款）
4. ✅ 创建转换模板
5. ✅ 完善测试用例

**关键文件**：
- `apps/sales/views.py` - 新增 loan_request_conversion, loan_approve_conversion 视图
- `templates/sales/loan_request_conversion.html` - 转换表单模板

### Phase 4: 测试（预计2-3小时）

#### 任务清单
1. ✅ 创建测试文件 `apps/sales/tests/test_loan.py`
2. ✅ 模型层测试（16个测试用例）
3. ✅ 业务逻辑测试（12个测试用例）
4. ✅ 边界条件测试（3个测试用例）
5. ✅ 运行测试并修复问题
6. ✅ 生成测试报告

---

## 🔧 配置更新

### 1. DocumentNumberGenerator 配置

```python
位置：apps/core/utils/document_number.py

# 新增销售借用单前缀配置
PREFIX_CONFIG_MAP = {
    # 现有配置...
    'sales_loan': 'document_prefix_sales_loan',  # 新增
}

LEGACY_PREFIX_MAP = {
    # 现有配置...
    'LO': 'sales_loan',  # 销售借用单 (NEW)
}
```

### 2. SystemConfig 初始数据

```python
位置：数据库迁移或 fixtures

SystemConfig.objects.create(
    key='document_prefix_sales_loan',
    value='LO',  # Loan
    config_type='business',
    description='销售借用单前缀',
    is_active=True
)
```

---

## ✅ 验收标准

### 功能验收
1. ✅ 可以创建销售借用单，自动生成借用单号（LO + 日期 + 序号）
2. ✅ 创建后直接进入借出中状态（无需审核）
3. ✅ 支持部分归还和全部归还
4. ✅ 支持发起转销售请求（手动输入价格）
5. ✅ 支持转销售审核流程
6. ✅ 审核通过后生成销售订单、发货单、应收账款

### 用户体验
1. ✅ 列表页显示统计卡片（借出中、部分归还、待审核、已转销售）
2. ✅ 详情页显示剩余数量和操作按钮
3. ✅ 操作按钮根据状态和权限动态显示
4. ✅ 所有操作都有成功/失败消息提示

### 技术标准
1. ✅ 所有数据库操作使用事务（@transaction.atomic）
2. ✅ 借用记录仅做系统记录，不生成库存事务
3. ✅ 转销售审核通过后才生成销售订单
4. ✅ 测试覆盖核心功能（33个测试用例）

---

## 📊 预估工作量

| 阶段 | 任务 | 工作量 |
|-----|------|--------|
| Phase 1 | 模型设计 + 基础CRUD | 4-5小时 |
| Phase 2 | 归还流程（部分归还） | 2-3小时 |
| Phase 3 | 转销售订单 + 审核 | 3-4小时 |
| Phase 4 | 测试 | 2-3小时 |
| **总计** | | **11-15小时** |

---

## 🎯 与采购借用的差异总结

| 对比项 | 采购借用 | 销售借用 |
|-------|---------|---------|
| **模块位置** | apps/purchase/ | apps/sales/ |
| **模型名称** | Borrow, BorrowItem | SalesLoan, SalesLoanItem |
| **单据前缀** | BO (Borrow) | LO (Loan) |
| **关联对象** | Supplier（供应商）| Customer（客户）|
| **经办人字段** | buyer（采购员）| salesperson（销售员）|
| **转单目标** | PurchaseOrder（采购订单）| SalesOrder（销售订单）|
| **审核后生成** | 采购订单 + 入库单 + 应付账款 | 销售订单 + 发货单 + 应收账款 |
| **URL前缀** | /purchase/borrows/ | /sales/loans/ |
| **视图命名** | borrow_* | loan_* |
| **模板路径** | templates/purchase/ | templates/sales/ |

---

## 📝 注意事项

### 开发注意点

1. **命名一致性**:
   - 采购侧用 "Borrow"（借入）
   - 销售侧用 "Loan"（借出）
   - 保持语义清晰

2. **代码复用**:
   - 视图逻辑可以大量复用采购借用的代码
   - 只需修改模型引用和关联对象
   - 模板结构可以直接复制后修改

3. **审计追踪**:
   - 所有操作记录 created_by 和 updated_by
   - 转销售审核记录审核人和审核时间

4. **权限控制**:
   - 仅管理员可以审核转销售请求
   - 普通用户只能创建、查看、归还

5. **数据一致性**:
   - 使用 @transaction.atomic 确保事务完整性
   - 状态流转必须符合业务规则

---

**计划版本**：v1.0
**更新时间**：2026-01-06
**计划状态**：待主人审批后开始实施

**期待主人的指示喵 φ(≧ω≦*)♪**
