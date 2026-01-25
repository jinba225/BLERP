# Django ERP 数据库设计详细分析

> 项目: BetterLaser ERP
> 生成时间: 2025-01-24
> 数据库: SQLite (开发) / MySQL (生产)

---

## 📊 数据库架构概览

### 表统计
```
总表数: 80+ 个业务表
总字段: 500+ 个字段
总索引: 150+ 个索引
总关系: 200+ 个外键关系
```

### 设计原则
1. **统一基类**: 所有业务表继承 BaseModel
2. **软删除**: 支持逻辑删除，保留数据完整性
3. **审计追踪**: 自动记录创建人、修改人、时间戳
4. **含税价格**: 财务相关字段采用含税价格体系
5. **国际化友好**: 支持多币种、多税率

---

## 🗃️ 核心表结构分析

### 1. 基础数据表 (Core Module)

#### company (公司信息表)
```sql
CREATE TABLE core_company (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,           -- 公司名称
    code VARCHAR(50) UNIQUE NOT NULL,     -- 公司代码
    legal_representative VARCHAR(100),    -- 法定代表人
    registration_number VARCHAR(100),     -- 注册号
    tax_number VARCHAR(100),              -- 税号
    address TEXT,                         -- 地址
    phone VARCHAR(50),                    -- 电话
    fax VARCHAR(50),                      -- 传真
    email VARCHAR(254),                   -- 邮箱
    website VARCHAR(200),                 -- 网站
    logo VARCHAR(100),                    -- Logo路径
    description TEXT,                     -- 公司描述
    is_active BOOLEAN DEFAULT TRUE,       -- 是否启用
    created_at DATETIME,                  -- 创建时间
    updated_at DATETIME,                  -- 更新时间
    created_by_id BIGINT,                 -- 创建人
    updated_by_id BIGINT,                 -- 更新人
    is_deleted BOOLEAN DEFAULT FALSE,     -- 是否删除
    deleted_at DATETIME,                  -- 删除时间
    deleted_by_id BIGINT                  -- 删除人
);
```

#### system_config (系统配置表)
```sql
CREATE TABLE core_system_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,     -- 配置键
    value TEXT NOT NULL,                  -- 配置值
    config_type VARCHAR(20),              -- 配置类型: system/business/ui/security
    description TEXT,                     -- 描述
    is_active BOOLEAN DEFAULT TRUE,       -- 是否启用
    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT
);

-- 常用配置项
INSERT INTO core_system_config (key, value, config_type) VALUES
('document_prefix_sales_order', 'SO', 'business'),
('document_prefix_quotation', 'SQ', 'business'),
('document_prefix_delivery', 'OUT', 'business'),
('document_number_date_format', 'YYMMDD', 'business'),
('document_number_sequence_digits', '3', 'business'),
('sales_auto_create_delivery_on_approve', 'true', 'business');
```

#### document_number_sequence (单据号序列表)
```sql
CREATE TABLE core_document_number_sequence (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    prefix VARCHAR(10) NOT NULL,          -- 单据前缀
    date_str VARCHAR(8) NOT NULL,         -- 日期字符串: YYYYMMDD
    current_number INT DEFAULT 0,         -- 当前序号
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE KEY unique_prefix_date (prefix, date_str)
);

-- 示例数据
-- prefix='SO', date_str='20250124', current_number=5
-- 生成单据号: SO20250124006
```

#### audit_log (审计日志表)
```sql
CREATE TABLE core_audit_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,                       -- 操作用户
    action VARCHAR(20) NOT NULL,          -- 操作类型: create/update/delete/login...
    model_name VARCHAR(100),              -- 模型名称
    object_id VARCHAR(100),               -- 对象ID
    object_repr VARCHAR(200),             -- 对象描述
    changes JSON,                         -- 变更内容
    ip_address VARCHAR(45),               -- IP地址
    user_agent TEXT,                      -- 用户代理
    timestamp DATETIME NOT NULL,          -- 时间戳
    INDEX idx_user_action (user_id, action),
    INDEX idx_timestamp (timestamp)
);
```

#### notification (系统通知表)
```sql
CREATE TABLE core_notification (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recipient_id BIGINT NOT NULL,         -- 接收人
    title VARCHAR(200) NOT NULL,          -- 标题
    message TEXT NOT NULL,                -- 消息内容
    notification_type VARCHAR(20),        -- 类型: info/success/warning/error
    category VARCHAR(30),                 -- 分类: sales_return/sales_order/inventory...
    reference_type VARCHAR(50),           -- 关联类型
    reference_id VARCHAR(100),            -- 关联ID
    reference_url VARCHAR(500),           -- 关联链接
    is_read BOOLEAN DEFAULT FALSE,        -- 是否已读
    read_at DATETIME,                     -- 阅读时间
    created_at DATETIME,
    INDEX idx_recipient_read (recipient_id, is_read, created_at),
    INDEX idx_category (category, created_at)
);
```

---

### 2. 销售管理表 (Sales Module)

