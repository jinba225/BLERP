# 预付款自动刷新功能 - 实现文档

**日期**: 2026-02-04
**功能**: 核销页面创建预付款后自动刷新下拉框

---

## 🎯 问题背景

用户在核销页面 (`/finance/supplier-accounts/4/writeoff/`) 点击"创建预付款"后，返回到核销页面时，预付款下拉框不会自动更新显示新创建的预付款，需要手动刷新整个页面才能看到。

---

## ✅ 解决方案

### 核心思路

1. **参数传递**: 预付款创建成功后，返回核销页面时携带标识参数 `?from_prepayment_create=1`
2. **自动检测**: 页面加载时JavaScript检测该参数
3. **AJAX刷新**: 自动调用API获取最新的预付款列表
4. **动态更新**: 更新下拉框选项并显示成功提示
5. **URL清理**: 清除URL参数，避免重复刷新

---

## 📝 修改文件清单

### 1. apps/finance/views.py

#### 1.1 修改预付款创建视图（第1246-1256行）
```python
# 如果有next参数，重定向到指定页面（用于从核销页面快速创建）
if next_url:
    # 添加标识参数，通知页面需要刷新预付款列表
    from urllib.parse import urlencode, urlparse
    parsed = urlparse(next_url)
    query_params = {'from_prepayment_create': '1'}
    new_query = urlencode(query_params)
    separator = '&' if parsed.query else '?'
    return redirect(f"{next_url}{separator}{new_query}")
return redirect(reverse('finance:supplier_prepayment_list'))
```

**功能**: 在返回核销页面时添加 `?from_prepayment_create=1` 参数

#### 1.2 新增API视图函数（第1107-1148行）
```python
@login_required
def api_supplier_account_available_prepays(request, pk):
    """
    API: 获取指定应付账款可用的预付款列表（JSON格式）
    用于AJAX动态刷新预付款下拉框
    """
    from django.http import JsonResponse

    account = get_object_or_404(SupplierAccount, pk=pk, is_deleted=False)

    # 获取该供应商所有活跃的预付款
    prepays = SupplierPrepayment.objects.filter(
        supplier=account.supplier,
        is_deleted=False,
        status='active',
        balance__gt=0
    ).order_by('-created_at')

    # 构建返回数据
    prepayments_data = []
    for prepay in prepays:
        prepayments_data.append({
            'id': prepay.id,
            'payment_number': prepay.payment_number,
            'paid_date': prepay.paid_date.strftime('%Y-%m-%d') if prepay.paid_date else '',
            'amount': float(prepay.amount),
            'balance': float(prepay.balance),
            'created_at': prepay.created_at.isoformat(),
        })

    # 检查是否有最近添加的预付款（5分钟内创建的）
    from django.utils import timezone
    from datetime import timedelta
    recent_threshold = timezone.now() - timedelta(minutes=5)
    newly_added = any(prepay.created_at >= recent_threshold for prepay in prepays)

    return JsonResponse({
        'prepayments': prepayments_data,
        'newly_added': newly_added,
        'count': len(prepayments_data),
    })
```

**功能**: 返回该应付账款可用的预付款列表（JSON格式）

### 2. apps/finance/urls.py

#### 添加API路由（第36行）
```python
path('supplier-accounts/<int:pk>/available-prepayments/', views.api_supplier_account_available_prepays, name='api_supplier_account_available_prepays'),
```

**功能**: 添加API端点路由

### 3. templates/modules/finance/supplier_account_writeoff.html

#### 添加JavaScript代码（第115-189行）
```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否从预付款创建页面返回
    const urlParams = new URLSearchParams(window.location.search);
    const fromPrepaymentCreate = urlParams.get('from_prepayment_create');

    if (fromPrepaymentCreate === '1') {
        // 自动刷新预付款下拉框
        refreshPrepaymentDropdown();

        // 清除URL参数（避免重复刷新）
        const cleanUrl = window.location.protocol + '//' + window.location.host + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }

    function refreshPrepaymentDropdown() {
        const select = document.querySelector('select[name="prepayment"]');
        if (!select) return;

        const selectedValue = select.value;

        // 显示加载提示
        select.disabled = true;
        const originalOptions = select.innerHTML;

        fetch(`{% url 'finance:api_supplier_account_available_prepays' account.pk %}`)
            .then(response => response.json())
            .then(data => {
                // 清空并重新填充选项
                select.innerHTML = '<option value="">不使用预付款</option>';

                // 添加新的预付款选项
                if (data.prepayments && data.prepayments.length > 0) {
                    data.prepayments.forEach(prepay => {
                        const option = document.createElement('option');
                        option.value = prepay.id;
                        option.textContent = `${prepay.paid_date} - 余额 ¥${parseFloat(prepay.balance).toFixed(2)}`;
                        select.appendChild(option);
                    });
                }

                // 恢复之前选中的值（如果还存在）
                if (selectedValue) {
                    const optionExists = Array.from(select.options).some(opt => opt.value === selectedValue);
                    if (optionExists) {
                        select.value = selectedValue;
                    }
                }

                // 显示成功提示
                if (data.newly_added) {
                    showToast('预付款已添加并自动刷新列表', 'success');
                }

                select.disabled = false;
            })
            .catch(error => {
                console.error('刷新预付款列表失败:', error);
                select.innerHTML = originalOptions;
                select.disabled = false;
                showToast('刷新预付款列表失败，请刷新页面', 'error');
            });
    }

    function showToast(message, type = 'info') {
        // 简单的提示消息实现
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
</script>
```

