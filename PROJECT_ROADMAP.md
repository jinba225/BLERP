# BetterLaser ERP - 项目执行路线图

> **更新时间**: 2025-11-10
> **项目阶段**: 核心功能开发阶段
> **当前完成度**: 60%
> **开发策略**: 聚焦贸易型企业，暂不开发生产管理模块

---

## 📊 整体规划

### 开发策略
- ✅ **第一阶段**: 补齐核心业务断点（1-2个月）- **进行中**
- 📋 **第二阶段**: 合同和报表功能（3-4个月）- 待开始
- 🚫 **第三阶段**: 生产管理模块 - **暂不开发**（架构保留扩展性）

### 适用企业类型
- ✅ **贸易型企业** - 完全支持
- ⚠️ **制造型企业** - 部分支持（无生产计划、工单、BOM等功能）

---

## 🎯 第一阶段：核心业务断点修复

**时间周期**: 1-2个月
**工作量估算**: 160小时（2人团队）
**目标**: 让系统具备基本运营能力，打通关键业务闭环

### 任务清单

#### ✅ 任务 1.1: 应付账款自动生成 【已完成】
**完成时间**: 2025-11-10
**工作量**: 已投入约30小时

**已实现功能**:
- ✅ SupplierAccount 模型增强（状态、付款比例、逾期检查）
- ✅ 采购发票认证时自动生成应付账款
- ✅ 应付账款列表和详情页面
- ✅ 手动生成应付账款功能
- ✅ 发票认证确认页面

**成果文件**:
- `apps/finance/models.py` (SupplierAccount 模型)
- `apps/finance/views.py` (供应商账款视图)
- `templates/finance/supplier_account_*.html` (应付账款模板)

---

#### 📋 任务 1.2: 财务报表生成 【待开始】⭐⭐⭐⭐⭐
**优先级**: 最高
**预计工作量**: 40小时（2周）
**紧迫性**: 企业合规运营必需

**需求描述**:
财务报表是企业合规运营的基础，必须能够自动生成符合会计准则的财务报表。

**功能要求**:

1. **资产负债表**
   ```
   资产 = 负债 + 所有者权益
   - 流动资产（现金、应收账款、存货等）
   - 固定资产
   - 流动负债（应付账款、短期借款等）
   - 长期负债
   - 所有者权益（实收资本、未分配利润等）
   ```

2. **利润表（损益表）**
   ```
   净利润 = 营业收入 - 营业成本 - 费用 + 其他收益
   - 营业收入（主营业务收入、其他业务收入）
   - 营业成本
   - 销售费用、管理费用、财务费用
   - 利润总额、净利润
   ```

3. **现金流量表**
   ```
   现金净增加额 = 经营活动现金流 + 投资活动现金流 + 筹资活动现金流
   - 经营活动现金流量
   - 投资活动现金流量
   - 筹资活动现金流量
   ```

4. **辅助报表**
   - 科目余额表（期初余额、借方发生额、贷方发生额、期末余额）
   - 科目明细账
   - 总账

**技术实现**:

```python
# 新增模型: apps/finance/models.py
class FinancialReport(BaseModel):
    """财务报表"""
    REPORT_TYPES = [
        ('balance_sheet', '资产负债表'),
        ('income_statement', '利润表'),
        ('cash_flow', '现金流量表'),
        ('trial_balance', '科目余额表'),
    ]

    report_type = models.CharField('报表类型', max_length=20, choices=REPORT_TYPES)
    report_date = models.DateField('报表日期')
    start_date = models.DateField('开始日期', null=True)  # 损益表、现金流量表需要
    end_date = models.DateField('结束日期', null=True)
    report_data = models.JSONField('报表数据')
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)

# 新增视图: apps/finance/views.py
class FinancialReportGenerator:
    """财务报表生成器"""

    def generate_balance_sheet(self, report_date):
        """生成资产负债表"""
        # 1. 获取所有资产类科目的余额
        # 2. 获取所有负债类科目的余额
        # 3. 获取所有权益类科目的余额
        # 4. 计算合计和验证平衡
        pass

    def generate_income_statement(self, start_date, end_date):
        """生成利润表"""
        # 1. 获取收入类科目的发生额
        # 2. 获取成本类科目的发生额
        # 3. 获取费用类科目的发生额
        # 4. 计算利润
        pass

    def generate_cash_flow(self, start_date, end_date):
        """生成现金流量表"""
        # 1. 分析现金类科目的变动
        # 2. 按活动类型分类
        # 3. 计算现金净增加额
        pass
```

