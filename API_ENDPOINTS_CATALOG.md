# Django ERP API 接口完整清单

> 项目: BetterLaser ERP
> API版本: v1
> 生成时间: 2025-01-24
> 认证方式: JWT + Session Authentication

---

## 🔐 认证接口 (Authentication)

### 用户认证
```
POST   /api/auth/login/                    # 用户登录
POST   /api/auth/logout/                   # 用户登出
POST   /api/auth/refresh/                  # 刷新JWT令牌
GET    /api/auth/user/                     # 获取当前用户信息
PUT    /api/auth/user/                     # 更新当前用户信息
POST   /api/auth/change-password/          # 修改密码
POST   /api/auth/reset-password/           # 重置密码
```

### 认证响应示例
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "系统管理员"
    },
    "permissions": ["view_sales_order", "add_sales_order"]
}
```

---

## 📊 核心接口 (Core Module)

### 系统配置
```
GET    /api/core/config/                   # 获取系统配置列表
POST   /api/core/config/                   # 创建配置项
GET    /api/core/config/{key}/             # 获取指定配置
PUT    /api/core/config/{key}/             # 更新配置项
DELETE /api/core/config/{key}/             # 删除配置项
```

### 通知管理
```
GET    /api/core/notifications/            # 获取通知列表
GET    /api/core/notifications/unread/      # 获取未读通知
POST   /api/core/notifications/            # 创建通知
GET    /api/core/notifications/{id}/        # 获取通知详情
PUT    /api/core/notifications/{id}/read/   # 标记为已读
DELETE /api/core/notifications/{id}/        # 删除通知
```

### 附件管理
```
GET    /api/core/attachments/              # 获取附件列表
POST   /api/core/attachments/              # 上传附件
GET    /api/core/attachments/{id}/          # 获取附件详情
DELETE /api/core/attachments/{id}/          # 删除附件
```

### 打印模板
```
GET    /api/core/templates/                # 获取模板列表
POST   /api/core/templates/                # 创建模板
GET    /api/core/templates/{id}/            # 获取模板详情
PUT    /api/core/templates/{id}/            # 更新模板
DELETE /api/core/templates/{id}/            # 删除模板
POST   /api/core/templates/{id}/preview/    # 预览模板
```

### 单据号生成
```
POST   /api/core/document-number/generate/ # 生成单据号
GET    /api/core/document-number/sequences/ # 获取单据号序列
```

---

## 🛒 销售管理接口 (Sales Module)

### 报价单管理
```
GET    /api/sales/quotes/                  # 获取报价单列表
POST   /api/sales/quotes/                  # 创建报价单
GET    /api/sales/quotes/{id}/              # 获取报价单详情
PUT    /api/sales/quotes/{id}/              # 更新报价单
DELETE /api/sales/quotes/{id}/              # 删除报价单
POST   /api/sales/quotes/{id}/convert/      # 转换为销售订单
POST   /api/sales/quotes/{id}/send/         # 发送报价单
```

### 销售订单管理
```
GET    /api/sales/orders/                  # 获取销售订单列表
POST   /api/sales/orders/                  # 创建销售订单
GET    /api/sales/orders/{id}/              # 获取销售订单详情
PUT    /api/sales/orders/{id}/              # 更新销售订单
DELETE /api/sales/orders/{id}/              # 删除销售订单
POST   /api/sales/orders/{id}/approve/      # 审核订单
POST   /api/sales/orders/{id}/unapprove/    # 撤销审核
POST   /api/sales/orders/{id}/complete/     # 完成订单
POST   /api/sales/orders/{id}/cancel/       # 取消订单
GET    /api/sales/orders/{id}/items/        # 获取订单明细
POST   /api/sales/orders/{id}/items/        # 添加订单明细
PUT    /api/sales/orders/{order_id}/items/{item_id}/ # 更新明细
DELETE /api/sales/orders/{order_id}/items/{item_id}/ # 删除明细
```

### 发货单管理
```
GET    /api/sales/deliveries/               # 获取发货单列表
POST   /api/sales/deliveries/               # 创建发货单
GET    /api/sales/deliveries/{id}/           # 获取发货单详情
PUT    /api/sales/deliveries/{id}/           # 更新发货单
DELETE /api/sales/deliveries/{id}/           # 删除发货单
POST   /api/sales/deliveries/{id}/ship/      # 确认发货
GET    /api/sales/deliveries/{id}/items/    # 获取发货明细
POST   /api/sales/deliveries/{id}/items/    # 添加发货明细
```

### 退货单管理
```
GET    /api/sales/returns/                  # 获取退货单列表
POST   /api/sales/returns/                  # 创建退货单
GET    /api/sales/returns/{id}/              # 获取退货单详情
PUT    /api/sales/returns/{id}/              # 更新退货单
DELETE /api/sales/returns/{id}/              # 删除退货单
POST   /api/sales/returns/{id}/approve/      # 审核退货
POST   /api/sales/returns/{id}/reject/       # 拒绝退货
POST   /api/sales/returns/{id}/receive/      # 确认收货
POST   /api/sales/returns/{id}/process/      # 处理退货
```

### 借用单管理
```
GET    /api/sales/loans/                    # 获取借用单列表
POST   /api/sales/loans/                    # 创建借用单
GET    /api/sales/loans/{id}/                # 获取借用单详情
PUT    /api/sales/loans/{id}/                # 更新借用单
DELETE /api/sales/loans/{id}/                # 删除借用单
POST   /api/sales/loans/{id}/approve/        # 审核借用
POST   /api/sales/loans/{id}/return/         # 借用归还
POST   /api/sales/loans/{id}/convert/        # 转为销售订单
```

### 销售统计
```
GET    /api/sales/statistics/               # 销售统计数据
GET    /api/sales/statistics/daily/         # 日销售统计
GET    /api/sales/statistics/monthly/       # 月销售统计
GET    /api/sales/reports/                   # 销售报表列表
GET    /api/sales/reports/sales-by-customer/ # 客户销售报表
GET    /api/sales/reports/sales-by-product/  # 产品销售报表
```

---

## 📦 采购管理接口 (Purchase Module)

### 采购申请
```
GET    /api/purchase/requests/              # 获取采购申请列表
POST   /api/purchase/requests/              # 创建采购申请
GET    /api/purchase/requests/{id}/          # 获取采购申请详情
PUT    /api/purchase/requests/{id}/          # 更新采购申请
DELETE /api/purchase/requests/{id}/          # 删除采购申请
POST   /api/purchase/requests/{id}/approve/  # 审核并转采购订单
POST   /api/purchase/requests/{id}/reject/   # 拒绝采购申请
GET    /api/purchase/requests/{id}/items/    # 获取申请明细
POST   /api/purchase/requests/{id}/items/    # 添加申请明细
```

### 采购询价
```
GET    /api/purchase/inquiries/             # 获取采购询价单列表
POST   /api/purchase/inquiries/             # 创建采购询价单
GET    /api/purchase/inquiries/{id}/         # 获取询价单详情
PUT    /api/purchase/inquiries/{id}/         # 更新询价单
DELETE /api/purchase/inquiries/{id}/         # 删除询价单
POST   /api/purchase/inquiries/{id}/send/    # 发送询价
POST   /api/purchase/inquiries/{id}/compare/ # 比价选择
```

### 采购订单
```
GET    /api/purchase/orders/                # 获取采购订单列表
POST   /api/purchase/orders/                # 创建采购订单
GET    /api/purchase/orders/{id}/            # 获取采购订单详情
PUT    /api/purchase/orders/{id}/            # 更新采购订单
DELETE /api/purchase/orders/{id}/            # 删除采购订单
POST   /api/purchase/orders/{id}/approve/    # 审核采购订单
POST   /api/purchase/orders/{id}/unapprove/  # 撤销审核
GET    /api/purchase/orders/{id}/items/      # 获取订单明细
POST   /api/purchase/orders/{id}/items/      # 添加订单明细
```

### 采购收货
```
GET    /api/purchase/receipts/              # 获取收货单列表
POST   /api/purchase/receipts/              # 创建收货单
GET    /api/purchase/receipts/{id}/          # 获取收货单详情
PUT    /api/purchase/receipts/{id}/          # 更新收货单
DELETE /api/purchase/receipts/{id}/          # 删除收货单
POST   /api/purchase/receipts/{id}/approve/  # 审核收货单
POST   /api/purchase/receipts/{id}/complete/ # 完成收货
GET    /api/purchase/receipts/{id}/items/    # 获取收货明细
POST   /api/purchase/receipts/{id}/items/    # 添加收货明细
```

### 采购退货
```
GET    /api/purchase/returns/               # 获取采购退货单列表
POST   /api/purchase/returns/               # 创建采购退货单
GET    /api/purchase/returns/{id}/           # 获取退货单详情
PUT    /api/purchase/returns/{id}/           # 更新退货单
DELETE /api/purchase/returns/{id}/           # 删除退货单
POST   /api/purchase/returns/{id}/approve/   # 审核退货单
POST   /api/purchase/returns/{id}/process/   # 处理退货
```

### 采购借用
```
GET    /api/purchase/borrow/                 # 获取采购借用单列表
POST   /api/purchase/borrow/                 # 创建采购借用单
GET    /api/purchase/borrow/{id}/             # 获取借用单详情
PUT    /api/purchase/borrow/{id}/             # 更新借用单
DELETE /api/purchase/borrow/{id}/             # 删除借用单
POST   /api/purchase/borrow/{id}/approve/     # 审核借用单
POST   /api/purchase/borrow/{id}/receipt/     # 确认收货
POST   /api/purchase/borrow/{id}/return/      # 借用归还
POST   /api/purchase/borrow/{id}/convert/     # 转为采购订单
```

### 采购统计
```
GET    /api/purchase/statistics/            # 采购统计数据
GET    /api/purchase/reports/                # 采购报表列表
GET    /api/purchase/reports/by-supplier/    # 供应商采购报表
GET    /api/purchase/reports/by-product/     # 产品采购报表
```

---

## 🏪 库存管理接口 (Inventory Module)

### 仓库管理
```
GET    /api/inventory/warehouses/            # 获取仓库列表
POST   /api/inventory/warehouses/            # 创建仓库
GET    /api/inventory/warehouses/{id}/        # 获取仓库详情
PUT    /api/inventory/warehouses/{id}/        # 更新仓库
DELETE /api/inventory/warehouses/{id}/        # 删除仓库
GET    /api/inventory/warehouses/{id}/locations/ # 获取仓库库位
POST   /api/inventory/warehouses/{id}/locations/ # 创建库位
```

### 库存台账
```
GET    /api/inventory/stocks/                # 获取库存台账列表
GET    /api/inventory/stocks/{id}/            # 获取库存详情
PUT    /api/inventory/stocks/{id}/            # 更新库存
GET    /api/inventory/stocks/alerts/         # 获取库存预警
GET    /api/inventory/stocks/transactions/   # 获取库存交易记录
POST   /api/inventory/stocks/adjust/         # 库存调整
```

### 入库管理
```
GET    /api/inventory/inbound/               # 获取入库单列表
POST   /api/inventory/inbound/               # 创建入库单
GET    /api/inventory/inbound/{id}/           # 获取入库单详情
PUT    /api/inventory/inbound/{id}/           # 更新入库单
DELETE /api/inventory/inbound/{id}/           # 删除入库单
POST   /api/inventory/inbound/{id}/approve/   # 审核入库单
POST   /api/inventory/inbound/{id}/complete/  # 完成入库
GET    /api/inventory/inbound/{id}/items/     # 获取入库明细
POST   /api/inventory/inbound/{id}/items/     # 添加入库明细
```

### 出库管理
```
GET    /api/inventory/outbound/              # 获取出库单列表
POST   /api/inventory/outbound/              # 创建出库单
GET    /api/inventory/outbound/{id}/          # 获取出库单详情
PUT    /api/inventory/outbound/{id}/          # 更新出库单
DELETE /api/inventory/outbound/{id}/          # 删除出库单
POST   /api/inventory/outbound/{id}/approve/  # 审核出库单
POST   /api/inventory/outbound/{id}/complete/ # 完成出库
GET    /api/inventory/outbound/{id}/items/    # 获取出库明细
POST   /api/inventory/outbound/{id}/items/    # 添加出库明细
```

### 库存调拨
```
GET    /api/inventory/transfers/             # 获取调拨单列表
POST   /api/inventory/transfers/             # 创建调拨单
GET    /api/inventory/transfers/{id}/         # 获取调拨单详情
PUT    /api/inventory/transfers/{id}/         # 更新调拨单
DELETE /api/inventory/transfers/{id}/         # 删除调拨单
POST   /api/inventory/transfers/{id}/approve/ # 审核调拨单
POST   /api/inventory/transfers/{id}/ship/    # 确认发货
POST   /api/inventory/transfers/{id}/receive/ # 确认收货
GET    /api/inventory/transfers/{id}/items/   # 获取调拨明细
POST   /api/inventory/transfers/{id}/items/   # 添加调拨明细
```

### 库存盘点
```
GET    /api/inventory/counts/                # 获取盘点单列表
POST   /api/inventory/counts/                # 创建盘点单
GET    /api/inventory/counts/{id}/            # 获取盘点单详情
PUT    /api/inventory/counts/{id}/            # 更新盘点单
DELETE /api/inventory/counts/{id}/            # 删除盘点单
POST   /api/inventory/counts/{id}/start/      # 开始盘点
POST   /api/inventory/counts/{id}/complete/   # 完成盘点
GET    /api/inventory/counts/{id}/items/      # 获取盘点明细
POST   /api/inventory/counts/{id}/items/      # 添加盘点明细
```

### 库存调整
```
GET    /api/inventory/adjustments/           # 获取调整单列表
POST   /api/inventory/adjustments/           # 创建调整单
GET    /api/inventory/adjustments/{id}/       # 获取调整单详情
PUT    /api/inventory/adjustments/{id}/       # 更新调整单
DELETE /api/inventory/adjustments/{id}/       # 删除调整单
POST   /api/inventory/adjustments/{id}/approve/ # 审核调整单
```

### 库存统计
```
GET    /api/inventory/statistics/            # 库存统计数据
GET    /api/inventory/statistics/summary/    # 库存汇总
GET    /api/inventory/statistics/movement/   # 库存变动统计
GET    /api/inventory/reports/                # 库存报表列表
GET    /api/inventory/reports/stock-alert/    # 库存预警报表
GET    /api/inventory/reports/stock-value/    # 库存价值报表
```

---

## 💰 财务管理接口 (Finance Module)

### 应收账款
```
GET    /api/finance/customer-accounts/       # 获取应收账款列表
POST   /api/finance/customer-accounts/       # 创建应收账款
GET    /api/finance/customer-accounts/{id}/   # 获取应收账款详情
PUT    /api/finance/customer-accounts/{id}/   # 更新应收账款
GET    /api/finance/customer-accounts/{id}/payments/ # 获取收款记录
POST   /api/finance/customer-accounts/{id}/payment/   # 记录收款
POST   /api/finance/customer-accounts/{id}/writeoff/  # 核销账款
GET    /api/finance/customer-accounts/aging/  # 账龄分析
```

### 应付账款
```
GET    /api/finance/supplier-accounts/       # 获取应付账款列表
POST   /api/finance/supplier-accounts/       # 创建应付账款
GET    /api/finance/supplier-accounts/{id}/   # 获取应付账款详情
PUT    /api/finance/supplier-accounts/{id}/   # 更新应付账款
GET    /api/finance/supplier-accounts/{id}/payments/ # 获取付款记录
POST   /api/finance/supplier-accounts/{id}/payment/   # 记录付款
POST   /api/finance/supplier-accounts/{id}/allocate/  # 分配付款
POST   /api/finance/supplier-accounts/{id}/writeoff/  # 核销账款
GET    /api/finance/supplier-accounts/aging/  # 账龄分析
```

### 预付款管理
```
GET    /api/finance/customer-prepayments/    # 获取客户预付款列表
POST   /api/finance/customer-prepayments/    # 创建客户预付款
GET    /api/finance/customer-prepayments/{id}/ # 获取预付款详情
PUT    /api/finance/customer-prepayments/{id}/ # 更新预付款
DELETE /api/finance/customer-prepayments/{id}/ # 删除预付款