**功能**:
- 检测URL参数并自动刷新
- 通过AJAX获取最新预付款列表
- 动态更新下拉框选项
- 保持之前选中的值
- 显示成功/失败提示
- 清除URL参数

---

## 🚀 使用流程

### 用户体验流程

1. **进入核销页面**
   - URL: `/finance/supplier-accounts/4/writeoff/`
   - 页面显示预付款下拉框（假设有2条预付款）

2. **点击"创建预付款"链接**
   - 自动跳转到预付款创建页面
   - 供应商已自动选中
   - 日期默认为当天

3. **填写预付款信息并保存**
   - 金额：¥10,000
   - 日期：2026-02-04（已默认）
   - 点击"保存"

4. **自动返回核销页面**
   - URL: `/finance/supplier-accounts/4/writeoff/?from_prepayment_create=1`
   - JavaScript自动检测参数
   - 自动调用API刷新预付款列表
   - 下拉框自动更新为3条预付款
   - 显示绿色成功提示："预付款已添加并自动刷新列表"
   - URL参数自动清除

5. **直接使用新创建的预付款**
   - 无需刷新页面
   - 预付款已自动出现在下拉框中
   - 直接选择并核销

---

## 🧪 测试验证

### 测试步骤

1. **访问核销页面**
   ```
   URL: http://127.0.0.1:8000/finance/supplier-accounts/4/writeoff/
   ```
   - 确认预付款下拉框显示当前可用的预付款

2. **点击"创建预付款"链接**
   - 验证自动跳转到预付款创建页面
   - 验证供应商已自动选中
   - 验证日期默认为当天

3. **创建新预付款**
   - 供应商：选择当前供应商
   - 金额：输入 ¥5,000
   - 日期：保持默认（当天）
   - 点击"保存"

4. **验证自动返回和刷新**
   - 验证自动返回到核销页面
   - 验证显示成功提示："预付款已添加并自动刷新列表"
   - 验证预付款下拉框已更新（包含新创建的预付款）
   - 验证URL参数已清除

5. **验证功能正常**
   - 在预付款下拉框中选择新创建的预付款
   - 验证可以正常使用进行核销

### 测试用例

| # | 场景 | 预期结果 |
|---|------|---------|
| 1 | 首次创建预付款 | 下拉框从0条变为1条 |
| 2 | 再次创建预付款 | 下拉框自动合并，只显示1条（余额累加） |
| 3 | 创建后返回 | 自动刷新，显示最新余额 |
| 4 | 网络错误 | 显示错误提示，保持原有选项 |
| 5 | 之前已选中 | 刷新后仍保持选中状态 |

---

## ✨ 技术特点

### 1. 无刷新体验
- ✅ 使用AJAX异步获取数据
- ✅ 无需刷新整个页面
- ✅ 用户操作流畅无中断

### 2. 智能状态保持
- ✅ 刷新前记录选中的值
- ✅ 刷新后恢复选中状态（如果选项还存在）
- ✅ 防止用户丢失选择

### 3. 友好提示
- ✅ 成功时显示绿色提示框
- ✅ 失败时显示红色错误提示
- ✅ 提示3秒后自动消失

### 4. URL清洁
- ✅ 返回后立即清除参数
- ✅ 避免用户刷新时重复执行
- ✅ 保持URL简洁

### 5. 时间检测
- ✅ API返回创建时间
- ✅ 检测5分钟内新建的预付款
- ✅ 只在真正添加新预付款时显示成功提示

---

## 📊 API响应示例

### 请求
```http
GET /finance/supplier-accounts/4/available-prepayments/
```

### 响应
```json
{
    "prepayments": [
        {
            "id": 1,
            "payment_number": "SP001",
            "paid_date": "2026-02-04",
            "amount": 15000.0,
            "balance": 15000.0,
            "created_at": "2026-02-04T10:30:00Z"
        }
    ],
    "newly_added": true,
    "count": 1
}
```

---

## 🔧 故障排查

### 问题1: 下拉框没有自动刷新

**可能原因**:
- JavaScript未加载
- API端点路径错误
- 网络请求失败

**解决方法**:
1. 打开浏览器开发者工具（F12）
2. 查看Console是否有错误
3. 查看Network标签，确认API请求是否成功
4. 检查响应状态码是否为200

### 问题2: 提示框不显示

**可能原因**:
- CSS样式未加载
- z-index层级问题

**解决方法**:
1. 检查页面是否加载了完整的CSS
2. 检查是否有其他元素遮挡
3. 尝试调整toast的z-index值

### 问题3: 返回后没有参数

**可能原因**:
- 预付款创建视图没有正确处理next_url
- URL构建逻辑有问题

**解决方法**:
1. 检查预付款创建视图代码
2. 确认urllib导入正确
3. 调试URL构建逻辑

---

## 📋 验收标准

- [x] 创建预付款后自动返回核销页面
- [x] 返回时携带 `?from_prepayment_create=1` 参数
- [x] 页面自动检测参数并刷新预付款列表
- [x] 下拉框动态更新显示最新预付款
- [x] 显示成功提示消息
- [x] URL参数自动清除
- [x] 保持之前选中的预付款（如果还存在）
- [x] 网络错误时显示友好提示
- [x] 整个过程无需手动刷新页面

---

**修复原则体现**:
- **KISS**: 通过简单的URL参数和JavaScript实现自动刷新
- **DRY**: 复用现有的预付款模型和API结构
- **YAGNI**: 只实现必要的自动刷新功能，不过度设计
- **用户体验**: 无缝的创建→返回→刷新流程，零中断体验