**模板文件**:
- `templates/finance/report_balance_sheet.html` - 资产负债表
- `templates/finance/report_income_statement.html` - 利润表
- `templates/finance/report_cash_flow.html` - 现金流量表
- `templates/finance/report_trial_balance.html` - 科目余额表
- `templates/finance/report_list.html` - 报表列表
- `templates/finance/report_generator.html` - 报表生成器

**验收标准**:
- [ ] 能够生成指定日期的资产负债表，且资产=负债+权益
- [ ] 能够生成指定期间的利润表，数据准确
- [ ] 能够生成指定期间的现金流量表
- [ ] 能够导出Excel格式
- [ ] 报表数据可保存和历史查询

**依赖关系**:
- 需要完整的科目体系（已有）
- 需要准确的凭证数据（已有）
- 需要凭证已过账（需补充过账逻辑）

---

#### 📋 任务 1.3: 采购询价管理 【待开始】⭐⭐⭐⭐
**优先级**: 高
**预计工作量**: 40小时（2周）
**紧迫性**: 采购流程关键环节

**需求描述**:
采购询价是采购流程的起点，需要能够向多个供应商询价、收集报价、进行比价分析。

**业务流程**:
```
采购需求 → 创建询价单 → 发送供应商 → 收集报价 → 比价分析 → 选定供应商 → 创建采购订单
```

**功能要求**:

1. **询价单管理**
   - 创建询价单（从采购申请或手工创建）
   - 添加询价产品明细
   - 设置期望交期和数量
   - 选择询价供应商（可选多个）

2. **供应商报价**
   - 供应商提交报价
   - 记录报价价格、交期、付款条件
   - 支持多轮报价

3. **比价分析**
   - 按产品对比不同供应商的报价
   - 价格、交期、质量等多维度对比
   - 生成比价分析表

4. **转采购订单**
   - 选定供应商后一键转采购订单

**技术实现**:

```python
# 新增模型: apps/purchase/models.py
class PurchaseInquiry(BaseModel):
    """采购询价单"""
    INQUIRY_STATUS = [
        ('draft', '草稿'),
        ('sent', '已发送'),
        ('quoted', '已报价'),
        ('compared', '已比价'),
        ('confirmed', '已确定'),
        ('cancelled', '已取消'),
    ]

    inquiry_number = models.CharField('询价单号', max_length=100, unique=True)
    inquiry_date = models.DateField('询价日期')
    required_date = models.DateField('要求交期')
    status = models.CharField('状态', max_length=20, choices=INQUIRY_STATUS, default='draft')
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='采购员')
    remark = models.TextField('备注', blank=True)

class PurchaseInquiryItem(BaseModel):
    """询价明细"""
    inquiry = models.ForeignKey(PurchaseInquiry, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField('数量', max_digits=10, decimal_places=3)
    target_price = models.DecimalField('目标价格', max_digits=10, decimal_places=2, null=True, blank=True)
    specifications = models.TextField('规格要求', blank=True)

class SupplierQuotation(BaseModel):
    """供应商报价"""
    QUOTATION_STATUS = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('selected', '已选中'),
        ('rejected', '已拒绝'),
    ]

    inquiry = models.ForeignKey(PurchaseInquiry, on_delete=models.CASCADE, related_name='quotations')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE)
    quotation_date = models.DateField('报价日期')
    delivery_days = models.IntegerField('交货天数')
    payment_terms = models.CharField('付款条件', max_length=200)
    status = models.CharField('状态', max_length=20, choices=QUOTATION_STATUS, default='draft')
    total_amount = models.DecimalField('报价总额', max_digits=12, decimal_places=2, default=0)

class SupplierQuotationItem(BaseModel):
    """供应商报价明细"""
    quotation = models.ForeignKey(SupplierQuotation, on_delete=models.CASCADE, related_name='items')
    inquiry_item = models.ForeignKey(PurchaseInquiryItem, on_delete=models.CASCADE)
    quote_price = models.DecimalField('报价单价', max_digits=10, decimal_places=2)
    quote_quantity = models.DecimalField('报价数量', max_digits=10, decimal_places=3)
    delivery_date = models.DateField('承诺交期', null=True, blank=True)
    remark = models.TextField('备注', blank=True)
```