#### sales_order (销售订单表)
```sql
CREATE TABLE sales_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(100) UNIQUE NOT NULL,  -- 订单号: SO20250124001
    customer_id BIGINT NOT NULL,                -- 客户ID
    status VARCHAR(20) DEFAULT 'draft',         -- 状态: draft/pending/confirmed/...
    payment_status VARCHAR(20) DEFAULT 'unpaid',-- 付款状态
    invoice_status VARCHAR(20) DEFAULT 'not_invoiced', -- 开票状态

    -- 日期信息
    order_date DATE NOT NULL,                   -- 订单日期
    required_date DATE,                         -- 要求交期
    promised_date DATE,                         -- 承诺交期
    shipped_date DATE,                          -- 发货日期

    -- 销售信息
    sales_rep_id BIGINT,                        -- 销售代表

    -- 金额信息 (含税体系)
    subtotal DECIMAL(12,2) DEFAULT 0,           -- 含税小计
    tax_rate DECIMAL(5,2) DEFAULT 13,           -- 税率(%)
    tax_amount DECIMAL(12,2) DEFAULT 0,          -- 税额(反推)
    discount_rate DECIMAL(5,2) DEFAULT 0,        -- 折扣率(%)
    discount_amount DECIMAL(12,2) DEFAULT 0,     -- 折扣金额
    shipping_cost DECIMAL(12,2) DEFAULT 0,       -- 含税运费
    total_amount DECIMAL(12,2) DEFAULT 0,        -- 含税总金额
    currency VARCHAR(10) DEFAULT 'CNY',         -- 币种

    -- 收货信息
    shipping_address TEXT,                      -- 收货地址
    shipping_contact VARCHAR(100),              -- 收货联系人
    shipping_phone VARCHAR(20),                 -- 收货电话
    shipping_method VARCHAR(100),               -- 配送方式
    tracking_number VARCHAR(100),               -- 快递单号

    -- 付款条件
    payment_terms VARCHAR(50),                  -- 付款方式

    -- 附加信息
    reference_number VARCHAR(100),              -- 客户订单号
    notes TEXT,                                -- 备注
    internal_notes TEXT,                        -- 内部备注

    -- 审核信息
    approved_by_id BIGINT,                      -- 审核人
    approved_at DATETIME,                       -- 审核时间

    -- 基础字段
    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    FOREIGN KEY (sales_rep_id) REFERENCES users_user(id),
    INDEX idx_customer_status (customer_id, status),
    INDEX idx_order_date (order_date),
    INDEX idx_status (status)
);
```

#### sales_order_item (销售订单明细表)
```sql
CREATE TABLE sales_order_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,                  -- 订单ID
    product_id BIGINT NOT NULL,                -- 产品ID
    quantity INT NOT NULL,                     -- 数量
    unit_price DECIMAL(12,2) NOT NULL,         -- 含税单价
    discount_rate DECIMAL(5,2) DEFAULT 0,      -- 折扣率(%)
    discount_amount DECIMAL(12,2) DEFAULT 0,   -- 折扣金额
    line_total DECIMAL(12,2) DEFAULT 0,        -- 含税小计

    -- 交付信息
    delivered_quantity INT DEFAULT 0,          -- 已交付数量
    required_date DATE,                        -- 要求交期

    -- 生产信息
    produced_quantity INT DEFAULT 0,           -- 已生产数量

    notes TEXT,                                -- 备注
    sort_order INT DEFAULT 0,                  -- 排序

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (order_id) REFERENCES sales_order(id),
    FOREIGN KEY (product_id) REFERENCES products_product(id),
    INDEX idx_order_product (order_id, product_id)
);
```

#### quote (销售报价表)
```sql
CREATE TABLE sales_quote (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    quote_number VARCHAR(100) UNIQUE NOT NULL, -- 报价单号: SQ20250124001
    quote_type VARCHAR(20) DEFAULT 'domestic', -- 报价类型: domestic/overseas
    customer_id BIGINT NOT NULL,               -- 客户ID
    contact_person_id BIGINT,                  -- 联系人ID
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/sent/accepted/rejected...

    -- 日期信息
    quote_date DATE NOT NULL,                  -- 报价日期
    valid_until DATE NOT NULL,                 -- 有效期至

    -- 销售信息
    sales_rep_id BIGINT,                       -- 销售代表

    -- 金额信息 (含税体系)
    currency VARCHAR(10) DEFAULT 'CNY',        -- 币种
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000, -- 汇率
    subtotal DECIMAL(12,2) DEFAULT 0,          -- 含税小计
    tax_rate DECIMAL(5,2) DEFAULT 13,          -- 税率(%)
    tax_amount DECIMAL(12,2) DEFAULT 0,         -- 税额(反推)
    discount_rate DECIMAL(5,2) DEFAULT 0,      -- 折扣率(%)
    discount_amount DECIMAL(12,2) DEFAULT 0,   -- 折扣金额
    total_amount DECIMAL(12,2) DEFAULT 0,      -- 含税总金额
    total_amount_cny DECIMAL(12,2) DEFAULT 0,  -- 总金额(CNY)

    -- 条款信息
    payment_terms VARCHAR(50),                 -- 付款方式
    delivery_terms VARCHAR(200),               -- 交货条件
    warranty_terms TEXT,                       -- 质保条款

    -- 附加信息
    reference_number VARCHAR(100),             -- 客户询价号
    notes TEXT,                                -- 备注

    -- 转换信息
    converted_order_id BIGINT,                 -- 转换的订单ID

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    FOREIGN KEY (converted_order_id) REFERENCES sales_order(id),
    INDEX idx_customer_status (customer_id, status),
    INDEX idx_quote_date (quote_date)
);
```

