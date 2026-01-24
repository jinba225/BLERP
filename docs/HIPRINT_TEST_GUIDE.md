# HiPrint 功能快速测试指南

## 🧪 测试环境准备

### 1. 启动开发服务器

```bash
cd /Users/janjung/Code_Projects/BLBS_ERP/django_erp
source venv/bin/activate
python manage.py runserver
```

### 2. 访问模板编辑器

```
http://localhost:8000/sales/templates/
```

点击任意模板的"编辑"按钮进入设计器。

---

## ✅ 测试一：WYSIWYG功能

### 目标
验证拖拽元素后能立即在画布上看到，无需保存。

### 步骤

1. **打开模板编辑器**
   - 进入：`http://localhost:8000/sales/templates/<template_id>/edit/`

2. **测试文本元素**
   - 从左侧"📝 基础元素"找到"文本"
   - 拖拽到中间画布的任意位置
   - ✅ **预期结果：** 立即显示文本框，提示"元素已添加到画布！"

3. **测试数据字段元素**
   - 从左侧"🔖 基本信息"找到"报价单号"
   - 拖拽到画布
   - ✅ **预期结果：** 立即显示带字段名称的元素

4. **测试条形码元素**
   - 从左侧"▦ 条码元素"找到"条形码"
   - 拖拽到画布
   - ✅ **预期结果：** 立即显示条形码占位符

5. **测试元素属性修改**
   - 点击刚添加的元素
   - 右侧属性面板修改字体大小、颜色等
   - ✅ **预期结果：** 修改立即生效

6. **测试元素拖动**
   - 拖动已添加的元素到新位置
   - ✅ **预期结果：** 元素跟随鼠标移动

7. **保存并验证**
   - 点击"保存模板"按钮
   - 刷新页面（Ctrl+R）
   - ✅ **预期结果：** 之前添加的所有元素仍然存在

### 预期控制台输出

打开浏览器控制台（F12），拖拽元素时应看到：

```
>>> 准备添加元素到画布 (WYSIWYG模式)
>>> 元素类型: text
>>> 位置: 150 200
>>> 当前面板: [object Object]
>>> 元素配置: {left: 150, top: 200, width: 150, ...}
>>> 添加文本元素
✅ 元素已添加到画布: [object Object]
```

### 常见问题

| 现象 | 原因 | 解决方法 |
|------|------|----------|
| 拖拽无反应 | 浏览器缓存 | 按 Ctrl+F5 强制刷新 |
| 提示"模板未初始化" | HiPrint未加载 | 检查网络，重新加载页面 |
| 元素添加后消失 | API调用失败 | 查看控制台错误日志 |

---

## ✅ 测试二：表格字段扩展

### 目标
验证打印预览中表格显示12列完整数据。

### 前置条件

需要有一个包含产品明细的报价单。如果没有，请先创建：

```bash
# Django shell 快速创建测试数据
source venv/bin/activate
python manage.py shell

# 在shell中执行：
from apps.sales.models import Quote, QuoteItem
from apps.customers.models import Customer
from apps.products.models import Product, Unit

# 获取或创建测试数据
customer = Customer.objects.first()
product = Product.objects.first()

if customer and product:
    # 确保产品有单位
    if not product.unit:
        unit, _ = Unit.objects.get_or_create(
            name='台',
            defaults={'code': 'TAI'}
        )
        product.unit = unit
        product.specifications = '10W 红外激光器，功率可调'
        product.save()

    # 创建报价单
    quote = Quote.objects.create(
        customer=customer,
        quote_number='TEST-Q-001',
        quote_type='domestic',
        status='draft'
    )

    # 创建明细项（含税率）
    QuoteItem.objects.create(
        quote=quote,
        product=product,
        quantity=10,
        unit_price=1000,
        discount_rate=5,
        tax_rate=13,  # 新增字段
        lead_time=30,
        notes='测试明细项'
    )

    print(f"✅ 测试报价单已创建: {quote.quote_number}")
    print(f"   明细项数量: {quote.items.count()}")
else:
    print("❌ 请先创建客户和产品")
```

### 步骤

1. **进入报价单详情页**
   ```
   http://localhost:8000/sales/quotes/<quote_id>/
   ```

2. **点击"打印"按钮**
   - 会打开新窗口显示打印预览

3. **检查表格列**

   表格应包含以下12列（从左到右）：

   | 列号 | 列名 | 示例数据 |
   |------|------|----------|
   | 1 | 序号 | 1 |
   | 2 | 产品编码 | BL-001 |
   | 3 | 产品名称 | 激光器 |
   | 4 | **规格型号** ⭐ | 10W 红外激光器，功率可调 |
   | 5 | 数量 | 10 |
   | 6 | **单位** ⭐ | 台 |
   | 7 | 单价 | 1000.00 |
   | 8 | 折扣率 | 5% |
   | 9 | **税率** ⭐ | 13% |
   | 10 | 小计 | 9500.00 |
   | 11 | 交货期 | 30天 |
   | 12 | **备注** ⭐ | 测试明细项 |

4. **检查合计行**
   - ✅ "合计："应显示在第10列（小计列）之前
   - ✅ 总金额应显示为红色粗体
   - ✅ colspan应正确，不出现错位