**模板文件**:
- `templates/purchase/inquiry_list.html` - 询价单列表
- `templates/purchase/inquiry_form.html` - 询价单表单
- `templates/purchase/inquiry_detail.html` - 询价单详情
- `templates/purchase/quotation_form.html` - 供应商报价表单
- `templates/purchase/quotation_comparison.html` - 比价分析

**验收标准**:
- [ ] 能够创建询价单并添加产品明细
- [ ] 能够选择多个供应商发送询价
- [ ] 供应商能够提交报价（或采购员代录）
- [ ] 能够进行多供应商比价分析
- [ ] 能够选定供应商并转采购订单

---

#### 📋 任务 1.4: 自动凭证生成 【待开始】⭐⭐⭐⭐
**优先级**: 高
**预计工作量**: 30小时（1.5周）
**紧迫性**: 打通业务与财务

**需求描述**:
业务单据审核或完成时，自动生成对应的会计凭证，减少手工录入工作量，确保业务与财务同步。

**自动凭证场景**:

1. **销售订单审核** → 生成凭证
   ```
   借: 应收账款 - 客户A
   贷: 主营业务收入
   贷: 应交税费 - 增值税 - 销项税额
   ```

2. **采购订单审核** → 生成凭证
   ```
   借: 库存商品
   借: 应交税费 - 增值税 - 进项税额
   贷: 应付账款 - 供应商A
   ```

3. **销售收款** → 生成凭证
   ```
   借: 银行存款
   贷: 应收账款 - 客户A
   ```

4. **采购付款** → 生成凭证
   ```
   借: 应付账款 - 供应商A
   贷: 银行存款
   ```

5. **销售发货（确认收入）** → 生成凭证
   ```
   借: 主营业务成本
   贷: 库存商品
   ```

**技术实现**:

```python
# 新增工具类: apps/finance/voucher_generator.py
class VoucherGenerator:
    """凭证自动生成器"""

    def generate_for_sales_order(self, sales_order):
        """销售订单审核时生成凭证"""
        if sales_order.status != 'confirmed':
            return None

        journal = Journal.objects.create(
            journal_number=DocumentNumberGenerator.generate('voucher'),
            journal_type='general',
            journal_date=sales_order.order_date,
            reference_type='sales_order',
            reference_id=str(sales_order.id),
            reference_number=sales_order.order_number,
            description=f'销售订单 {sales_order.order_number}',
            prepared_by=sales_order.updated_by,
        )

        # 借: 应收账款
        JournalEntry.objects.create(
            journal=journal,
            account=Account.objects.get(code='1122'),  # 应收账款
            debit_amount=sales_order.total_amount,
            customer=sales_order.customer,
            description=f'销售订单 {sales_order.order_number}',
        )

        # 贷: 主营业务收入
        JournalEntry.objects.create(
            journal=journal,
            account=Account.objects.get(code='6001'),  # 主营业务收入
            credit_amount=sales_order.total_amount - sales_order.tax_amount,
            description=f'销售订单 {sales_order.order_number}',
        )

        # 贷: 应交税费
        if sales_order.tax_amount > 0:
            JournalEntry.objects.create(
                journal=journal,
                account=Account.objects.get(code='2221'),  # 应交税费
                credit_amount=sales_order.tax_amount,
                description=f'增值税销项税额',
            )

        # 计算借贷合计
        journal.total_debit = sales_order.total_amount
        journal.total_credit = sales_order.total_amount
        journal.save()

        return journal

    def generate_for_purchase_order(self, purchase_order):
        """采购订单审核时生成凭证"""
        # 类似逻辑
        pass

    def generate_for_payment(self, payment):
        """收付款时生成凭证"""
        # 类似逻辑
        pass
```