#### delivery (发货单表)
```sql
CREATE TABLE sales_delivery (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    delivery_number VARCHAR(100) UNIQUE NOT NULL, -- 发货单号: OUT20250124001
    sales_order_id BIGINT NOT NULL,                 -- 销售订单ID
    status VARCHAR(20) DEFAULT 'preparing',         -- 状态: preparing/ready/shipped...

    -- 日期信息
    planned_date DATE NOT NULL,                     -- 计划发货日期
    actual_date DATE,                               -- 实际发货日期
    delivered_date DATE,                            -- 送达日期

    -- 收货信息
    shipping_address TEXT NOT NULL,                 -- 收货地址
    shipping_contact VARCHAR(100) NOT NULL,         -- 收货联系人
    shipping_phone VARCHAR(20) NOT NULL,            -- 收货电话
    shipping_method VARCHAR(100),                   -- 配送方式
    carrier VARCHAR(100),                           -- 承运商
    tracking_number VARCHAR(100),                   -- 快递单号

    -- 仓库信息
    warehouse_id BIGINT NOT NULL,                   -- 发货仓库ID

    -- 人员信息
    prepared_by_id BIGINT,                          -- 备货人
    shipped_by_id BIGINT,                           -- 发货人

    notes TEXT,                                     -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (sales_order_id) REFERENCES sales_order(id),
    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    INDEX idx_order_status (sales_order_id, status),
    INDEX idx_planned_date (planned_date)
);
```

#### sales_return (销售退货表)
```sql
CREATE TABLE sales_return (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    return_number VARCHAR(100) UNIQUE NOT NULL,  -- 退货单号: SR20250124001
    sales_order_id BIGINT NOT NULL,              -- 原销售订单ID
    delivery_id BIGINT,                          -- 原发货单ID
    status VARCHAR(20) DEFAULT 'pending',        -- 状态: pending/approved/received...
    reason VARCHAR(20) NOT NULL,                 -- 退货原因: defective/wrong_item/damaged...

    -- 日期信息
    return_date DATE NOT NULL,                   -- 退货日期
    received_date DATE,                          -- 收货日期

    -- 金额信息
    refund_amount DECIMAL(12,2) DEFAULT 0,       -- 退款金额
    restocking_fee DECIMAL(12,2) DEFAULT 0,      -- 重新入库费

    -- 审核信息
    approved_by_id BIGINT,                       -- 审核人
    approved_at DATETIME,                        -- 审核时间

    notes TEXT,                                  -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (sales_order_id) REFERENCES sales_order(id),
    FOREIGN KEY (delivery_id) REFERENCES sales_delivery(id),
    INDEX idx_order_status (sales_order_id, status),
    INDEX idx_return_date (return_date)
);
```

#### sales_loan (销售借用表)
```sql
CREATE TABLE sales_loan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    loan_number VARCHAR(100) UNIQUE NOT NULL,   -- 借用单号: SL20250124001
    customer_id BIGINT NOT NULL,                -- 客户ID
    salesperson_id BIGINT,                      -- 销售员ID
    status VARCHAR(20) DEFAULT 'draft',         -- 状态: draft/loaned/partially_returned...

    -- 日期信息
    loan_date DATE NOT NULL,                    -- 借出日期
    expected_return_date DATE,                  -- 预计归还日期

    -- 借用信息
    purpose TEXT,                               -- 借用目的
    delivery_address TEXT,                      -- 借出地址
    contact_person VARCHAR(100),                -- 联系人
    contact_phone VARCHAR(20),                  -- 联系电话

    -- 转销售信息
    converted_order_id BIGINT,                  -- 转换的销售订单ID
    conversion_approved_by_id BIGINT,           -- 转销售审核人
    conversion_approved_at DATETIME,            -- 转销售审核时间
    conversion_notes TEXT,                      -- 转销售备注

    notes TEXT,                                 -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    FOREIGN KEY (converted_order_id) REFERENCES sales_order(id),
    INDEX idx_customer_status (customer_id, status),
    INDEX idx_loan_date (loan_date)
);
```

---

### 3. 库存管理表 (Inventory Module)

#### warehouse (仓库表)
```sql
CREATE TABLE inventory_warehouse (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,                -- 仓库名称
    code VARCHAR(50) UNIQUE NOT NULL,          -- 仓库编码
    warehouse_type VARCHAR(20) DEFAULT 'main', -- 仓库类型: main/branch/virtual/transit/damaged/borrow
    address TEXT,                              -- 仓库地址
    manager_id BIGINT,                         -- 仓库管理员
    phone VARCHAR(20),                         -- 联系电话
    capacity DECIMAL(12,2),                    -- 仓库容量
    is_active BOOLEAN DEFAULT TRUE,            -- 是否启用

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    INDEX idx_type_active (warehouse_type, is_active)
);
```

#### inventory_stock (库存台账表)
```sql
CREATE TABLE inventory_stock (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL,                -- 产品ID
    warehouse_id BIGINT NOT NULL,              -- 仓库ID
    location_id BIGINT,                        -- 库位ID
    quantity INT DEFAULT 0,                    -- 库存数量
    reserved_quantity INT DEFAULT 0,           -- 预留数量
    cost_price DECIMAL(12,2) DEFAULT 0,        -- 成本价
    last_in_date DATETIME,                     -- 最后入库时间
    last_out_date DATETIME,                    -- 最后出库时间

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (product_id) REFERENCES products_product(id),
    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    UNIQUE KEY unique_product_warehouse_location (product_id, warehouse_id, location_id),
    INDEX idx_product_warehouse (product_id, warehouse_id)
);
```

