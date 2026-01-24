"""
初始选项数据 - 从现有硬编码choices迁移而来
Initial choice options data migrated from hardcoded choices.
"""

INITIAL_CHOICE_OPTIONS = [
    # ============================================
    # 客户相关选项 (Customer Related)
    # ============================================

    # 客户等级 (Customer Level)
    {'category': 'customer_level', 'code': 'A', 'label': 'A级客户', 'sort_order': 10, 'is_system': True, 'description': '重要客户'},
    {'category': 'customer_level', 'code': 'B', 'label': 'B级客户', 'sort_order': 20, 'is_system': True, 'description': '主要客户'},
    {'category': 'customer_level', 'code': 'C', 'label': 'C级客户', 'sort_order': 30, 'is_system': True, 'description': '普通客户'},
    {'category': 'customer_level', 'code': 'D', 'label': 'D级客户', 'sort_order': 40, 'is_system': True, 'description': '小客户'},

    # 客户状态 (Customer Status)
    {'category': 'customer_status', 'code': 'active', 'label': '正常', 'sort_order': 10, 'is_system': True, 'color': '#10b981', 'icon': 'fa-check-circle'},
    {'category': 'customer_status', 'code': 'inactive', 'label': '停用', 'sort_order': 20, 'is_system': True, 'color': '#6b7280', 'icon': 'fa-ban'},
    {'category': 'customer_status', 'code': 'potential', 'label': '潜在客户', 'sort_order': 30, 'is_system': True, 'color': '#3b82f6', 'icon': 'fa-star'},
    {'category': 'customer_status', 'code': 'blacklist', 'label': '黑名单', 'sort_order': 40, 'is_system': True, 'color': '#ef4444', 'icon': 'fa-exclamation-triangle'},

    # 地址类型 (Address Type)
    {'category': 'address_type', 'code': 'billing', 'label': '账单地址', 'sort_order': 10, 'is_system': True},
    {'category': 'address_type', 'code': 'shipping', 'label': '收货地址', 'sort_order': 20, 'is_system': True},
    {'category': 'address_type', 'code': 'office', 'label': '办公地址', 'sort_order': 30, 'is_system': True},
    {'category': 'address_type', 'code': 'warehouse', 'label': '仓库地址', 'sort_order': 40, 'is_system': True},

    # 拜访类型 (Visit Type)
    {'category': 'visit_type', 'code': 'phone', 'label': '电话拜访', 'sort_order': 10, 'is_system': True},
    {'category': 'visit_type', 'code': 'email', 'label': '邮件联系', 'sort_order': 20, 'is_system': True},
    {'category': 'visit_type', 'code': 'onsite', 'label': '上门拜访', 'sort_order': 30, 'is_system': True},
    {'category': 'visit_type', 'code': 'exhibition', 'label': '展会接触', 'sort_order': 40, 'is_system': True},
    {'category': 'visit_type', 'code': 'online', 'label': '在线沟通', 'sort_order': 50, 'is_system': True},

    # 拜访目的 (Visit Purpose)
    {'category': 'visit_purpose', 'code': 'sales', 'label': '销售拜访', 'sort_order': 10, 'is_system': True},
    {'category': 'visit_purpose', 'code': 'service', 'label': '售后服务', 'sort_order': 20, 'is_system': True},
    {'category': 'visit_purpose', 'code': 'collection', 'label': '催收款项', 'sort_order': 30, 'is_system': True},
    {'category': 'visit_purpose', 'code': 'relationship', 'label': '关系维护', 'sort_order': 40, 'is_system': True},
    {'category': 'visit_purpose', 'code': 'complaint', 'label': '投诉处理', 'sort_order': 50, 'is_system': True},

    # 信用操作类型 (Credit Type)
    {'category': 'credit_type', 'code': 'increase', 'label': '增加信用额度', 'sort_order': 10, 'is_system': True, 'color': '#10b981'},
    {'category': 'credit_type', 'code': 'decrease', 'label': '减少信用额度', 'sort_order': 20, 'is_system': True, 'color': '#f59e0b'},
    {'category': 'credit_type', 'code': 'freeze', 'label': '冻结信用', 'sort_order': 30, 'is_system': True, 'color': '#3b82f6'},
    {'category': 'credit_type', 'code': 'unfreeze', 'label': '解冻信用', 'sort_order': 40, 'is_system': True, 'color': '#10b981'},

    # ============================================
    # 供应商相关选项 (Supplier Related)
    # ============================================

    # 供应商等级 (Supplier Level)
    {'category': 'supplier_level', 'code': 'A', 'label': 'A级供应商', 'sort_order': 10, 'is_system': True, 'description': '战略供应商'},
    {'category': 'supplier_level', 'code': 'B', 'label': 'B级供应商', 'sort_order': 20, 'is_system': True, 'description': '重要供应商'},
    {'category': 'supplier_level', 'code': 'C', 'label': 'C级供应商', 'sort_order': 30, 'is_system': True, 'description': '普通供应商'},
    {'category': 'supplier_level', 'code': 'D', 'label': 'D级供应商', 'sort_order': 40, 'is_system': True, 'description': '备选供应商'},

    # 联系人类型 (Contact Type)
    {'category': 'contact_type', 'code': 'primary', 'label': '主要联系人', 'sort_order': 10, 'is_system': True},
    {'category': 'contact_type', 'code': 'finance', 'label': '财务联系人', 'sort_order': 20, 'is_system': True},
    {'category': 'contact_type', 'code': 'technical', 'label': '技术联系人', 'sort_order': 30, 'is_system': True},
    {'category': 'contact_type', 'code': 'sales', 'label': '销售联系人', 'sort_order': 40, 'is_system': True},
    {'category': 'contact_type', 'code': 'other', 'label': '其他联系人', 'sort_order': 50, 'is_system': True},

    # 评估周期 (Evaluation Period)
    {'category': 'evaluation_period', 'code': 'monthly', 'label': '月度评估', 'sort_order': 10, 'is_system': True},
    {'category': 'evaluation_period', 'code': 'quarterly', 'label': '季度评估', 'sort_order': 20, 'is_system': True},
    {'category': 'evaluation_period', 'code': 'annual', 'label': '年度评估', 'sort_order': 30, 'is_system': True},

    # ============================================
    # 产品相关选项 (Product Related)
    # ============================================

    # 产品类型 (Product Type)
    {'category': 'product_type', 'code': 'finished', 'label': '成品', 'sort_order': 10, 'is_system': True},
    {'category': 'product_type', 'code': 'semi_finished', 'label': '半成品', 'sort_order': 20, 'is_system': True},
    {'category': 'product_type', 'code': 'raw_material', 'label': '原材料', 'sort_order': 30, 'is_system': True},
    {'category': 'product_type', 'code': 'consumable', 'label': '耗材', 'sort_order': 40, 'is_system': True},

    # 产品状态 (Product Status)
    {'category': 'product_status', 'code': 'active', 'label': '在售', 'sort_order': 10, 'is_system': True, 'color': '#10b981'},
    {'category': 'product_status', 'code': 'inactive', 'label': '停售', 'sort_order': 20, 'is_system': True, 'color': '#6b7280'},
    {'category': 'product_status', 'code': 'discontinued', 'label': '已停产', 'sort_order': 30, 'is_system': True, 'color': '#ef4444'},

    # 单位类型 (Unit Type)
    {'category': 'unit_type', 'code': 'quantity', 'label': '数量单位', 'sort_order': 10, 'is_system': True, 'description': '件、个、台等'},
    {'category': 'unit_type', 'code': 'weight', 'label': '重量单位', 'sort_order': 20, 'is_system': True, 'description': 'kg、g、吨等'},
    {'category': 'unit_type', 'code': 'length', 'label': '长度单位', 'sort_order': 30, 'is_system': True, 'description': '米、厘米等'},

    # 属性类型 (Attribute Type)
    {'category': 'attribute_type', 'code': 'text', 'label': '文本', 'sort_order': 10, 'is_system': True},
    {'category': 'attribute_type', 'code': 'number', 'label': '数字', 'sort_order': 20, 'is_system': True},
    {'category': 'attribute_type', 'code': 'date', 'label': '日期', 'sort_order': 30, 'is_system': True},
    {'category': 'attribute_type', 'code': 'select', 'label': '选择', 'sort_order': 40, 'is_system': True},

    # 价格类型 (Price Type)
    {'category': 'price_type', 'code': 'standard', 'label': '标准价格', 'sort_order': 10, 'is_system': True},
    {'category': 'price_type', 'code': 'member', 'label': '会员价格', 'sort_order': 20, 'is_system': True},
    {'category': 'price_type', 'code': 'wholesale', 'label': '批发价格', 'sort_order': 30, 'is_system': True},

    # ============================================
    # 库存相关选项 (Inventory Related)
    # ============================================

    # 仓库类型 (Warehouse Type)
    {'category': 'warehouse_type', 'code': 'main', 'label': '主仓库', 'sort_order': 10, 'is_system': True},
    {'category': 'warehouse_type', 'code': 'transit', 'label': '中转仓', 'sort_order': 20, 'is_system': True},
    {'category': 'warehouse_type', 'code': 'return', 'label': '退货仓', 'sort_order': 30, 'is_system': True},
    {'category': 'warehouse_type', 'code': 'virtual', 'label': '虚拟仓', 'sort_order': 40, 'is_system': True},

    # 库存调整类型 (Adjustment Type)
    {'category': 'adjustment_type', 'code': 'increase', 'label': '盘盈', 'sort_order': 10, 'is_system': True, 'color': '#10b981'},
    {'category': 'adjustment_type', 'code': 'decrease', 'label': '盘亏', 'sort_order': 20, 'is_system': True, 'color': '#ef4444'},
    {'category': 'adjustment_type', 'code': 'damage', 'label': '损坏', 'sort_order': 30, 'is_system': True, 'color': '#f59e0b'},
    {'category': 'adjustment_type', 'code': 'other', 'label': '其他', 'sort_order': 40, 'is_system': True},

    # 调整原因 (Adjustment Reason)
    {'category': 'adjustment_reason', 'code': 'count_diff', 'label': '盘点差异', 'sort_order': 10, 'is_system': True},
    {'category': 'adjustment_reason', 'code': 'damage', 'label': '货物损坏', 'sort_order': 20, 'is_system': True},
    {'category': 'adjustment_reason', 'code': 'expire', 'label': '过期报废', 'sort_order': 30, 'is_system': True},
    {'category': 'adjustment_reason', 'code': 'lost', 'label': '丢失', 'sort_order': 40, 'is_system': True},
    {'category': 'adjustment_reason', 'code': 'system_error', 'label': '系统错误', 'sort_order': 50, 'is_system': True},
    {'category': 'adjustment_reason', 'code': 'other', 'label': '其他原因', 'sort_order': 60, 'is_system': True},

    # 盘点类型 (Count Type)
    {'category': 'count_type', 'code': 'full', 'label': '全盘', 'sort_order': 10, 'is_system': True, 'description': '全仓盘点'},
    {'category': 'count_type', 'code': 'partial', 'label': '抽盘', 'sort_order': 20, 'is_system': True, 'description': '部分产品盘点'},
    {'category': 'count_type', 'code': 'cycle', 'label': '循环盘点', 'sort_order': 30, 'is_system': True, 'description': '定期循环盘点'},

    # 库存事务类型 (Transaction Type)
    {'category': 'transaction_type', 'code': 'in', 'label': '入库', 'sort_order': 10, 'is_system': True, 'color': '#10b981'},
    {'category': 'transaction_type', 'code': 'out', 'label': '出库', 'sort_order': 20, 'is_system': True, 'color': '#ef4444'},
    {'category': 'transaction_type', 'code': 'transfer', 'label': '调拨', 'sort_order': 30, 'is_system': True, 'color': '#3b82f6'},
    {'category': 'transaction_type', 'code': 'adjust', 'label': '调整', 'sort_order': 40, 'is_system': True, 'color': '#f59e0b'},
    {'category': 'transaction_type', 'code': 'count', 'label': '盘点', 'sort_order': 50, 'is_system': True, 'color': '#8b5cf6'},
    {'category': 'transaction_type', 'code': 'freeze', 'label': '冻结', 'sort_order': 60, 'is_system': True, 'color': '#6b7280'},

    # ============================================
    # 财务相关选项 (Finance Related)
    # ============================================

    # 付款方式 (Payment Terms)
    {'category': 'payment_terms', 'code': 'tt_100', 'label': 'T/T 100%', 'sort_order': 10, 'is_system': True, 'description': '全额电汇'},
    {'category': 'payment_terms', 'code': 'net_30', 'label': 'NET 30 EOM.', 'sort_order': 20, 'is_system': True, 'description': '月底后30天'},
    {'category': 'payment_terms', 'code': 'net_60', 'label': 'NET 60 EOM.', 'sort_order': 30, 'is_system': True, 'description': '月底后60天'},
    {'category': 'payment_terms', 'code': '30_70', 'label': '30% Adv,70% B4 SHPT.30%+70%', 'sort_order': 40, 'is_system': True, 'description': '30%预付，70%发货前付'},
    {'category': 'payment_terms', 'code': 'cash', 'label': 'Cash', 'sort_order': 50, 'is_system': True, 'description': '现金支付'},
    {'category': 'payment_terms', 'code': 'be', 'label': 'B/E', 'sort_order': 60, 'is_system': True, 'description': '银行汇票'},
]