**集成点**:
- `apps/sales/views.py` - `approve_order()` 函数中调用
- `apps/purchase/views.py` - `approve_order()` 函数中调用
- `apps/finance/views.py` - 收付款视图中调用

**配置管理**:
```python
# 新增: apps/finance/voucher_config.py
VOUCHER_TEMPLATES = {
    'sales_order': {
        'enabled': True,
        'accounts': {
            'receivable': '1122',  # 应收账款
            'revenue': '6001',     # 主营业务收入
            'tax': '2221',         # 应交税费
        }
    },
    'purchase_order': {
        'enabled': True,
        'accounts': {
            'inventory': '1405',   # 库存商品
            'payable': '2202',     # 应付账款
            'tax': '2221',         # 应交税费
        }
    },
    # ... 更多配置
}
```

**验收标准**:
- [ ] 销售订单审核自动生成凭证
- [ ] 采购订单审核自动生成凭证
- [ ] 收付款自动生成凭证
- [ ] 发货确认收入自动生成成本结转凭证
- [ ] 凭证借贷平衡
- [ ] 可配置是否启用自动凭证
- [ ] 自动凭证可审核和撤销

---

#### 📋 任务 1.5: 核销机制完善 【待开始】⭐⭐⭐
**优先级**: 中
**预计工作量**: 20小时（1周）
**紧迫性**: 应收应付管理完整性

**需求描述**:
完善收款与应收账款、付款与应付账款的核销机制，确保账款清晰准确。

**业务流程**:
```
收款 → 选择应收账款 → 核销 → 更新应收余额
付款 → 选择应付账款 → 核销 → 更新应付余额
```

**功能要求**:

1. **收款核销**
   - 收款时关联对应的应收账款
   - 支持一笔收款核销多个应收
   - 支持多笔收款核销一个应收
   - 自动更新应收账款的已付金额和余额
   - 核销历史记录

2. **付款核销**
   - 付款时关联对应的应付账款
   - 支持一笔付款核销多个应付
   - 支持多笔付款核销一个应付
   - 自动更新应付账款的已付金额和余额
   - 核销历史记录

3. **核销管理**
   - 核销单独管理
   - 核销可撤销（未过账的）
   - 核销明细查询
   - 未核销款项查询

**技术实现**:

```python
# 新增模型: apps/finance/models.py
class WriteOff(BaseModel):
    """核销记录"""
    WRITEOFF_TYPE = [
        ('receivable', '应收核销'),
        ('payable', '应付核销'),
    ]

    writeoff_number = models.CharField('核销单号', max_length=100, unique=True)
    writeoff_type = models.CharField('核销类型', max_length=20, choices=WRITEOFF_TYPE)
    writeoff_date = models.DateField('核销日期')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='writeoffs')
    total_amount = models.DecimalField('核销总额', max_digits=12, decimal_places=2)
    is_reversed = models.BooleanField('是否已撤销', default=False)
    reversed_at = models.DateTimeField('撤销时间', null=True, blank=True)

class WriteOffItem(BaseModel):
    """核销明细"""
    writeoff = models.ForeignKey(WriteOff, on_delete=models.CASCADE, related_name='items')
    customer_account = models.ForeignKey(
        CustomerAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='writeoff_items'
    )
    supplier_account = models.ForeignKey(
        SupplierAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='writeoff_items'
    )
    writeoff_amount = models.DecimalField('核销金额', max_digits=12, decimal_places=2)
```