#### inventory_transaction (库存交易记录表)
```sql
CREATE TABLE inventory_transaction (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    transaction_type VARCHAR(20) NOT NULL,     -- 交易类型: in/out/transfer/adjustment/return/scrap
    product_id BIGINT NOT NULL,                -- 产品ID
    warehouse_id BIGINT NOT NULL,              -- 仓库ID
    location_id BIGINT,                        -- 库位ID
    quantity INT NOT NULL,                     -- 数量
    unit_cost DECIMAL(12,2) DEFAULT 0,         -- 单位成本
    total_cost DECIMAL(12,2) DEFAULT 0,        -- 总成本

    -- 关联信息
    reference_type VARCHAR(20),                 -- 关联类型: purchase_order/sales_order...
    reference_id VARCHAR(100),                 -- 关联单据ID
    reference_number VARCHAR(100),             -- 关联单据号

    -- 批次信息
    batch_number VARCHAR(100),                 -- 批次号
    serial_number VARCHAR(100),                -- 序列号
    expiry_date DATE,                          -- 过期日期

    -- 交易信息
    transaction_date DATETIME NOT NULL,        -- 交易时间
    operator_id BIGINT,                        -- 操作员
    notes TEXT,                                -- 备注

    created_at DATETIME,
    FOREIGN KEY (product_id) REFERENCES products_product(id),
    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    INDEX idx_product_date (product_id, transaction_date),
    INDEX idx_warehouse_date (warehouse_id, transaction_date)
);
```

#### inbound_order (入库单表)
```sql
CREATE TABLE inventory_inbound_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(100) UNIQUE NOT NULL, -- 入库单号: IN20250124001
    warehouse_id BIGINT NOT NULL,              -- 仓库ID
    order_type VARCHAR(20) NOT NULL,           -- 入库类型: purchase/return/transfer/other
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/pending/approved/completed/cancelled
    order_date DATE NOT NULL,                  -- 入库日期

    -- 供应商信息
    supplier_id BIGINT,                        -- 供应商ID

    -- 参考信息
    reference_number VARCHAR(100),             -- 参考单号
    reference_type VARCHAR(50),                -- 参考类型
    reference_id INT,                          -- 参考ID

    -- 审核信息
    approved_by_id BIGINT,                     -- 审核人
    approved_at DATETIME,                      -- 审核时间

    notes TEXT,                                -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers_supplier(id),
    INDEX idx_warehouse_status (warehouse_id, status),
    INDEX idx_order_date (order_date)
);
```

#### outbound_order (出库单表)
```sql
CREATE TABLE inventory_outbound_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(100) UNIQUE NOT NULL, -- 出库单号: OUT20250124001
    warehouse_id BIGINT NOT NULL,              -- 仓库ID
    order_type VARCHAR(20) NOT NULL,           -- 出库类型: sales/production/transfer/other
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/pending/approved/completed/cancelled
    order_date DATE NOT NULL,                  -- 出库日期

    -- 客户信息
    customer_id BIGINT,                        -- 客户ID

    -- 参考信息
    reference_number VARCHAR(100),             -- 参考单号
    reference_type VARCHAR(50),                -- 参考类型
    reference_id INT,                          -- 参考ID

    -- 审核信息
    approved_by_id BIGINT,                     -- 审核人
    approved_at DATETIME,                      -- 审核时间

    notes TEXT,                                -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    INDEX idx_warehouse_status (warehouse_id, status),
    INDEX idx_order_date (order_date)
);
```

#### stock_transfer (库存调拨表)
```sql
CREATE TABLE inventory_transfer (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    transfer_number VARCHAR(100) UNIQUE NOT NULL, -- 调拨单号: TF20250124001
    from_warehouse_id BIGINT NOT NULL,             -- 源仓库ID
    to_warehouse_id BIGINT NOT NULL,               -- 目标仓库ID
    status VARCHAR(20) DEFAULT 'draft',            -- 状态: draft/pending/approved/in_transit/completed/cancelled
    transfer_date DATE NOT NULL,                   -- 调拨日期
    expected_arrival_date DATE,                    -- 预计到达日期
    actual_arrival_date DATE,                      -- 实际到达日期

    -- 审核信息
    approved_by_id BIGINT,                         -- 审核人
    approved_at DATETIME,                          -- 审核时间

    -- 系统标识
    is_auto_generated BOOLEAN DEFAULT FALSE,      -- 系统自动生成标识

    notes TEXT,                                    -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (from_warehouse_id) REFERENCES inventory_warehouse(id),
    FOREIGN KEY (to_warehouse_id) REFERENCES inventory_warehouse(id),
    INDEX idx_from_to_status (from_warehouse_id, to_warehouse_id, status),
    INDEX idx_transfer_date (transfer_date)
);
```

---

### 4. 采购管理表 (Purchase Module)