GET    /api/finance/supplier-prepayments/    # 获取供应商预付款列表
POST   /api/finance/supplier-prepayments/    # 创建供应商预付款
GET    /api/finance/supplier-prepayments/{id}/ # 获取预付款详情
PUT    /api/finance/supplier-prepayments/{id}/ # 更新预付款
DELETE /api/finance/supplier-prepayments/{id}/ # 删除预付款
```

### 发票管理
```
GET    /api/finance/invoices/                # 获取发票列表
POST   /api/finance/invoices/                # 创建发票
GET    /api/finance/invoices/{id}/            # 获取发票详情
PUT    /api/finance/invoices/{id}/            # 更新发票
DELETE /api/finance/invoices/{id}/            # 删除发票
POST   /api/finance/invoices/{id}/verify/     # 验证发票
POST   /api/finance/invoices/{id}/void/       # 作废发票
GET    /api/finance/invoices/{id}/items/      # 获取发票明细
POST   /api/finance/invoices/{id}/items/      # 添加发票明细
```

### 费用管理
```
GET    /api/finance/expenses/                # 获取费用报销列表
POST   /api/finance/expenses/                # 创建费用报销
GET    /api/finance/expenses/{id}/            # 获取费用报销详情
PUT    /api/finance/expenses/{id}/            # 更新费用报销
DELETE /api/finance/expenses/{id}/            # 删除费用报销
POST   /api/finance/expenses/{id}/submit/     # 提交报销
POST   /api/finance/expenses/{id}/approve/    # 审核报销
POST   /api/finance/expenses/{id}/reject/     # 拒绝报销
POST   /api/finance/expenses/{id}/pay/        # 支付报销
```

### 记账凭证
```
GET    /api/finance/journals/                # 获取记账凭证列表
POST   /api/finance/journals/                # 创建记账凭证
GET    /api/finance/journals/{id}/            # 获取凭证详情
PUT    /api/finance/journals/{id}/            # 更新凭证
DELETE /api/finance/journals/{id}/            # 删除凭证
POST   /api/finance/journals/{id}/post/       # 凭证过账
POST   /api/finance/journals/{id}/cancel/     # 凭证作废
GET    /api/finance/journals/{id}/entries/    # 获取凭证分录
POST   /api/finance/journals/{id}/entries/    # 添加凭证分录
```

### 会计科目
```
GET    /api/finance/accounts/                # 获取会计科目列表
POST   /api/finance/accounts/                # 创建会计科目
GET    /api/finance/accounts/{id}/            # 获取科目详情
PUT    /api/finance/accounts/{id}/            # 更新科目
DELETE /api/finance/accounts/{id}/            # 删除科目
GET    /api/finance/accounts/tree/            # 获取科目树
GET    /api/finance/accounts/{id}/balance/    # 获取科目余额
```

### 财务报表
```
GET    /api/finance/reports/                 # 获取财务报表列表
GET    /api/finance/reports/trial-balance/   # 试算平衡表
GET    /api/finance/reports/income-statement/# 利润表
GET    /api/finance/reports/balance-sheet/   # 资产负债表
GET    /api/finance/reports/cash-flow/       # 现金流量表
POST   /api/finance/reports/generate/        # 生成自定义报表
```

---

## 🏭 产品管理接口 (Products Module)

### 产品管理
```
GET    /api/products/products/               # 获取产品列表
POST   /api/products/products/               # 创建产品
GET    /api/products/products/{id}/           # 获取产品详情
PUT    /api/products/products/{id}/           # 更新产品
DELETE /api/products/products/{id}/           # 删除产品
GET    /api/products/products/{id}/images/    # 获取产品图片
POST   /api/products/products/{id}/images/    # 上传产品图片
GET    /api/products/products/{id}/attributes/# 获取产品属性
POST   /api/products/products/{id}/attributes/# 添加产品属性
GET    /api/products/products/{id}/price-history/ # 获取价格历史
```

### 产品分类
```
GET    /api/products/categories/             # 获取产品分类列表
POST   /api/products/categories/             # 创建产品分类
GET    /api/products/categories/{id}/         # 获取分类详情
PUT    /api/products/categories/{id}/         # 更新分类
DELETE /api/products/categories/{id}/         # 删除分类
GET    /api/products/categories/tree/         # 获取分类树
GET    /api/products/categories/{id}/products/# 获取分类下的产品
```

### 品牌管理
```
GET    /api/products/brands/                 # 获取品牌列表
POST   /api/products/brands/                 # 创建品牌
GET    /api/products/brands/{id}/             # 获取品牌详情
PUT    /api/products/brands/{id}/             # 更新品牌
DELETE /api/products/brands/{id}/             # 删除品牌
```

### 计量单位
```
GET    /api/products/units/                  # 获取计量单位列表
POST   /api/products/units/                  # 创建计量单位
GET    /api/products/units/{id}/              # 获取单位详情
PUT    /api/products/units/{id}/              # 更新单位
DELETE /api/products/units/{id}/              # 删除单位
GET    /api/products/units/default/           # 获取默认单位
```

---

## 👥 客户管理接口 (Customers Module)

### 客户管理
```
GET    /api/customers/customers/             # 获取客户列表
POST   /api/customers/customers/             # 创建客户
GET    /api/customers/customers/{id}/         # 获取客户详情
PUT    /api/customers/customers/{id}/         # 更新客户
DELETE /api/customers/customers/{id}/         # 删除客户
GET    /api/customers/customers/{id}/contacts/# 获取客户联系人
POST   /api/customers/customers/{id}/contacts/# 添加联系人
GET    /api/customers/customers/{id}/accounts/ # 获取客户账款
GET    /api/customers/customers/{id}/orders/   # 获取客户订单
```

### 客户统计
```
GET    /api/customers/statistics/            # 客户统计数据
GET    /api/customers/reports/                # 客户报表列表
GET    /api/customers/reports/sales-by-customer/ # 客户销售分析
```

---

## 🏢 供应商管理接口 (Suppliers Module)

### 供应商管理
```
GET    /api/suppliers/suppliers/             # 获取供应商列表
POST   /api/suppliers/suppliers/             # 创建供应商
GET    /api/suppliers/suppliers/{id}/         # 获取供应商详情
PUT    /api/suppliers/suppliers/{id}/         # 更新供应商
DELETE /api/suppliers/suppliers/{id}/         # 删除供应商
GET    /api/suppliers/suppliers/{id}/contacts/# 获取供应商联系人
POST   /api/suppliers/suppliers/{id}/contacts/# 添加联系人
GET    /api/suppliers/suppliers/{id}/accounts/ # 获取供应商账款
GET    /api/suppliers/suppliers/{id}/orders/   # 获取供应商订单
```

### 供应商统计
```
GET    /api/suppliers/statistics/            # 供应商统计数据
GET    /api/suppliers/reports/                # 供应商报表列表
GET    /api/suppliers/reports/purchase-by-supplier/ # 供应商采购分析
```

---

## 👤 用户管理接口 (Users Module)

### 用户管理
```
GET    /api/users/users/                     # 获取用户列表
POST   /api/users/users/                     # 创建用户
GET    /api/users/users/{id}/                 # 获取用户详情
PUT    /api/users/users/{id}/                 # 更新用户
DELETE /api/users/users/{id}/                 # 删除用户
POST   /api/users/users/{id}/change-password/# 修改用户密码
POST   /api/users/users/{id}/reset-password/  # 重置用户密码
GET    /api/users/users/{id}/permissions/     # 获取用户权限
POST   /api/users/users/{id}/permissions/     # 设置用户权限
```

### 角色管理
```
GET    /api/users/roles/                     # 获取角色列表
POST   /api/users/roles/                     # 创建角色
GET    /api/users/roles/{id}/                 # 获取角色详情
PUT    /api/users/roles/{id}/                 # 更新角色
DELETE /api/users/roles/{id}/                 # 删除角色
GET    /api/users/roles/{id}/permissions/     # 获取角色权限
POST   /api/users/roles/{id}/permissions/     # 设置角色权限
GET    /api/users/roles/{id}/users/           # 获取角色用户
POST   /api/users/roles/{id}/users/           # 添加角色用户
DELETE /api/users/roles/{role_id}/users/{user_id}/ # 移除角色用户
```

### 权限管理
```
GET    /api/users/permissions/               # 获取权限列表
GET    /api/users/permissions/{id}/           # 获取权限详情
GET    /api/users/permissions/tree/           # 获取权限树
```

### 登录日志
```
GET    /api/users/login-logs/                # 获取登录日志
GET    /api/users/login-logs/{id}/            # 获取日志详情
```

---

## 🏢 组织架构接口 (Departments Module)

### 部门管理
```
GET    /api/departments/departments/         # 获取部门列表
POST   /api/departments/departments/         # 创建部门
GET    /api/departments/departments/{id}/     # 获取部门详情
PUT    /api/departments/departments/{id}/     # 更新部门
DELETE /api/departments/departments/{id}/     # 删除部门
GET    /api/departments/departments/tree/     # 获取部门树
GET    /api/departments/departments/{id}/users/ # 获取部门用户
GET    /api/departments/departments/{id}/positions/ # 获取部门岗位
```

### 岗位管理
```
GET    /api/departments/positions/            # 获取岗位列表
POST   /api/departments/positions/            # 创建岗位
GET    /api/departments/positions/{id}/        # 获取岗位详情
PUT    /api/departments/positions/{id}/        # 更新岗位
DELETE /api/departments/positions/{id}/        # 删除岗位
GET    /api/departments/positions/{id}/users/  # 获取岗位用户
```

### 预算管理
```
GET    /api/departments/budgets/              # 获取预算列表
POST   /api/departments/budgets/              # 创建预算
GET    /api/departments/budgets/{id}/          # 获取预算详情
PUT    /api/departments/budgets/{id}/          # 更新预算
DELETE /api/departments/budgets/{id}/          # 删除预算
GET    /api/departments/budgets/{id}/actuals/  # 获取实际支出
```

---

## 🤖 AI助手接口 (AI Assistant Module)

### AI配置管理
```
GET    /api/ai/model-configs/                # 获取AI模型配置列表
POST   /api/ai/model-configs/                # 创建AI模型配置
GET    /api/ai/model-configs/{id}/            # 获取配置详情
PUT    /api/ai/model-configs/{id}/            # 更新配置
DELETE /api/ai/model-configs/{id}/            # 删除配置
POST   /api/ai/model-configs/{id}/test/       # 测试配置
POST   /api/ai/model-configs/{id}/set-default/ # 设为默认
```

### AI对话管理
```
GET    /api/ai/conversations/                # 获取对话列表
POST   /api/ai/conversations/                # 创建对话
GET    /api/ai/conversations/{id}/            # 获取对话详情
DELETE /api/ai/conversations/{id}/            # 删除对话
GET    /api/ai/conversations/{id}/messages/   # 获取对话消息
POST   /api/ai/conversations/{id}/messages/   # 发送消息
DELETE /api/ai/conversations/{id}/messages/{message_id}/ # 删除消息
```

### ERP工具管理
```
GET    /api/ai/tools/                        # 获取ERP工具列表
POST   /api/ai/tools/                        # 创建ERP工具
GET    /api/ai/tools/{id}/                    # 获取工具详情
PUT    /api/ai/tools/{id}/                    # 更新工具
DELETE /api/ai/tools/{id}/                    # 删除工具
GET    /api/ai/tools/categories/              # 获取工具分类
GET    /api/ai/tools/execution-logs/          # 获取工具执行日志
```

### 渠道配置
```
GET    /api/ai/channels/wechat/               # 获取微信配置
PUT    /api/ai/channels/wechat/               # 更新微信配置
GET    /api/ai/channels/dingtalk/             # 获取钉钉配置
PUT    /api/ai/channels/dingtalk/             # 更新钉钉配置
GET    /api/ai/channels/telegram/             # 获取Telegram配置
PUT    /api/ai/channels/telegram/             # 更新Telegram配置
```

---

## 📋 通用查询参数

### 分页参数
```
?page=1&page_size=20
```

### 排序参数
```
?ordering=-created_at      # 按创建时间倒序
?ordering=name,created_at  # 多字段排序
```

### 过滤参数
```
?status=confirmed                    # 精确匹配
?customer__name__icontains=激光      # 模糊搜索
?created_at__gte=2025-01-01          # 范围查询
?created_at__lte=2025-12-31
```

### 搜索参数
```
?search=激光设备                     # 全文搜索
```

---

## 📤 标准响应格式

### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": 1,
        "name": "示例数据"
    }
}
```

