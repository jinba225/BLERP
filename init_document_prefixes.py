#!/usr/bin/env python
"""
初始化单号前缀配置

参考 Odoo 标准设置各类单据的前缀
运行方式：python init_document_prefixes.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.models import SystemConfig

# 定义单号前缀配置（参考 Odoo 标准）
DOCUMENT_PREFIXES = {
    # 销售相关
    'document_prefix_quotation': {
        'value': 'SQ',
        'description': '报价单前缀 - 销售报价单的单号前缀（Sales Quotation）',
        'config_type': 'business',
    },
    'document_prefix_sales_order': {
        'value': 'SO',
        'description': '销售订单前缀 - 销售订单的单号前缀（Sales Order）',
        'config_type': 'business',
    },
    'document_prefix_delivery': {
        'value': 'OUT',
        'description': '发货单前缀 - 销售发货单的单号前缀（Delivery / Outbound）',
        'config_type': 'business',
    },
    'document_prefix_sales_return': {
        'value': 'SR',
        'description': '销售退货前缀 - 销售退货单的单号前缀（Sales Return）',
        'config_type': 'business',
    },

    # 采购相关
    'document_prefix_purchase_request': {
        'value': 'PR',
        'description': '采购申请前缀 - 采购申请单的单号前缀（Purchase Request）',
        'config_type': 'business',
    },
    'document_prefix_purchase_inquiry': {
        'value': 'RFQ',
        'description': '采购询价前缀 - 采购询价单的单号前缀（Request for Quotation）',
        'config_type': 'business',
    },
    'document_prefix_purchase_order': {
        'value': 'PO',
        'description': '采购订单前缀 - 采购订单的单号前缀（Purchase Order）',
        'config_type': 'business',
    },
    'document_prefix_receipt': {
        'value': 'IN',
        'description': '收货单前缀 - 采购收货单/入库单的单号前缀（Receipt / Inbound）',
        'config_type': 'business',
    },
    'document_prefix_purchase_return': {
        'value': 'ROUT',
        'description': '采购退货前缀 - 采购退货单的单号前缀（Return Outbound）',
        'config_type': 'business',
    },

    # 库存相关
    'document_prefix_stock_in': {
        'value': 'IN',
        'description': '入库单前缀 - 库存入库单的单号前缀（Stock In）',
        'config_type': 'business',
    },
    'document_prefix_stock_out': {
        'value': 'OUT',
        'description': '出库单前缀 - 库存出库单的单号前缀（Stock Out）',
        'config_type': 'business',
    },
    'document_prefix_stock_transfer': {
        'value': 'INT',
        'description': '调拨单前缀 - 库存调拨单的单号前缀（Internal Transfer）',
        'config_type': 'business',
    },
    'document_prefix_stock_picking': {
        'value': 'PICK',
        'description': '盘点单前缀 - 库存盘点单的单号前缀（Stock Picking/Inventory）',
        'config_type': 'business',
    },
    'document_prefix_stock_adjustment': {
        'value': 'ADJ',
        'description': '库存调整前缀 - 库存调整单的单号前缀（Adjustment）',
        'config_type': 'business',
    },

    # 质检相关
    'document_prefix_quality_inspection': {
        'value': 'QC',
        'description': '质检单前缀 - 质量检验单的单号前缀（Quality Control）',
        'config_type': 'business',
    },

    # 合同相关
    'document_prefix_sales_contract': {
        'value': 'SC',
        'description': '销售合同前缀 - 销售合同的单号前缀（Sales Contract）',
        'config_type': 'business',
    },
    'document_prefix_purchase_contract': {
        'value': 'PC',
        'description': '采购合同前缀 - 采购合同的单号前缀（Purchase Contract）',
        'config_type': 'business',
    },
    'document_prefix_loan_contract': {
        'value': 'LC',
        'description': '借用合同前缀 - 借用合同的单号前缀（Loan Contract）',
        'config_type': 'business',
    },

    # 生产相关
    'document_prefix_production_plan': {
        'value': 'PP',
        'description': '生产计划前缀 - 生产计划的单号前缀（Production Plan）',
        'config_type': 'business',
    },
    'document_prefix_work_order': {
        'value': 'MO',
        'description': '生产工单前缀 - 生产工单的单号前缀（Manufacturing Order）',
        'config_type': 'business',
    },
    'document_prefix_material_requisition': {
        'value': 'MR',
        'description': '领料单前缀 - 生产领料单的单号前缀（Material Requisition）',
        'config_type': 'business',
    },
    'document_prefix_material_return': {
        'value': 'MTR',
        'description': '退料单前缀 - 生产退料单的单号前缀（Material Return）',
        'config_type': 'business',
    },

    # 财务相关
    'document_prefix_payment_receipt': {
        'value': 'PAY',
        'description': '收款单前缀 - 收款单的单号前缀（Payment Receipt）',
        'config_type': 'business',
    },
    'document_prefix_payment': {
        'value': 'BILL',
        'description': '付款单前缀 - 付款单的单号前缀（Bill Payment）',
        'config_type': 'business',
    },
    'document_prefix_invoice': {
        'value': 'INV',
        'description': '发票前缀 - 发票的单号前缀（Invoice）',
        'config_type': 'business',
    },
    'document_prefix_refund': {
        'value': 'RINV',
        'description': '退款单前缀 - 退款单的单号前缀（Refund Invoice）',
        'config_type': 'business',
    },
    'document_prefix_expense': {
        'value': 'EXP',
        'description': '报销单前缀 - 费用报销单的单号前缀（Expense）',
        'config_type': 'business',
    },
}

def init_prefixes():
    """初始化单号前缀配置"""
    print("开始初始化单号前缀配置...\n")

    created_count = 0
    updated_count = 0

    for key, config_data in DOCUMENT_PREFIXES.items():
        config, created = SystemConfig.objects.get_or_create(
            key=key,
            defaults={
                'value': config_data['value'],
                'description': config_data['description'],
                'config_type': config_data['config_type'],
            }
        )

        if created:
            created_count += 1
            print(f"✓ 创建配置: {key} = {config.value}")
        else:
            # 如果已存在，不覆盖用户的自定义配置
            updated_count += 1
            print(f"  已存在: {key} = {config.value} (保留现有配置)")

    print(f"\n完成！创建 {created_count} 个新配置，跳过 {updated_count} 个已存在的配置")
    print("\n配置说明：")
    print("- 这些配置可以在系统后台 /admin/core/systemconfig/ 中修改")
    print("- 单号格式：前缀 + YYYYMMDD + 4位序号")
    print("- 例如：SO20251108001（销售订单）")
    print("\n主要单号前缀：")
    print("  SQ  - 销售报价单 (Sales Quotation)")
    print("  SO  - 销售订单 (Sales Order)")
    print("  PR  - 采购申请单 (Purchase Request)")
    print("  PO  - 采购订单 (Purchase Order)")
    print("  IN  - 入库单/收货单 (Inbound)")
    print("  OUT - 出库单/发货单 (Outbound)")
    print("  INV - 发票 (Invoice)")
    print("  ...")

if __name__ == '__main__':
    init_prefixes()