#### purchase_order (采购订单表)
```sql
CREATE TABLE purchase_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(100) UNIQUE NOT NULL, -- 采购单号: PO20250124001
    supplier_id BIGINT,                        -- 供应商ID (允许NULL)
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/approved/partial_received/fully_received...
    payment_status VARCHAR(20) DEFAULT 'unpaid',-- 付款状态

    -- 日期信息
    order_date DATE NOT NULL,                  -- 订单日期
    required_date DATE,                        -- 要求交期
    promised_date DATE,                        -- 承诺交期
    received_date DATE,                        -- 收货日期

    -- 采购信息
    buyer_id BIGINT,                           -- 采购员

    -- 金额信息
    subtotal DECIMAL(12,2) DEFAULT 0,          -- 小计
    tax_rate DECIMAL(5,2) DEFAULT 0,           -- 税率(%)
    tax_amount DECIMAL(12,2) DEFAULT 0,        -- 税额
    discount_rate DECIMAL(5,2) DEFAULT 0,      -- 折扣率(%)
    discount_amount DECIMAL(12,2) DEFAULT 0,   -- 折扣金额
    shipping_cost DECIMAL(12,2) DEFAULT 0,     -- 运费
    total_amount DECIMAL(12,2) DEFAULT 0,      -- 总金额
    currency VARCHAR(10) DEFAULT 'CNY',        -- 币种

    -- 收货信息
    delivery_address TEXT,                     -- 收货地址
    delivery_contact VARCHAR(100),             -- 收货联系人
    delivery_phone VARCHAR(20),                -- 收货电话
    warehouse_id BIGINT,                       -- 收货仓库

    -- 付款条件
    payment_terms VARCHAR(50),                 -- 付款方式

    -- 附加信息
    reference_number VARCHAR(100),             -- 供应商订单号
    notes TEXT,                               -- 备注
    internal_notes TEXT,                       -- 内部备注

    -- 审核信息
    approved_by_id BIGINT,                     -- 审核人
    approved_at DATETIME,                      -- 审核时间

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (supplier_id) REFERENCES suppliers_supplier(id),
    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    INDEX idx_supplier_status (supplier_id, status),
    INDEX idx_order_date (order_date)
);
```

#### purchase_request (采购申请表)
```sql
CREATE TABLE purchase_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_number VARCHAR(100) UNIQUE NOT NULL, -- 申请单号: PR20250124001
    requester_id BIGINT NOT NULL,                 -- 申请人ID
    department_id BIGINT,                         -- 申请部门ID
    status VARCHAR(20) DEFAULT 'draft',          -- 状态: draft/approved
    priority VARCHAR(20) DEFAULT 'normal',        -- 优先级: low/normal/high/urgent
    request_date DATE NOT NULL,                   -- 申请日期
    required_date DATE,                           -- 需求日期

    purpose TEXT,                                 -- 采购目的
    justification TEXT,                           -- 申请理由
    estimated_total DECIMAL(12,2) DEFAULT 0,     -- 预估总额
    budget_code VARCHAR(100),                     -- 预算科目

    notes TEXT,                                   -- 备注
    rejection_reason TEXT,                        -- 拒绝原因

    -- 审核信息
    approved_by_id BIGINT,                        -- 审核人
    approved_at DATETIME,                         -- 审核时间

    -- 转订单信息
    converted_order_id BIGINT,                    -- 转换的采购订单ID

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (requester_id) REFERENCES users_user(id),
    FOREIGN KEY (department_id) REFERENCES departments_department(id),
    FOREIGN KEY (converted_order_id) REFERENCES purchase_order(id),
    INDEX idx_requester_status (requester_id, status),
    INDEX idx_request_date (request_date)
);
```

#### borrow_order (采购借用表)
```sql
CREATE TABLE purchase_borrow_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    borrow_number VARCHAR(100) UNIQUE NOT NULL, -- 借用单号: PB20250124001
    supplier_id BIGINT NOT NULL,                -- 供应商ID
    requester_id BIGINT NOT NULL,               -- 申请人ID
    department_id BIGINT,                       -- 申请部门ID
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/approved/received/returned/converting/cancelled
    priority VARCHAR(20) DEFAULT 'normal',      -- 优先级

    -- 日期信息
    request_date DATE NOT NULL,                 -- 申请日期
    required_date DATE,                         -- 需求日期
    expected_return_date DATE,                  -- 预计归还日期

    -- 借用信息
    purpose TEXT,                               -- 借用目的
    warehouse_id BIGINT,                        -- 收货仓库

    -- 转采购信息
    conversion_approved_by_id BIGINT,           -- 转采购审核人
    conversion_approved_at DATETIME,            -- 转采购审核时间
    converted_order_id BIGINT,                  -- 转换的采购订单ID

    notes TEXT,                                 -- 备注

    -- 审核信息
    approved_by_id BIGINT,                      -- 审核人
    approved_at DATETIME,                       -- 审核时间

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (supplier_id) REFERENCES suppliers_supplier(id),
    FOREIGN KEY (warehouse_id) REFERENCES inventory_warehouse(id),
    FOREIGN KEY (converted_order_id) REFERENCES purchase_order(id),
    INDEX idx_supplier_status (supplier_id, status),
    INDEX idx_request_date (request_date)
);
```

---

### 5. 财务管理表 (Finance Module)

#### customer_account (客户应收账款表)
```sql
CREATE TABLE finance_customer_account (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL,               -- 客户ID
    sales_order_id BIGINT,                     -- 销售订单ID
    invoice_number VARCHAR(100),               -- 发票号
    invoice_date DATE,                         -- 发票日期
    due_date DATE,                             -- 到期日期

    -- 金额信息
    invoice_amount DECIMAL(12,2) DEFAULT 0,    -- 发票金额
    paid_amount DECIMAL(12,2) DEFAULT 0,       -- 已付金额
    balance DECIMAL(12,2) DEFAULT 0,           -- 余额

    currency VARCHAR(10) DEFAULT 'CNY',        -- 币种
    notes TEXT,                               -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    FOREIGN KEY (sales_order_id) REFERENCES sales_order(id),
    INDEX idx_customer_balance (customer_id, balance),
    INDEX idx_due_date (due_date)
);
```