**模板文件**:
- `templates/finance/writeoff_list.html` - 核销记录列表
- `templates/finance/writeoff_form.html` - 核销表单
- `templates/finance/writeoff_detail.html` - 核销详情

**验收标准**:
- [ ] 收款时能够核销应收账款
- [ ] 付款时能够核销应付账款
- [ ] 支持一笔款项核销多个账款
- [ ] 自动更新账款余额
- [ ] 核销记录可查询
- [ ] 核销可撤销

---

#### 📋 任务 1.6: 质检流程 【待开始】⭐⭐⭐
**优先级**: 中
**预计工作量**: 30小时（1.5周）
**紧迫性**: 质量管理提升

**需求描述**:
建立完整的质检流程，确保采购收货质量可控。

**业务流程**:
```
采购收货 → 创建质检单 → 质检检验 → 质检结果 → 合格入库/不合格退货
```

**功能要求**:

1. **质检单管理**
   - 从收货单自动生成质检单
   - 手工创建质检单
   - 质检项目配置
   - 质检标准设定

2. **质检执行**
   - 质检员录入检验结果
   - 支持抽检和全检
   - 不合格项记录
   - 质检照片上传

3. **质检结果处理**
   - 合格：自动更新收货单状态，允许入库
   - 不合格：锁定库存，生成退货单
   - 让步接收：特殊审批后入库

4. **质检报表**
   - 质检统计报表
   - 供应商质量分析

**技术实现**:

```python
# 新增模型: apps/purchase/models.py (或独立quality app)
class QualityInspection(BaseModel):
    """质检单"""
    INSPECTION_TYPE = [
        ('incoming', '来料检验'),
        ('process', '过程检验'),
        ('final', '成品检验'),
    ]

    INSPECTION_STATUS = [
        ('pending', '待检'),
        ('in_progress', '检验中'),
        ('passed', '合格'),
        ('failed', '不合格'),
        ('conditional', '让步接收'),
    ]

    inspection_number = models.CharField('质检单号', max_length=100, unique=True)
    inspection_type = models.CharField('检验类型', max_length=20, choices=INSPECTION_TYPE)
    status = models.CharField('状态', max_length=20, choices=INSPECTION_STATUS, default='pending')
    receipt = models.ForeignKey(PurchaseReceipt, on_delete=models.CASCADE, related_name='inspections')
    inspection_date = models.DateField('检验日期')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='质检员')

class QualityInspectionItem(BaseModel):
    """质检明细"""
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='items')
    receipt_item = models.ForeignKey(PurchaseReceiptItem, on_delete=models.CASCADE)
    sample_quantity = models.DecimalField('抽检数量', max_digits=10, decimal_places=3)
    passed_quantity = models.DecimalField('合格数量', max_digits=10, decimal_places=3)
    failed_quantity = models.DecimalField('不合格数量', max_digits=10, decimal_places=3)
    inspection_result = models.CharField('检验结果', max_length=20)
    defect_description = models.TextField('缺陷描述', blank=True)
```

**模板文件**:
- `templates/purchase/inspection_list.html` - 质检单列表
- `templates/purchase/inspection_form.html` - 质检单表单
- `templates/purchase/inspection_detail.html` - 质检详情

**验收标准**:
- [ ] 收货后能创建质检单
- [ ] 质检员能录入检验结果
- [ ] 合格后自动更新收货单状态
- [ ] 不合格能生成退货单
- [ ] 质检数据可追溯查询

---

### 第一阶段总结

**总工作量**: 160小时（约8周，2人团队，或4周，4人团队）

**完成后效果**:
- ✅ 业务与财务打通（自动凭证）
- ✅ 财务报表可自动生成（合规运营）
- ✅ 采购流程完整（询价→订单→收货→质检→入库）
- ✅ 应收应付管理完善（核销机制完整）
- ✅ 质量管理可控（质检流程完整）

**里程碑**:
- 系统具备基本运营能力
- 可以在小范围试运行
- 为第二阶段打下基础

