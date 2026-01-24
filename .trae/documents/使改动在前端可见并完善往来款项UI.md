## 问题核查结果

* 后端改动已存在：

  * `apps/sales/models.py:480–527` 已设置报价转订单的默认日期与+15天交期；`templates/sales/delivery_confirm_ship.html:33–44` 承运商默认“顺丰速运”；发货确认时生成发票与应收在 `apps/sales/views.py:1156–1282`。

  * 财务路由已聚焦到应收、应付、预收/预付与报表：`apps/finance/urls.py:12–73`。

  * 新增模型：`apps/finance/models.py:471–520` 定义 `CustomerPrepayment`、`SupplierPrepayment`。

* 但前端仍显示“财务管理”，并含“会计科目/记账凭证/预算管理”菜单：`templates/base.html:857–891`、`templates/reports/finance_reports.html:2–23` 等。

* 预收/预付与核销相关模板缺失：未找到 `templates/finance/customer_prepayment_*`、`supplier_prepayment_*`、`*writeoff.html`，导致功能不可见。

* 迁移未生成：`apps/finance/migrations/` 中无针对预收/预付的新迁移文件，数据库尚未包含新表。

## 拟实施改动

1. 更新全局导航与标签

* 将侧边栏“财务管理”统一改为“往来款项”，更新折叠菜单与悬浮菜单两处：`templates/base.html`。

* 移除“会计科目/记账凭证/预算管理”菜单项及相关的模块代码；新增“预收款”(`/finance/prepayments/customer/`)与“预付款”(`/finance/prepayments/supplier/`)菜单项及功能。

* 报表入口改为“往来报表”，指向 `finance:arap_summary_report`。

1. 统一面包屑与页面标题

* 在 `templates/reports/finance_reports.html`、`templates/finance/*`（仪表盘、应收/应付详情与列表、收付款详情）中，将“财务管理/财务报表”等字样替换为“往来款项/往来报表”，并保持 `{% block breadcrumb %}` 一致规范。

1. 补齐预收/预付与核销的前端模板

* 新增：

  * `templates/finance/customer_prepayment_list.html`、`customer_prepayment_form.html`。

  * `templates/finance/supplier_prepayment_list.html`、`supplier_prepayment_form.html`。

  * `templates/finance/customer_account_writeoff.html`、`supplier_account_writeoff.html`。

* 模板遵循现有列表/表单样式，挂载到现有路由与视图（`apps/finance/views.py`）。

1. 生成并应用数据库迁移

* 为 `CustomerPrepayment`、`SupplierPrepayment` 生成迁移，执行 `makemigrations apps.finance && migrate`，确保新表可用。

1. 销售模块可见性微调（如必要）

* 若“创建退货单”按钮受状态限制过严，按流程允许在订单进入 `shipped/delivered/completed` 时显示：`templates/sales/order_detail.html:68–71` 已存在，确认逻辑即可。

* 若承运商未被提交时为空，后端默认值调整为“顺丰速运”（`apps/sales/views.py` 设置 POST 默认值）。

## 验证方案

* 手动浏览左侧菜单与面包屑，确认“往来款项”与子菜单显示正确，旧菜单已移除。

* 进入“预收款/预付款”列表与创建页，完成一次创建并在数据库中查到记录；在应收/应付详情页执行手动核销，验证预收/预付可参与核销。

* 在销售流程中：报价→订单（默认日期/交期），订单确认生成发货单，确认发货后生成发票与应收；在订单页显示“创建退货单”并能创建退货。

## 运行与发布

* 执行迁移；若使用静态文件缓存，运行 `collectstatic` 并重启服务以加载模板更新。

## 风险与回滚

* 菜单项移除会使旧路径不可达；保留后端路由最小集，若需回滚，仅恢复 `templates/base.html` 的旧菜单与标签即可。