#### supplier_account (供应商应付账款表)
```sql
CREATE TABLE finance_supplier_account (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    supplier_id BIGINT,                        -- 供应商ID
    customer_id BIGINT,                        -- 客户ID (销售退货退款时使用)
    purchase_order_id BIGINT,                  -- 采购订单ID
    sales_return_id BIGINT,                    -- 销售退货单ID
    invoice_id BIGINT,                         -- 关联发票ID

    -- 发票信息 (保留向后兼容)
    invoice_number VARCHAR(100),               -- 发票号
    invoice_date DATE,                         -- 发票日期
    due_date DATE,                             -- 到期日期

    -- 状态
    status VARCHAR(20) DEFAULT 'pending',      -- 状态: pending/partially_paid/paid/overdue

    -- 金额信息 (自动归集)
    invoice_amount DECIMAL(12,2) DEFAULT 0,    -- 实际应付金额 = 累计正应付 + 累计负应付
    paid_amount DECIMAL(12,2) DEFAULT 0,       -- 已核销金额
    balance DECIMAL(12,2) DEFAULT 0,           -- 未付余额 = 实际应付 - 已核销

    currency VARCHAR(10) DEFAULT 'CNY',        -- 币种
    notes TEXT,                               -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (supplier_id) REFERENCES suppliers_supplier(id),
    FOREIGN KEY (customer_id) REFERENCES customers_customer(id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_order(id),
    FOREIGN KEY (sales_return_id) REFERENCES sales_return(id),
    INDEX idx_supplier_status (supplier_id, status),
    INDEX idx_due_date (due_date)
);
```

#### account (会计科目表)
```sql
CREATE TABLE finance_account (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,         -- 科目代码
    name VARCHAR(100) NOT NULL,               -- 科目名称
    account_type VARCHAR(20) NOT NULL,        -- 科目类型: asset/liability/equity/revenue/expense/cost
    category VARCHAR(30),                     -- 科目分类: current_asset/fixed_asset...

    -- 层级结构
    parent_id BIGINT,                         -- 上级科目ID
    level INT DEFAULT 1,                      -- 科目级别

    -- 属性
    is_leaf BOOLEAN DEFAULT TRUE,             -- 是否末级科目
    is_active BOOLEAN DEFAULT TRUE,           -- 是否启用
    allow_manual_entry BOOLEAN DEFAULT TRUE,  -- 允许手工录入

    -- 余额信息
    opening_balance DECIMAL(15,2) DEFAULT 0,  -- 期初余额
    current_balance DECIMAL(15,2) DEFAULT 0,  -- 当前余额

    description TEXT,                         -- 科目说明

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (parent_id) REFERENCES finance_account(id),
    INDEX idx_code (code),
    INDEX idx_type (account_type)
);
```

#### journal (记账凭证表)
```sql
CREATE TABLE finance_journal (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    journal_number VARCHAR(50) UNIQUE NOT NULL, -- 凭证号
    journal_type VARCHAR(20) DEFAULT 'general', -- 凭证类型: general/cash/bank/transfer/adjustment
    status VARCHAR(20) DEFAULT 'draft',        -- 状态: draft/posted/cancelled

    -- 日期信息
    journal_date DATE NOT NULL,                -- 凭证日期
    period VARCHAR(7) NOT NULL,                -- 会计期间: YYYY-MM

    -- 关联信息
    reference_type VARCHAR(50),                -- 关联类型
    reference_id VARCHAR(100),                 -- 关联单据ID
    reference_number VARCHAR(100),             -- 关联单据号

    -- 金额信息
    total_debit DECIMAL(15,2) DEFAULT 0,      -- 借方合计
    total_credit DECIMAL(15,2) DEFAULT 0,     -- 贷方合计

    -- 人员信息
    prepared_by_id BIGINT,                    -- 制单人
    reviewed_by_id BIGINT,                    -- 审核人
    posted_by_id BIGINT,                      -- 过账人
    posted_at DATETIME,                       -- 过账时间

    description TEXT,                         -- 摘要
    notes TEXT,                              -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    INDEX idx_journal_date (journal_date),
    INDEX idx_period (period),
    INDEX idx_status (status)
);
```

---

### 6. 产品管理表 (Products Module)

#### product (产品表)
```sql
CREATE TABLE products_product (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,               -- 产品名称
    code VARCHAR(100) UNIQUE NOT NULL,       -- 产品编码
    barcode VARCHAR(100) UNIQUE,              -- 条形码
    category_id BIGINT,                       -- 产品分类ID
    brand_id BIGINT,                          -- 品牌ID
    product_type VARCHAR(20) DEFAULT 'finished', -- 产品类型: material/semi_finished/finished/service/virtual
    status VARCHAR(20) DEFAULT 'active',      -- 状态: active/inactive/discontinued/development

    -- 描述信息
    description TEXT,                         -- 产品描述
    specifications TEXT,                      -- 产品规格
    model VARCHAR(100),                       -- 型号

    -- 单位信息
    unit_id BIGINT,                           -- 基本单位ID

    -- 尺寸重量
    weight DECIMAL(10,3),                     -- 重量(kg)
    length DECIMAL(10,2),                     -- 长度(cm)
    width DECIMAL(10,2),                      -- 宽度(cm)
    height DECIMAL(10,2),                     -- 高度(cm)

    -- 价格信息
    cost_price DECIMAL(12,2) DEFAULT 0,       -- 成本价
    selling_price DECIMAL(12,2) DEFAULT 0,    -- 销售价

    -- 库存设置
    track_inventory BOOLEAN DEFAULT TRUE,     -- 是否进行库存管理
    min_stock INT DEFAULT 0,                  -- 最小库存
    max_stock INT DEFAULT 0,                  -- 最大库存
    reorder_point INT DEFAULT 0,              -- 再订货点

    -- 图片信息
    main_image VARCHAR(100),                  -- 主图路径

    -- 附加信息
    warranty_period INT DEFAULT 0,            -- 保修期(月)
    shelf_life INT,                           -- 保质期(天)
    notes TEXT,                              -- 备注

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (category_id) REFERENCES products_productcategory(id),
    FOREIGN KEY (brand_id) REFERENCES products_brand(id),
    FOREIGN KEY (unit_id) REFERENCES products_unit(id),
    INDEX idx_code (code),
    INDEX idx_category (category_id),
    INDEX idx_status (status)
);
```

