"""
Django ERP 数据一致性端到端验证测试

跨模块验证数据一致性:
1. 采购订单与库存一致性
2. 应付账款与收货单一致性
3. 销售订单与发货一致性
4. 应收账款与发货单一致性

关键验证:
- 订单记录的收货数量 = 库存交易的入库数量
- 应付金额 = 收货单汇总 - 退货单汇总
- 订单记录的发货数量 = 库存交易的出库数量
- 应收金额 = 发货单汇总 - 退货单汇总
"""

from decimal import Decimal

import pytest
from django.db.models import Sum
from finance.models import (
    CustomerAccount,
    CustomerAccountDetail,
    SupplierAccount,
    SupplierAccountDetail,
)
from inventory.models import InventoryTransaction
from purchase.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    PurchaseReturn,
    PurchaseReturnItem,
)
from sales.models import (
    SalesDelivery,
    SalesDeliveryItem,
    SalesOrder,
    SalesOrderItem,
    SalesReturn,
    SalesReturnItem,
)


@pytest.mark.django_db
@pytest.mark.e2e
class TestDataConsistencyE2E:
    """数据一致性端到端验证测试"""

    def test_purchase_order_inventory_consistency(self):
        """
        验证: 所有采购订单的收货数量 = 库存交易入库数量

        方法:
        1. 遍历所有已收货的采购订单
        2. 计算订单记录的已收货数量
        3. 计算库存交易的入库数量
        4. 验证两者相等
        """
        issues = []

        # 只检查已部分收货或完全收货的订单
        orders = PurchaseOrder.objects.filter(status__in=["partial_received", "fully_received"])

        for order in orders:
            # 订单记录的已收货数量
            order_received = Decimal("0")
            for item in order.items.all():
                order_received += item.received_quantity or Decimal("0")

            # 库存交易的入库数量
            inventory_received = InventoryTransaction.objects.filter(
                reference_type="purchase_receipt",
                reference_id__in=PurchaseReceipt.objects.filter(purchase_order=order).values_list(
                    "id", flat=True
                ),
                transaction_type="in",
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            if order_received != inventory_received:
                issues.append(
                    {
                        "order_number": order.order_number,
                        "order_received": order_received,
                        "inventory_received": inventory_received,
                        "difference": order_received - inventory_received,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个订单库存不一致: {issues}"

    def test_supplier_account_receipt_consistency(self):
        """
        验证: 应付账款金额 = 收货单汇总 - 退货单汇总

        方法:
        1. 遍历所有供应商应付账款
        2. 计算收货单总金额
        3. 计算退货单总金额
        4. 验证应付金额 = 收货 - 退货
        """
        issues = []

        accounts = SupplierAccount.objects.filter(outstanding_amount__gt=Decimal("0"))

        for account in accounts:
            # 获取关联的采购订单
            order = account.purchase_order

            if not order:
                continue

            # 计算收货单总金额
            receipts = PurchaseReceipt.objects.filter(purchase_order=order, status="confirmed")

            receipt_total = Decimal("0")
            for receipt in receipts:
                receipt_total += receipt.total_amount or Decimal("0")

            # 计算退货单总金额
            returns = PurchaseReturn.objects.filter(
                receipt__purchase_order=order, status="confirmed"
            )

            return_total = Decimal("0")
            for return_order in returns:
                return_total += return_order.total_amount or Decimal("0")

            # 应付账款应该等于收货 - 退货
            expected_amount = receipt_total - return_total

            if account.invoice_amount != expected_amount:
                issues.append(
                    {
                        "order_number": order.order_number,
                        "account_invoice": account.invoice_amount,
                        "receipt_total": receipt_total,
                        "return_total": return_total,
                        "expected_amount": expected_amount,
                        "difference": account.invoice_amount - expected_amount,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个应付账款金额不一致: {issues}"

    def test_sales_order_delivery_consistency(self):
        """
        验证: 所有销售订单的发货数量 = 库存交易出库数量

        方法:
        1. 遍历所有已发货的销售订单
        2. 计算订单记录的已发货数量
        3. 计算库存交易的出库数量
        4. 验证两者相等
        """
        issues = []

        # 只检查已部分发货或完全发货的订单
        orders = SalesOrder.objects.filter(status__in=["partial_delivered", "fully_delivered"])

        for order in orders:
            # 订单记录的已发货数量
            order_delivered = Decimal("0")
            for item in order.items.all():
                order_delivered += item.delivered_quantity or Decimal("0")

            # 库存交易的出库数量
            inventory_delivered = InventoryTransaction.objects.filter(
                reference_type="sales_delivery",
                reference_id__in=SalesDelivery.objects.filter(sales_order=order).values_list(
                    "id", flat=True
                ),
                transaction_type="out",
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            if order_delivered != inventory_delivered:
                issues.append(
                    {
                        "order_number": order.order_number,
                        "order_delivered": order_delivered,
                        "inventory_delivered": inventory_delivered,
                        "difference": order_delivered - inventory_delivered,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个订单发货不一致: {issues}"

    def test_customer_account_delivery_consistency(self):
        """
        验证: 应收账款金额 = 发货单汇总 - 退货单汇总

        方法:
        1. 遍历所有客户应收账款
        2. 计算发货单总金额
        3. 计算退货单总金额
        4. 验证应收金额 = 发货 - 退货
        """
        issues = []

        accounts = CustomerAccount.objects.filter(outstanding_amount__gt=Decimal("0"))

        for account in accounts:
            # 获取关联的销售订单
            order = account.sales_order

            if not order:
                continue

            # 计算发货单总金额
            deliveries = SalesDelivery.objects.filter(sales_order=order, status="confirmed")

            delivery_total = Decimal("0")
            for delivery in deliveries:
                delivery_total += delivery.total_amount or Decimal("0")

            # 计算退货单总金额
            returns = SalesReturn.objects.filter(delivery__sales_order=order, status="confirmed")

            return_total = Decimal("0")
            for return_order in returns:
                return_total += return_order.total_amount or Decimal("0")

            # 应收账款应该等于发货 - 退货
            expected_amount = delivery_total - return_total

            if account.invoice_amount != expected_amount:
                issues.append(
                    {
                        "order_number": order.order_number,
                        "account_invoice": account.invoice_amount,
                        "delivery_total": delivery_total,
                        "return_total": return_total,
                        "expected_amount": expected_amount,
                        "difference": account.invoice_amount - expected_amount,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个应收账款金额不一致: {issues}"

    def test_supplier_account_detail_aggregation(self):
        """
        验证: 供应商应付账款主单金额 = 明细单汇总金额

        方法:
        1. 遍历所有供应商应付账款
        2. 计算明细单汇总金额
        3. 验证主单金额 = 明细汇总
        """
        issues = []

        accounts = SupplierAccount.objects.all()

        for account in accounts:
            # 计算明细单汇总
            detail_total = account.details.aggregate(total=Sum("amount"))["total"] or Decimal("0")

            if account.invoice_amount != detail_total:
                issues.append(
                    {
                        "account_id": account.id,
                        "order_number": (
                            account.purchase_order.order_number if account.purchase_order else None
                        ),
                        "account_invoice": account.invoice_amount,
                        "detail_total": detail_total,
                        "difference": account.invoice_amount - detail_total,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个应付账款明细汇总不一致: {issues}"

    def test_customer_account_detail_aggregation(self):
        """
        验证: 客户应收账款主单金额 = 明细单汇总金额

        方法:
        1. 遍历所有客户应收账款
        2. 计算明细单汇总金额
        3. 验证主单金额 = 明细汇总
        """
        issues = []

        accounts = CustomerAccount.objects.all()

        for account in accounts:
            # 计算明细单汇总
            detail_total = account.details.aggregate(total=Sum("amount"))["total"] or Decimal("0")

            if account.invoice_amount != detail_total:
                issues.append(
                    {
                        "account_id": account.id,
                        "order_number": (
                            account.sales_order.order_number if account.sales_order else None
                        ),
                        "account_invoice": account.invoice_amount,
                        "detail_total": detail_total,
                        "difference": account.invoice_amount - detail_total,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个应收账款明细汇总不一致: {issues}"

    def test_inventory_stock_transaction_consistency(self):
        """
        验证: 库存数量 = 库存事务汇总（入库 - 出库）

        方法:
        1. 遍历所有库存记录
        2. 计算入库事务汇总
        3. 计算出库事务汇总
        4. 验证库存数量 = 入库 - 出库
        """
        from apps.inventory.models import InventoryStock

        issues = []

        stocks = InventoryStock.objects.all()

        for stock in stocks:
            # 计算入库汇总
            qty_in = InventoryTransaction.objects.filter(
                product=stock.product, warehouse=stock.warehouse, transaction_type="in"
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            # 计算出库汇总
            qty_out = InventoryTransaction.objects.filter(
                product=stock.product, warehouse=stock.warehouse, transaction_type="out"
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            # 库存应该等于入库 - 出库
            expected_qty = qty_in - qty_out

            if stock.quantity != expected_qty:
                issues.append(
                    {
                        "product": stock.product.code,
                        "warehouse": stock.warehouse.code,
                        "stock_quantity": stock.quantity,
                        "qty_in": qty_in,
                        "qty_out": qty_out,
                        "expected_qty": expected_qty,
                        "difference": stock.quantity - expected_qty,
                    }
                )

        assert len(issues) == 0, f"发现{len(issues)}个库存数量不一致: {issues}"