---

## 📊 第二阶段：合同和报表功能

**时间周期**: 3-4个月
**工作量估算**: 240小时（2人团队）
**目标**: 补齐高级功能，提升管理能力

### 任务清单

#### 📋 任务 2.1: 合同管理模块 【待开始】
**预计工作量**: 80小时（4周）

**需求描述**:
建立销售合同和采购合同管理体系，规范合同签订和执行流程。

**功能要求**:

1. **销售合同管理**
   - 合同基本信息（编号、客户、金额、签订日期）
   - 合同条款管理（付款条件、交货条件、违约责任）
   - 合同附件（扫描件、PDF）
   - 合同审批流程
   - 合同执行跟踪（订单关联、发货进度、回款进度）
   - 合同变更管理
   - 合同到期提醒

2. **采购合同管理**
   - 合同基本信息（编号、供应商、金额、签订日期）
   - 合同条款管理
   - 合同附件
   - 合同审批流程
   - 合同执行跟踪（订单关联、收货进度、付款进度）
   - 合同变更管理
   - 合同到期提醒

3. **合同分析**
   - 合同履约率统计
   - 合同金额统计
   - 客户/供应商合同分析

**技术实现**:

```python
# 新增模块: apps/contracts/
class Contract(BaseModel):
    """合同"""
    CONTRACT_TYPE = [
        ('sales', '销售合同'),
        ('purchase', '采购合同'),
        ('lease', '借用合同'),
    ]

    CONTRACT_STATUS = [
        ('draft', '草稿'),
        ('reviewing', '审批中'),
        ('approved', '已批准'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('terminated', '已终止'),
    ]

    contract_number = models.CharField('合同编号', max_length=100, unique=True)
    contract_type = models.CharField('合同类型', max_length=20, choices=CONTRACT_TYPE)
    status = models.CharField('状态', max_length=20, choices=CONTRACT_STATUS, default='draft')

    # 关联方
    customer = models.ForeignKey('customers.Customer', null=True, blank=True)
    supplier = models.ForeignKey('suppliers.Supplier', null=True, blank=True)

    # 合同基本信息
    signing_date = models.DateField('签订日期')
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    contract_amount = models.DecimalField('合同金额', max_digits=15, decimal_places=2)

    # 付款条件
    payment_terms = models.TextField('付款条件')
    delivery_terms = models.TextField('交货条件')

    # 附件
    attachment = models.FileField('合同附件', upload_to='contracts/%Y/%m/', null=True, blank=True)

class ContractItem(BaseModel):
    """合同明细"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField('数量', max_digits=10, decimal_places=3)
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    delivery_date = models.DateField('交货日期', null=True, blank=True)
```

**验收标准**:
- [ ] 能够创建销售合同和采购合同
- [ ] 合同审批流程完整
- [ ] 合同能够关联订单
- [ ] 合同执行进度可追踪
- [ ] 合同到期提前提醒

---

#### 📋 任务 2.2: 报表中心 【待开始】
**预计工作量**: 80小时（4周）

**需求描述**:
建立完整的业务报表体系，支持数据分析和决策。

**报表清单** (36个核心报表):

**销售报表** (10个):
1. 销售日报/月报/年报
2. 销售排行榜（产品、客户、销售员）
3. 销售趋势分析
4. 客户销售分析
5. 产品销售分析
6. 销售订单统计
7. 发货统计
8. 退货统计
9. 销售毛利分析
10. 应收账款账龄分析

**采购报表** (8个):
1. 采购日报/月报/年报
2. 采购排行榜（产品、供应商）
3. 供应商采购分析
4. 产品采购分析
5. 采购订单统计
6. 收货统计
7. 退货统计
8. 应付账款账龄分析

**库存报表** (8个):
1. 库存余额表
2. 库存流水账
3. 库存收发汇总表
4. 库存周转率分析
5. 呆滞库存分析
6. 库存预警报表
7. 库存盘点差异表
8. 库存成本分析