#### product_category (产品分类表 - MPTT树形结构)
```sql
CREATE TABLE products_productcategory (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,               -- 分类名称
    code VARCHAR(50) UNIQUE NOT NULL,         -- 分类代码
    parent_id BIGINT,                         -- 上级分类ID
    description TEXT,                         -- 分类描述
    image VARCHAR(100),                       -- 分类图片
    sort_order INT DEFAULT 0,                 -- 排序
    is_active BOOLEAN DEFAULT TRUE,           -- 是否启用

    -- MPTT字段
    lft INT DEFAULT 0,                        -- 左值
    rght INT DEFAULT 0,                       -- 右值
    tree_id INT DEFAULT 0,                    -- 树ID
    level INT DEFAULT 0,                      -- 层级

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    FOREIGN KEY (parent_id) REFERENCES products_productcategory(id),
    INDEX idx_lft_rght (lft, rght),
    INDEX idx_tree_id (tree_id)
);
```

---

### 7. AI助手表 (AI Assistant Module)

#### ai_model_config (AI模型配置表)
```sql
CREATE TABLE ai_model_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,               -- 配置名称
    provider VARCHAR(50) NOT NULL,            -- 提供商: openai/anthropic/baidu/aliyun/tencent/zhipu/moonshot/deepseek/mock

    -- API配置
    api_key VARCHAR(500) NOT NULL,            -- API Key (加密存储)
    api_base VARCHAR(500),                    -- API Base URL
    model_name VARCHAR(100) NOT NULL,         -- 模型名称: gpt-4/claude-3-5-sonnet/ernie-bot-4.0

    -- 参数配置
    temperature DECIMAL(3,2) DEFAULT 0.7,     -- Temperature (0-1)
    max_tokens INT DEFAULT 2000,              -- Max Tokens
    timeout INT DEFAULT 60,                   -- 超时时间(秒)

    -- 状态管理
    is_active BOOLEAN DEFAULT TRUE,           -- 是否启用
    is_default BOOLEAN DEFAULT FALSE,         -- 是否默认
    priority INT DEFAULT 0,                   -- 优先级

    -- 使用统计
    total_requests INT DEFAULT 0,             -- 总请求数
    total_tokens INT DEFAULT 0,               -- 总Token数
    last_used_at DATETIME,                    -- 最后使用时间

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    INDEX idx_provider_active (provider, is_active),
    INDEX idx_priority (priority)
);
```

#### ai_conversation (AI对话会话表)
```sql
CREATE TABLE ai_conversation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id VARCHAR(100) UNIQUE NOT NULL, -- 会话ID (UUID)
    user_id BIGINT NOT NULL,                     -- 用户ID
    channel VARCHAR(20) NOT NULL,                 -- 渠道: web/wechat/dingtalk/telegram
    channel_user_id VARCHAR(200),                 -- 渠道用户ID (微信openid或钉钉userid)

    -- 会话状态
    status VARCHAR(20) DEFAULT 'active',          -- 状态: active/ended

    -- 会话元信息
    title VARCHAR(200),                          -- 会话标题
    context_summary TEXT,                        -- 上下文摘要

    -- 统计信息
    message_count INT DEFAULT 0,                 -- 消息数
    last_message_at DATETIME,                    -- 最后消息时间

    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users_user(id),
    INDEX idx_user_channel_status (user_id, channel, status),
    INDEX idx_conversation_id (conversation_id)
);
```

#### ai_message (AI对话消息表)
```sql
CREATE TABLE ai_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id BIGINT NOT NULL,         -- 会话ID
    role VARCHAR(20) NOT NULL,               -- 角色: user/assistant/system/tool

    -- 消息内容
    content TEXT NOT NULL,                   -- 消息内容
    content_type VARCHAR(20) DEFAULT 'text', -- 内容类型: text/image/file

    -- 工具调用记录
    tool_calls JSON,                         -- 工具调用记录
    tool_results JSON,                       -- 工具执行结果

    -- 模型信息
    model_config_id BIGINT,                  -- 使用的模型配置
    tokens_used INT DEFAULT 0,               -- 消耗Token数
    response_time DECIMAL(10,3),             -- 响应时间(秒)

    created_at DATETIME,
    FOREIGN KEY (conversation_id) REFERENCES ai_conversation(id),
    FOREIGN KEY (model_config_id) REFERENCES ai_model_config(id),
    INDEX idx_conversation_created (conversation_id, created_at)
);
```

