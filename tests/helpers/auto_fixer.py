"""
Django ERP 自动修复器

自动识别和修复常见数据不一致问题:
1. 金额计算错误
2. 数量汇总不一致
3. 应付/应收归集错误
4. 库存数量偏差

使用方法:
    from tests.helpers.auto_fixer import AutoFixer

    fixer = AutoFixer()
    fixer.fix_purchase_order_totals(order)
    fixer.fix_supplier_account_aggregation(account)
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum


class AutoFixer:
    """自动修复器"""

    def __init__(self):
        """初始化修复器"""
        self.fixes_applied = []

    def get_fixes_applied(self):
        """获取已应用的修复列表"""
        return self.fixes_applied

    def log_fix(self, model_name, object_id, issue_type, fix_description):
        """记录修复"""
        self.fixes_applied.append(
            {
                "model": model_name,
                "object_id": object_id,
                "issue_type": issue_type,
                "description": fix_description,
            }
        )

    def fix_purchase_order_totals(self, order):
        """
        修复采购订单总金额

        问题: 订单总金额与明细汇总不一致
        修复: 重新从明细汇总计算总金额
        """
        

        calculated_total = order.items.filter(is_deleted=False).aggregate(total=Sum("line_total"))[
            "total"
        ] or Decimal("0")

        if order.total_amount != calculated_total:
            old_total = order.total_amount
            order.total_amount = calculated_total
            order.save()

            self.log_fix(
                model_name="PurchaseOrder",
                object_id=order.id,
                issue_type="total_amount",
                fix_description=f"总金额从 {old_total} 修复为 {calculated_total}",
            )
            return True

        return False

    def fix_sales_order_totals(self, order):
        """
        修复销售订单总金额

        问题: 订单总金额与明细汇总不一致
        修复: 重新从明细汇总计算总金额
        """
        

        calculated_total = order.items.filter(is_deleted=False).aggregate(total=Sum("line_total"))[
            "total"
        ] or Decimal("0")

        if order.total_amount != calculated_total:
            old_total = order.total_amount
            order.total_amount = calculated_total
            order.save()

            self.log_fix(
                model_name="SalesOrder",
                object_id=order.id,
                issue_type="total_amount",
                fix_description=f"总金额从 {old_total} 修复为 {calculated_total}",
            )
            return True

        return False

    def fix_purchase_receipt_totals(self, receipt):
        """
        修复采购收货单总金额

        问题: 收货单总金额与明细汇总不一致
        修复: 重新从明细汇总计算总金额
        """
        from apps.purchase.models import PurchaseReceipt

        calculated_total = receipt.items.aggregate(total=Sum("line_total"))["total"] or Decimal("0")

        if receipt.total_amount != calculated_total:
            old_total = receipt.total_amount
            receipt.total_amount = calculated_total
            receipt.save()

            self.log_fix(
                model_name="PurchaseReceipt",
                object_id=receipt.id,
                issue_type="total_amount",
                fix_description=f"总金额从 {old_total} 修复为 {calculated_total}",
            )
            return True

        return False

    def fix_sales_delivery_totals(self, delivery):
        """
        修复销售发货单总金额

        问题: 发货单总金额与明细汇总不一致
        修复: 重新从明细汇总计算总金额
        """
        from apps.sales.models import SalesDelivery

        calculated_total = delivery.items.aggregate(total=Sum("line_total"))["total"] or Decimal(
            "0"
        )

        if delivery.total_amount != calculated_total:
            old_total = delivery.total_amount
            delivery.total_amount = calculated_total
            delivery.save()

            self.log_fix(
                model_name="SalesDelivery",
                object_id=delivery.id,
                issue_type="total_amount",
                fix_description=f"总金额从 {old_total} 修复为 {calculated_total}",
            )
            return True

        return False

    def fix_supplier_account_aggregation(self, account):
        """
        修复应付账款归集

        问题: 应付账款主单金额与明细汇总不一致
        修复: 重新从明细汇总计算应付金额
        """
        from apps.finance.models import SupplierAccount, SupplierAccountDetail

        detail_total = account.details.aggregate(total=Sum("amount"))["total"] or Decimal("0")

        if account.invoice_amount != detail_total:
            old_amount = account.invoice_amount
            account.invoice_amount = detail_total

            # 重新计算余额
            paid_amount = account.paid_amount or Decimal("0")
            account.outstanding_amount = detail_total - paid_amount

            account.save()

            self.log_fix(
                model_name="SupplierAccount",
                object_id=account.id,
                issue_type="aggregation",
                fix_description=f"应付金额从 {old_amount} 修复为 {detail_total}",
            )
            return True

        return False

    def fix_customer_account_aggregation(self, account):
        """
        修复应收账款归集

        问题: 应收账款主单金额与明细汇总不一致
        修复: 重新从明细汇总计算应收金额
        """
        from apps.finance.models import CustomerAccount, CustomerAccountDetail

        detail_total = account.details.aggregate(total=Sum("amount"))["total"] or Decimal("0")

        if account.invoice_amount != detail_total:
            old_amount = account.invoice_amount
            account.invoice_amount = detail_total

            # 重新计算余额
            received_amount = account.received_amount or Decimal("0")
            account.outstanding_amount = detail_total - received_amount

            account.save()

            self.log_fix(
                model_name="CustomerAccount",
                object_id=account.id,
                issue_type="aggregation",
                fix_description=f"应收金额从 {old_amount} 修复为 {detail_total}",
            )
            return True

        return False

    def fix_inventory_stock_quantity(self, stock):
        """
        修复库存数量

        问题: 库存数量与库存事务汇总不一致
        修复: 重新从事务记录汇总计算库存数量
        """
        from apps.inventory.models import InventoryTransaction

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
            old_qty = stock.quantity
            stock.quantity = expected_qty
            stock.save()

            self.log_fix(
                model_name="InventoryStock",
                object_id=stock.id,
                issue_type="quantity",
                fix_description=f"库存数量从 {old_qty} 修复为 {expected_qty}",
            )
            return True

        return False

    def fix_purchase_order_received_quantity(self, order):
        """
        修复采购订单已收货数量

        问题: 订单明细的已收货数量与收货单汇总不一致
        修复: 重新从收货单汇总计算已收货数量
        """
        from apps.purchase.models import PurchaseReceipt, PurchaseReceiptItem

        fixed = False

        for item in order.items.all():
            if item.is_deleted:
                continue

            # 计算该明细的收货汇总
            received_qty = PurchaseReceiptItem.objects.filter(
                order_item=item, receipt__status="confirmed"
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            if item.received_quantity != received_qty:
                old_qty = item.received_quantity
                item.received_quantity = received_qty
                item.save()

                self.log_fix(
                    model_name="PurchaseOrderItem",
                    object_id=item.id,
                    issue_type="received_quantity",
                    fix_description=f"已收货数量从 {old_qty} 修复为 {received_qty}",
                )
                fixed = True

        return fixed

    def fix_sales_order_delivered_quantity(self, order):
        """
        修复销售订单已发货数量

        问题: 订单明细的已发货数量与发货单汇总不一致
        修复: 重新从发货单汇总计算已发货数量
        """
        from apps.sales.models import SalesDelivery, SalesDeliveryItem

        fixed = False

        for item in order.items.all():
            if item.is_deleted:
                continue

            # 计算该明细的发货汇总
            delivered_qty = SalesDeliveryItem.objects.filter(
                order_item=item, delivery__status="confirmed"
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

            if item.delivered_quantity != delivered_qty:
                old_qty = item.delivered_quantity
                item.delivered_quantity = delivered_qty
                item.save()

                self.log_fix(
                    model_name="SalesOrderItem",
                    object_id=item.id,
                    issue_type="delivered_quantity",
                    fix_description=f"已发货数量从 {old_qty} 修复为 {delivered_qty}",
                )
                fixed = True

        return fixed

    @transaction.atomic
    def fix_all_purchase_orders(self):
        """修复所有采购订单"""
        from apps.purchase.models import PurchaseOrder

        fixed_count = 0
        orders = PurchaseOrder.objects.all()

        for order in orders:
            if self.fix_purchase_order_totals(order):
                fixed_count += 1

        return fixed_count

    @transaction.atomic
    def fix_all_sales_orders(self):
        """修复所有销售订单"""
        from apps.sales.models import SalesOrder

        fixed_count = 0
        orders = SalesOrder.objects.all()

        for order in orders:
            if self.fix_sales_order_totals(order):
                fixed_count += 1

        return fixed_count

    @transaction.atomic
    def fix_all_supplier_accounts(self):
        """修复所有供应商应付账款"""
        from apps.finance.models import SupplierAccount

        fixed_count = 0
        accounts = SupplierAccount.objects.all()

        for account in accounts:
            if self.fix_supplier_account_aggregation(account):
                fixed_count += 1

        return fixed_count

    @transaction.atomic
    def fix_all_customer_accounts(self):
        """修复所有客户应收账款"""
        from apps.finance.models import CustomerAccount

        fixed_count = 0
        accounts = CustomerAccount.objects.all()

        for account in accounts:
            if self.fix_customer_account_aggregation(account):
                fixed_count += 1

        return fixed_count

    @transaction.atomic
    def fix_all_inventory_stocks(self):
        """修复所有库存数量"""
        from apps.inventory.models import InventoryStock

        fixed_count = 0
        stocks = InventoryStock.objects.all()

        for stock in stocks:
            if self.fix_inventory_stock_quantity(stock):
                fixed_count += 1

        return fixed_count