5. **测试打印**
   - 点击"打印"按钮
   - 检查打印预览
   - ✅ **预期结果：** 所有12列都显示完整，无截断

6. **测试导出PDF**
   - 点击"导出PDF"按钮
   - 下载并打开PDF文件
   - ✅ **预期结果：** PDF中表格完整显示

### 预期控制台输出

```
=== 打印页面初始化 ===
模板JSON: {panels: [...]}
报价单数据: {quote_number: "TEST-Q-001", items: [...]}
✅ 模板渲染完成
🔄 开始查找并替换表格占位符...
找到 1 个占位符
✅ 表格已插入
```

### 数据验证检查清单

- [ ] **规格型号列** 显示产品的specifications字段
- [ ] **单位列** 显示产品的unit.name（如：台、个、套）
- [ ] **税率列** 显示为百分比格式（如：13%）
- [ ] **备注列** 显示明细项的notes字段
- [ ] 空值显示为"-"而不是空白或"null"
- [ ] 数字列右对齐，文本列左对齐
- [ ] 合计行正确计算总金额

---

## ✅ 测试三：字段空值处理

### 目标
验证字段为空时的显示效果。

### 步骤

1. **创建一个没有规格、单位、税率的明细项**

```python
# Django shell
QuoteItem.objects.create(
    quote=quote,
    product=product,
    quantity=5,
    unit_price=500,
    # 不设置 tax_rate（使用默认值13%）
    # product.specifications 为空
    # product.unit 为空
)
```

2. **查看打印预览**

3. **验证空值显示**
   - 规格型号为空 → 应显示 **"-"**
   - 单位为空 → 应显示 **"个"**（默认值）
   - 税率为空 → 应显示 **"0%"** 或 **"13%"**（默认值）
   - 备注为空 → 应显示空白（正常）

---

## 🐛 常见问题排查

### 问题1：表格不显示或显示空白

**检查步骤：**
1. 打开浏览器控制台（F12）
2. 查看是否有JavaScript错误
3. 检查`quoteData.items`是否有数据：
   ```javascript
   console.log('报价单数据:', quoteData);
   ```

**可能原因：**
- 报价单没有明细项
- 模板中没有添加"明细表格占位符"
- JavaScript函数执行失败

### 问题2：新字段显示为空或"undefined"

**检查步骤：**
1. 确认数据库迁移已执行：
   ```bash
   python manage.py showmigrations sales
   ```
   应显示：`[X] 0007_quoteitem_tax_rate`

2. 检查Product模型是否有相关字段：
   ```python
   # Django shell
   from apps.products.models import Product
   p = Product.objects.first()
   print(p.specifications)  # 规格型号
   print(p.unit)            # 单位
   ```

### 问题3：WYSIWYG不工作，仍需保存才能看到

**检查步骤：**
1. 清除浏览器缓存：Ctrl+Shift+Delete
2. 强制刷新页面：Ctrl+F5
3. 检查控制台是否有错误
4. 验证HiPrint版本是否支持这些API

**调试代码：**
```javascript
// 在控制台执行
console.log('hiprintTemplate:', hiprintTemplate);
console.log('printPanels:', hiprintTemplate.printPanels);
console.log('panel methods:', Object.keys(hiprintTemplate.printPanels[0]));
```

---

## 📊 性能测试

### 大量明细项测试

测试目标：验证表格在有大量明细项时的性能。

```python
# Django shell - 创建100个明细项
from apps.sales.models import Quote, QuoteItem
from apps.products.models import Product

quote = Quote.objects.get(quote_number='TEST-Q-001')
product = Product.objects.first()

for i in range(100):
    QuoteItem.objects.create(
        quote=quote,
        product=product,
        quantity=i+1,
        unit_price=100 + i,
        tax_rate=13,
        notes=f'明细项{i+1}'
    )

print(f"✅ 已创建100个明细项")
```

**验证点：**
- [ ] 打印预览加载时间 < 3秒
- [ ] 表格滚动流畅
- [ ] 页面不卡顿
- [ ] 浏览器不崩溃

---

## 📝 测试报告模板

完成测试后，请填写：

```
测试日期：2025-01-__
测试人员：______
浏览器：Chrome / Firefox / Safari (版本: ____)

【WYSIWYG功能】
✅ / ❌ 文本元素拖拽立即显示
✅ / ❌ 数据字段拖拽立即显示
✅ / ❌ 条形码拖拽立即显示
✅ / ❌ 元素属性修改立即生效
✅ / ❌ 保存后不丢失元素

【表格字段扩展】
✅ / ❌ 规格型号显示正确
✅ / ❌ 单位显示正确
✅ / ❌ 税率显示为百分比
✅ / ❌ 备注显示完整
✅ / ❌ 合计行不错位

【空值处理】
✅ / ❌ 规格为空显示"-"
✅ / ❌ 单位为空显示"个"
✅ / ❌ 税率为空显示默认值

【性能测试】
✅ / ❌ 100项明细加载正常
✅ / ❌ 页面响应流畅

【问题记录】
1. _________________________
2. _________________________
```

---

## 🎯 完成标准

所有测试项都应该是 ✅ 才算完成。

如有 ❌ 项，请记录详细错误信息并反馈给开发团队。

**祝测试顺利！** 🚀