### 列表响应
```json
{
    "success": true,
    "count": 100,
    "next": "/api/sales/orders/?page=2",
    "previous": null,
    "results": [
        {"id": 1, "name": "示例数据1"},
        {"id": 2, "name": "示例数据2"}
    ]
}
```

### 错误响应
```json
{
    "success": false,
    "message": "操作失败",
    "errors": {
        "field_name": ["错误信息1", "错误信息2"]
    }
}
```

---

## 🔒 权限说明

### 权限格式
```
{app}.{action}_{model}

示例:
sales.view_salesorder     # 查看销售订单
sales.add_salesorder      # 创建销售订单
sales.change_salesorder   # 修改销售订单
sales.delete_salesorder   # 删除销售订单
```

### 权限检查
```python
# 在ViewSet中
permission_classes = [IsAuthenticated]
# 具体权限在模型层面检查
```

---

## 🌐 跨域配置

### CORS设置
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
```

---

## 📊 API使用统计

### 接口分类统计
- 认证接口: 8个
- 核心接口: 20+个
- 销售管理: 50+个
- 采购管理: 45+个
- 库存管理: 40+个
- 财务管理: 60+个
- 产品管理: 25+个
- 客户管理: 15+个
- 供应商管理: 15+个
- 用户管理: 20+个
- 组织架构: 20+个
- AI助手: 25+个

**总计**: 350+ 个API接口

---

## 📝 开发建议

### API文档生成
```bash
# 安装 drf-yasg
pip install drf-yasg

# 添加到 settings.py
INSTALLED_APPS += ['drf_yasg']

# 访问文档
http://your-domain.com/swagger/
http://your-domain.com/redoc/
```

### API版本控制
```python
# 建议添加版本控制
urlpatterns = [
    path('api/v1/', include(v1_urls)),
    path('api/v2/', include(v2_urls)),
]
```

### 限流控制
```python
# 添加限流
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```

---

**文档版本**: v1.0
**API版本**: v1
**生成时间**: 2025-01-24
**维护状态**: 🟢 活跃开发中