#### ai_tool (AI工具定义表)
```sql
CREATE TABLE ai_tool (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tool_name VARCHAR(100) UNIQUE NOT NULL,  -- 工具名称 (唯一标识)
    display_name VARCHAR(200) NOT NULL,      -- 显示名称
    category VARCHAR(50) NOT NULL,           -- 分类: sales/purchase/inventory/finance/report/system

    -- 工具描述 (给AI看的)
    description TEXT NOT NULL,               -- 工具描述

    -- 参数定义 (JSON Schema格式)
    parameters JSON NOT NULL,                -- 参数定义

    -- 执行配置
    handler_path VARCHAR(200) NOT NULL,      -- 处理器路径: apps.ai_assistant.tools.sales.SearchCustomerTool
    requires_approval BOOLEAN DEFAULT FALSE, -- 需要审批

    -- 权限控制
    required_permissions JSON DEFAULT ('[]'), -- 所需权限列表

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,          -- 是否启用

    -- 使用统计
    call_count INT DEFAULT 0,                -- 调用次数
    success_count INT DEFAULT 0,             -- 成功次数
    last_called_at DATETIME,                 -- 最后调用时间

    created_at DATETIME,
    updated_at DATETIME,
    created_by_id BIGINT,
    updated_by_id BIGINT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by_id BIGINT,

    INDEX idx_category (category),
    INDEX idx_tool_name (tool_name)
);
```

---

## 🔗 表关系图

### 核心外键关系

```
customers_customer (客户)
    ├── sales_order (销售订单) ──┐
    ├── quote (报价单)           │
    ├── delivery (发货单)        │
    ├── sales_return (退货单)    │
    ├── sales_loan (借用单)      │
    ├── customer_account (应收)  │
    └── outbound_order (出库单)  │

suppliers_supplier (供应商)
    ├── purchase_order (采购订单) ──┐
    ├── borrow_order (借用单)       │
    ├── supplier_account (应付)     │
    └── inbound_order (入库单)      │

products_product (产品)
    ├── sales_order_item (订单明细)
    ├── quote_item (报价明细)
    ├── inventory_stock (库存台账)
    ├── purchase_order_item (采购明细)
    └── inventory_transaction (交易记录)

inventory_warehouse (仓库)
    ├── inventory_stock (库存台账)
    ├── inbound_order (入库单)
    ├── outbound_order (出库单)
    ├── stock_transfer (调拨单)
    └── delivery (发货单)

users_user (用户)
    ├── sales_order (销售订单)
    ├── purchase_order (采购订单)
    ├── customer_account (应收)
    └── 所有 created_by/updated_by
```

---

## 📈 性能优化建议

### 1. 索引优化
```sql
-- 高频查询索引
CREATE INDEX idx_sales_order_customer_status_date
ON sales_order(customer_id, status, order_date DESC);

CREATE INDEX idx_inventory_stock_product_warehouse
ON inventory_stock(product_id, warehouse_id);

CREATE INDEX idx_customer_account_balance
ON finance_customer_account(balance DESC)
WHERE balance > 0;
```

### 2. 分区表建议
```sql
-- 按年份分区历史数据表
ALTER TABLE audit_log PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### 3. 查询优化
```python
# 避免 N+1 查询
orders = SalesOrder.objects.select_related(
    'customer', 'sales_rep', 'approved_by'
).prefetch_related(
    'items__product'
).filter(is_deleted=False)

# 使用索引字段
Product.objects.filter(code='PRODUCT001')  # 使用索引
Product.objects.filter(name__icontains='laser')  # 全表扫描
```

---

## 🔒 数据安全建议

### 1. 敏感数据加密
```python
# API Key 加密存储
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)

    def encrypt(self, value):
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, value):
        return self.cipher.decrypt(value.encode()).decode()
```

### 2. 数据备份策略
```bash
# 每日全量备份
0 2 * * * /usr/bin/mysqldump -u root -p${DB_PASSWORD} \
    --single-transaction --routines --triggers \
    django_erp > /backup/django_erp_$(date +\%Y\%m\%d).sql

# 每周备份清理
0 3 * * 0 find /backup -name "django_erp_*.sql" \
    -mtime +30 -delete
```

### 3. 软删除数据归档
```python
# 定期归档软删除数据
def archive_deleted_records():
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_records = SalesOrder.objects.filter(
        is_deleted=True,
        deleted_at__lt=cutoff_date
    )

    # 移动到归档表或导出到文件
    for record in deleted_records:
        archive_record(record)
        record.hard_delete()
```

---

## 📋 总结

### 数据库设计特点
1. **统一规范**: 所有表继承 BaseModel，字段命名统一
2. **软删除**: 保留数据完整性，支持数据恢复
3. **审计追踪**: 完整的操作日志和时间戳记录
4. **国际化支持**: 多币种、多税率支持
5. **树形结构**: MPTT实现高效的层级查询
6. **业务完整**: 覆盖ERP核心业务流程

### 改进建议
1. **性能优化**: 添加复合索引，优化查询语句
2. **数据安全**: 敏感数据加密，完善备份策略
3. **归档策略**: 历史数据分区归档
4. **监控告警**: 数据库性能监控
5. **容量规划**: 表空间规划和扩展

---

**文档版本**: v1.0
**生成时间**: 2025-01-24
**数据库版本**: MySQL 8.0+ (生产) / SQLite 3 (开发)