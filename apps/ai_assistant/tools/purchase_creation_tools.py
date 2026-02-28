"""
采购模块创建工具

提供采购业务的创建功能，包括询价、收货、退货等
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from django.db import transaction
from django.utils import timezone
from products.models import Product
from purchase.models import (
    PurchaseInquiry,
    PurchaseInquiryItem,
    PurchaseReceipt,
    SupplierQuotation,
    SupplierQuotationItem,
)
from suppliers.models import Supplier

from common.utils import DocumentNumberGenerator

from .base_tool import BaseTool, ToolResult


class CreatePurchaseInquiryTool(BaseTool):
    """创建采购询价单工具"""

    name = "create_purchase_inquiry"
    display_name = "创建采购询价单"
    description = "创建采购询价单并发送给供应商"
    category = "purchase"
    risk_level = "medium"
    require_permission = "purchase.add_purchaseinquiry"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "询价明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "数量"},
                            "target_price": {
                                "type": "number",
                                "description": "目标单价",
                            },
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "supplier_ids": {
                    "type": "array",
                    "description": "供应商ID列表（可选，如果不指定则后续添加）",
                    "items": {"type": "integer"},
                },
                "inquiry_date": {
                    "type": "string",
                    "description": "询价日期（YYYY-MM-DD，默认今天）",
                },
                "required_date": {
                    "type": "string",
                    "description": "要求报价日期（YYYY-MM-DD）",
                },
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["items"],
        }

    def execute(
        self,
        items: list,
        supplier_ids: list = None,
        inquiry_date: str = None,
        required_date: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建询价单"""
        try:
            # 验证明细并计算
            validated_items = []
            total_amount = 0

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])
                target_price = float(item.get("target_price", 0))
                line_total = quantity * target_price
                total_amount += line_total

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "target_price": target_price,
                        "line_total": line_total,
                    }
                )

            # 创建询价单
            with transaction.atomic():
                inquiry_number = DocumentNumberGenerator.generate("purchase_inquiry")
                inquiry_date_obj = (
                    datetime.strptime(inquiry_date, "%Y-%m-%d").date()
                    if inquiry_date
                    else timezone.now().date()
                )

                # 默认要求报价日期为7天后
                required_date_obj = None
                if required_date:
                    required_date_obj = datetime.strptime(required_date, "%Y-%m-%d").date()
                else:
                    required_date_obj = inquiry_date_obj + timedelta(days=7)

                inquiry = PurchaseInquiry.objects.create(
                    inquiry_number=inquiry_number,
                    inquiry_date=inquiry_date_obj,
                    required_date=required_date_obj,
                    total_amount=total_amount,
                    status="draft",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    PurchaseInquiryItem.objects.create(
                        inquiry=inquiry,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        target_price=item_data["target_price"],
                        line_total=item_data["line_total"],
                        created_by=self.user,
                    )

                # 添加供应商（如果有）
                if supplier_ids:
                    for supplier_id in supplier_ids:
                        try:
                            supplier = Supplier.objects.get(id=supplier_id, is_deleted=False)
                            inquiry.suppliers.add(supplier)
                        except Supplier.DoesNotExist:
                            pass

            return ToolResult(
                success=True,
                data={
                    "inquiry_id": inquiry.id,
                    "inquiry_number": inquiry.inquiry_number,
                    "inquiry_date": inquiry.inquiry_date.strftime("%Y-%m-%d"),
                    "required_date": inquiry.required_date.strftime("%Y-%m-%d"),
                    "total_amount": float(total_amount),
                    "items_count": len(validated_items),
                    "suppliers_count": len(supplier_ids) if supplier_ids else 0,
                },
                message=f"询价单 {inquiry.inquiry_number} 创建成功，包含 {len(validated_items)} 个明细",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建询价单失败: {str(e)}")


class AddSupplierQuotationTool(BaseTool):
    """添加供应商报价工具"""

    name = "add_supplier_quotation"
    display_name = "添加供应商报价"
    description = "为询价单添加供应商报价"
    category = "purchase"
    risk_level = "medium"
    require_permission = "purchase.add_supplierquotation"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "inquiry_id": {"type": "integer", "description": "询价单ID"},
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "items": {
                    "type": "array",
                    "description": "报价明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "数量"},
                            "unit_price": {"type": "number", "description": "单价"},
                            "lead_time_days": {
                                "type": "integer",
                                "description": "交货周期（天）",
                            },
                        },
                        "required": ["product_id", "quantity", "unit_price"],
                    },
                },
                "quote_date": {
                    "type": "string",
                    "description": "报价日期（YYYY-MM-DD，默认今天）",
                },
                "valid_until": {
                    "type": "string",
                    "description": "报价有效期至（YYYY-MM-DD）",
                },
                "payment_terms": {"type": "string", "description": "付款条款"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["inquiry_id", "supplier_id", "items"],
        }

    def execute(
        self,
        inquiry_id: int,
        supplier_id: int,
        items: list,
        quote_date: str = None,
        valid_until: str = "",
        payment_terms: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行添加报价"""
        try:
            # 获取询价单
            try:
                inquiry = PurchaseInquiry.objects.get(id=inquiry_id, is_deleted=False)
            except PurchaseInquiry.DoesNotExist:
                return ToolResult(success=False, error=f"询价单ID {inquiry_id} 不存在")

            # 获取供应商
            try:
                supplier = Supplier.objects.get(id=supplier_id, is_deleted=False)
            except Supplier.DoesNotExist:
                return ToolResult(success=False, error=f"供应商ID {supplier_id} 不存在")

            # 验证明细并计算
            validated_items = []
            total_amount = 0

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])
                unit_price = float(item["unit_price"])
                line_total = quantity * unit_price
                total_amount += line_total

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                        "lead_time_days": item.get("lead_time_days", 0),
                    }
                )

            # 创建供应商报价
            with transaction.atomic():
                quote_number = DocumentNumberGenerator.generate("supplier_quotation")
                quote_date_obj = (
                    datetime.strptime(quote_date, "%Y-%m-%d").date()
                    if quote_date
                    else timezone.now().date()
                )

                # 默认有效期为30天
                valid_until_obj = None
                if valid_until:
                    valid_until_obj = datetime.strptime(valid_until, "%Y-%m-%d").date()
                else:
                    valid_until_obj = quote_date_obj + timedelta(days=30)

                quotation = SupplierQuotation.objects.create(
                    quote_number=quote_number,
                    inquiry=inquiry,
                    supplier=supplier,
                    quote_date=quote_date_obj,
                    valid_until=valid_until_obj,
                    total_amount=total_amount,
                    payment_terms=payment_terms,
                    status="submitted",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    SupplierQuotationItem.objects.create(
                        quotation=quotation,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        line_total=item_data["line_total"],
                        lead_time_days=item_data["lead_time_days"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "quotation_id": quotation.id,
                    "quote_number": quotation.quote_number,
                    "inquiry_number": inquiry.inquiry_number,
                    "supplier_name": supplier.name,
                    "quote_date": quotation.quote_date.strftime("%Y-%m-%d"),
                    "valid_until": quotation.valid_until.strftime("%Y-%m-%d"),
                    "total_amount": float(total_amount),
                    "items_count": len(validated_items),
                },
                message=f"供应商报价 {quotation.quote_number} 添加成功，总金额 {total_amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"添加供应商报价失败: {str(e)}")


class CreatePurchaseReceiptTool(BaseTool):
    """创建收货单工具"""

    name = "create_purchase_receipt"
    display_name = "创建收货单"
    description = "为采购订单创建收货单"
    category = "purchase"
    risk_level = "medium"
    require_permission = "purchase.add_purchasereceipt"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "采购订单ID"},
                "items": {
                    "type": "array",
                    "description": "收货明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "收货数量"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "receipt_date": {
                    "type": "string",
                    "description": "收货日期（YYYY-MM-DD，默认今天）",
                },
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["order_id", "items"],
        }

    def execute(
        self,
        order_id: int,
        items: list,
        receipt_date: str = None,
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建收货单"""
        try:
            from purchase.models import PurchaseOrder, PurchaseReceiptItem

            # 获取订单
            try:
                order = PurchaseOrder.objects.get(id=order_id, is_deleted=False)
            except PurchaseOrder.DoesNotExist:
                return ToolResult(success=False, error=f"采购订单ID {order_id} 不存在")

            # 验证明细
            validated_items = []

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                    }
                )

            # 创建收货单
            with transaction.atomic():
                receipt_number = DocumentNumberGenerator.generate("purchase_receipt")
                receipt_date_obj = (
                    datetime.strptime(receipt_date, "%Y-%m-%d").date()
                    if receipt_date
                    else timezone.now().date()
                )

                receipt = PurchaseReceipt.objects.create(
                    receipt_number=receipt_number,
                    purchase_order=order,
                    receipt_date=receipt_date_obj,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    PurchaseReceiptItem.objects.create(
                        receipt=receipt,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "receipt_id": receipt.id,
                    "receipt_number": receipt.receipt_number,
                    "order_number": order.order_number,
                    "supplier_name": order.supplier.name if order.supplier else "",
                    "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d"),
                    "items_count": len(validated_items),
                },
                message=f"收货单 {receipt.receipt_number} 创建成功，包含 {len(validated_items)} 个明细",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建收货单失败: {str(e)}")