**财务报表** (10个):
1. 资产负债表
2. 利润表
3. 现金流量表
4. 科目余额表
5. 科目明细账
6. 应收账款账龄分析
7. 应付账款账龄分析
8. 收款统计
9. 付款统计
10. 费用统计

**技术实现**:

```python
# apps/reports/views.py
class ReportGenerator:
    """报表生成器"""

    def sales_summary_report(self, start_date, end_date):
        """销售汇总报表"""
        orders = SalesOrder.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
            is_deleted=False
        )

        data = {
            'total_orders': orders.count(),
            'total_amount': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'by_customer': orders.values('customer__name').annotate(
                count=Count('id'),
                amount=Sum('total_amount')
            ),
            'by_product': SalesOrderItem.objects.filter(
                order__in=orders
            ).values('product__name').annotate(
                quantity=Sum('quantity'),
                amount=Sum('line_total')
            ),
        }
        return data
```

**模板体系**:
- `templates/reports/report_list.html` - 报表目录
- `templates/reports/sales/` - 销售报表模板
- `templates/reports/purchase/` - 采购报表模板
- `templates/reports/inventory/` - 库存报表模板
- `templates/reports/finance/` - 财务报表模板

**导出功能**:
- Excel导出（使用 openpyxl）
- PDF导出（使用 WeasyPrint）
- CSV导出

**验收标准**:
- [ ] 至少完成36个核心报表
- [ ] 报表数据准确
- [ ] 支持日期范围筛选
- [ ] 支持Excel/PDF导出
- [ ] 图表可视化展示

---

#### 📋 任务 2.3: 库存流程优化 【待开始】
**预计工作量**: 40小时（2周）

**功能要求**:

1. **拣货流程完善**
   - 拣货单生成（从发货单）
   - 拣货任务分配
   - 拣货完成确认
   - 拣货效率统计

2. **盘点差异处理**
   - 盘点差异自动分析
   - 差异原因分类
   - 差异调整单自动生成
   - 盘点结果审批

3. **库存预警增强**
   - 低库存预警
   - 超储预警
   - 保质期预警
   - 预警通知推送

**验收标准**:
- [ ] 拣货流程完整
- [ ] 盘点差异自动调整
- [ ] 库存预警实时推送

---

#### 📋 任务 2.4: 批量操作和导入导出 【待开始】
**预计工作量**: 40小时（2周）

**功能要求**:

1. **批量操作**
   - 批量审核
   - 批量删除
   - 批量导出
   - 批量打印

2. **数据导入**
   - 客户资料导入
   - 产品资料导入
   - 期初库存导入
   - 期初余额导入
   - 数据验证和错误提示

3. **数据导出**
   - 业务单据导出
   - 基础资料导出
   - 自定义字段导出
   - 导出模板配置

**验收标准**:
- [ ] 支持Excel批量导入主数据
- [ ] 支持批量操作业务单据
- [ ] 导入错误提示友好
- [ ] 导出格式可自定义

---

### 第二阶段总结

**总工作量**: 240小时（约12周，2人团队）

**完成后效果**:
- ✅ 合同管理规范化
- ✅ 业务数据可视化（36个核心报表）
- ✅ 库存管理更精细
- ✅ 数据导入导出便捷

**里程碑**:
- 系统功能完整，可正式上线运营
- 管理能力大幅提升
- 决策支持完善

---

## 🚫 第三阶段：生产管理（暂不开发）

**说明**:
- 当前系统面向贸易型企业，暂不开发生产管理模块
- 架构设计已预留扩展接口
- 未来如需支持生产管理，可基于现有架构快速开发

**预留扩展点**:
1. 产品模型已支持 BOM 关联（通过 JSONField 或新建 BOM 模型）
2. 库存事务支持生产入库和领料出库
3. 单据号生成器支持生产工单编号
4. 审批流程框架可复用到生产工单

**未来可扩展模块**:
- 物料清单（BOM）管理
- 生产计划和排程
- 生产工单管理
- 工艺路线管理
- 生产领料/退料
- 生产进度跟踪
- 产能分析

---

## 📅 时间计划

### Gantt 图示

```
第一阶段 (1-2个月):
周1-2  ████ 财务报表生成
周3-4  ████ 采购询价管理
周5-6  ███  自动凭证生成
周7    ██   核销机制完善
周8-9  ███  质检流程

第二阶段 (3-4个月):
月1    ████████ 合同管理模块
月2    ████████ 报表中心
月3    ████     库存流程优化
月4    ████     批量操作和导入导出
```

### 关键里程碑

| 里程碑 | 目标日期 | 成果 |
|--------|---------|------|
| 🏁 M1: 第一阶段完成 | 2个月后 | 系统具备基本运营能力 |
| 🎯 M2: 试运行开始 | 2.5个月后 | 小范围上线试运行 |
| 🏁 M3: 第二阶段完成 | 6个月后 | 系统功能完整，正式上线 |
| 🎉 M4: 全面上线 | 7个月后 | 替代Legacy系统 |

---

## 🎯 成功标准

### 第一阶段完成标准
- [ ] 财务三大报表可自动生成且数据准确
- [ ] 采购询价流程打通，可进行供应商比价
- [ ] 业务单据审核自动生成凭证
- [ ] 收付款与应收应付核销完整
- [ ] 质检流程完整，不合格品可追溯
- [ ] 所有功能通过测试

### 第二阶段完成标准
- [ ] 销售合同和采购合同管理完整
- [ ] 36个核心报表全部实现
- [ ] 库存拣货和盘点流程完善
- [ ] 批量操作和导入导出功能完整
- [ ] 所有功能通过测试

### 最终验收标准
- [ ] 业务流程闭环（销售、采购、库存、财务）
- [ ] 数据准确性 > 99%
- [ ] 系统稳定性 > 99.5%
- [ ] 用户满意度 > 85%
- [ ] 可替代Legacy系统

---

## 📝 风险管理

### 技术风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 性能问题 | 高 | 数据量大时查询慢 → 添加索引、优化查询、引入缓存 |
| 数据一致性 | 高 | 并发操作导致数据错误 → 使用事务、加锁机制 |
| 报表性能 | 中 | 复杂报表生成慢 → 异步任务、数据预聚合 |

### 业务风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 需求变更 | 中 | 需求频繁变化 → 敏捷开发、迭代交付 |
| 数据迁移失败 | 高 | Legacy数据迁移出错 → 充分测试、备份、灰度上线 |
| 用户抵触 | 中 | 用户不愿使用新系统 → 充分培训、分步上线 |

### 项目风险

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 人员流失 | 高 | 核心开发人员离职 → 代码文档化、知识共享 |
| 进度延期 | 中 | 开发时间超预期 → 优先级管理、MVP思维 |
| 预算超支 | 中 | 开发成本增加 → 控制范围、分阶段验收 |

---

## 📚 参考资料

### 开发文档
- Django 4.2 官方文档: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Tailwind CSS: https://tailwindcss.com/

### 会计准则
- 企业会计准则 - 基本准则
- 小企业会计准则
- 会计科目和账务处理

### 项目文档
- `/CLAUDE.md` - 项目总览
- `/django_erp/apps/*/CLAUDE.md` - 各模块文档
- `/django_erp/PROJECT_ROADMAP.md` - 本文档

---

## ✅ 附录：任务检查清单

### 开发前检查
- [ ] 需求文档已评审
- [ ] 技术方案已确定
- [ ] 数据库设计已完成
- [ ] 接口设计已完成

### 开发中检查
- [ ] 代码符合编码规范
- [ ] 单元测试覆盖率 > 70%
- [ ] 代码已审查
- [ ] 文档已更新

### 上线前检查
- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 安全测试通过
- [ ] 用户验收通过
- [ ] 数据备份完成
- [ ] 回滚方案已准备

---

**文档版本**: v1.0
**最后更新**: 2025-11-10
**维护者**: BetterLaser ERP 开发团队
