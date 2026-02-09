"""
采购模块扩展工具

提供采购业务的高级查询和操作工具，包括询价、收货、退货、借出等功能
"""

from typing import Any, Dict

from django.db.models import Q
from purchase.models import (
    Borrow,
    PurchaseInquiry,
    PurchaseReceipt,
    PurchaseReturn,
    SupplierQuotation,
)
from suppliers.models import Supplier

from .base_tool import BaseTool, ToolResult


class QueryPurchaseInquiriesTool(BaseTool):
    """查询采购询价单工具"""

    name = "query_purchase_inquiries"
    display_name = "查询询价单"
    description = "查询采购询价单列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "询价状态（draft/sent/quoted/selected/ordered/cancelled）",
                    "enum": ["draft", "sent", "quoted", "selected", "ordered", "cancelled"],
                },
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（询价单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        supplier_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            inquiries = PurchaseInquiry.objects.filter(is_deleted=False)

            if status:
                inquiries = inquiries.filter(status=status)

            if date_from:
                inquiries = inquiries.filter(inquiry_date__gte=date_from)

            if date_to:
                inquiries = inquiries.filter(inquiry_date__lte=date_to)

            if keyword:
                inquiries = inquiries.filter(inquiry_number__icontains=keyword)

            inquiries = inquiries.order_by("-inquiry_date")[:limit]

            # 格式化结果
            results = []
            for inquiry in inquiries:
                # 获取供应商报价数量
                quotes_count = (
                    inquiry.quotes.filter(is_deleted=False).count()
                    if hasattr(inquiry, "quotes")
                    else 0
                )

                results.append(
                    {
                        "id": inquiry.id,
                        "inquiry_number": inquiry.inquiry_number,
                        "inquiry_date": inquiry.inquiry_date.strftime("%Y-%m-%d")
                        if inquiry.inquiry_date
                        else None,
                        "required_date": inquiry.required_date.strftime("%Y-%m-%d")
                        if inquiry.required_date
                        else None,
                        "status": inquiry.status,
                        "status_display": inquiry.get_status_display(),
                        "total_amount": float(inquiry.total_amount) if inquiry.total_amount else 0,
                        "quotes_count": quotes_count,
                        "items_count": inquiry.items.count() if hasattr(inquiry, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个询价单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询询价单失败: {str(e)}")


class QuerySupplierQuotationsTool(BaseTool):
    """查询供应商报价工具"""

    name = "query_supplier_quotations"
    display_name = "查询供应商报价"
    description = "查询供应商报价列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "报价状态（draft/submitted/selected/rejected/cancelled）",
                    "enum": ["draft", "submitted", "selected", "rejected", "cancelled"],
                },
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "inquiry_id": {"type": "integer", "description": "询价单ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（报价单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        supplier_id: int = None,
        inquiry_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            quotations = SupplierQuotation.objects.filter(is_deleted=False)

            if status:
                quotations = quotations.filter(status=status)

            if supplier_id:
                quotations = quotations.filter(supplier_id=supplier_id)

            if inquiry_id:
                quotations = quotations.filter(inquiry_id=inquiry_id)

            if date_from:
                quotations = quotations.filter(quote_date__gte=date_from)

            if date_to:
                quotations = quotations.filter(quote_date__lte=date_to)

            if keyword:
                quotations = quotations.filter(quote_number__icontains=keyword)

            quotations = quotations.select_related("supplier", "inquiry").order_by("-quote_date")[
                :limit
            ]

            # 格式化结果
            results = []
            for quot in quotations:
                results.append(
                    {
                        "id": quot.id,
                        "quote_number": quot.quote_number,
                        "supplier_name": quot.supplier.name if quot.supplier else "",
                        "inquiry_number": quot.inquiry.inquiry_number if quot.inquiry else "",
                        "quote_date": quot.quote_date.strftime("%Y-%m-%d")
                        if quot.quote_date
                        else None,
                        "valid_until": quot.valid_until.strftime("%Y-%m-%d")
                        if quot.valid_until
                        else None,
                        "status": quot.status,
                        "status_display": quot.get_status_display(),
                        "total_amount": float(quot.total_amount) if quot.total_amount else 0,
                        "items_count": quot.items.count() if hasattr(quot, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个供应商报价")

        except Exception as e:
            return ToolResult(success=False, error=f"查询供应商报价失败: {str(e)}")


class QueryPurchaseReceiptsTool(BaseTool):
    """查询收货单工具"""

    name = "query_purchase_receipts"
    display_name = "查询收货单"
    description = "查询采购收货单列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "收货状态（pending/received/inspected/rejected/cancelled）",
                    "enum": ["pending", "received", "inspected", "rejected", "cancelled"],
                },
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（收货单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        supplier_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            receipts = PurchaseReceipt.objects.filter(is_deleted=False)

            if status:
                receipts = receipts.filter(status=status)

            if supplier_id:
                receipts = receipts.filter(purchase_order__supplier_id=supplier_id)

            if date_from:
                receipts = receipts.filter(receipt_date__gte=date_from)

            if date_to:
                receipts = receipts.filter(receipt_date__lte=date_to)

            if keyword:
                receipts = receipts.filter(receipt_number__icontains=keyword)

            receipts = receipts.select_related("purchase_order__supplier").order_by(
                "-receipt_date"
            )[:limit]

            # 格式化结果
            results = []
            for receipt in receipts:
                results.append(
                    {
                        "id": receipt.id,
                        "receipt_number": receipt.receipt_number,
                        "order_number": receipt.purchase_order.order_number
                        if receipt.purchase_order
                        else "",
                        "supplier_name": receipt.purchase_order.supplier.name
                        if receipt.purchase_order and receipt.purchase_order.supplier
                        else "",
                        "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d")
                        if receipt.receipt_date
                        else None,
                        "status": receipt.status,
                        "status_display": receipt.get_status_display(),
                        "items_count": receipt.items.count() if hasattr(receipt, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个收货单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询收货单失败: {str(e)}")


class QueryPurchaseReturnsTool(BaseTool):
    """查询采购退货工具"""

    name = "query_purchase_returns"
    display_name = "查询采购退货"
    description = "查询采购退货单列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "退货状态（pending/approved/rejected/completed/cancelled）",
                    "enum": ["pending", "approved", "rejected", "completed", "cancelled"],
                },
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（退货单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        supplier_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            returns = PurchaseReturn.objects.filter(is_deleted=False)

            if status:
                returns = returns.filter(status=status)

            if supplier_id:
                returns = returns.filter(supplier_id=supplier_id)

            if date_from:
                returns = returns.filter(return_date__gte=date_from)

            if date_to:
                returns = returns.filter(return_date__lte=date_to)

            if keyword:
                returns = returns.filter(return_number__icontains=keyword)

            returns = returns.select_related("supplier").order_by("-return_date")[:limit]

            # 格式化结果
            results = []
            for ret in returns:
                results.append(
                    {
                        "id": ret.id,
                        "return_number": ret.return_number,
                        "supplier_name": ret.supplier.name if ret.supplier else "",
                        "return_date": ret.return_date.strftime("%Y-%m-%d")
                        if ret.return_date
                        else None,
                        "return_reason": ret.return_reason,
                        "return_reason_display": ret.get_return_reason_display(),
                        "status": ret.status,
                        "status_display": ret.get_status_display(),
                        "items_count": ret.items.count() if hasattr(ret, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个采购退货单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询采购退货失败: {str(e)}")


class QueryPurchaseBorrowsTool(BaseTool):
    """查询采购借出工具"""

    name = "query_purchase_borrows"
    display_name = "查询采购借出"
    description = "查询采购借出单列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "借出状态（pending/approved/rejected/borrowed/returned/cancelled）",
                    "enum": [
                        "pending",
                        "approved",
                        "rejected",
                        "borrowed",
                        "returned",
                        "cancelled",
                    ],
                },
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（借出单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        supplier_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            borrows = Borrow.objects.filter(is_deleted=False)

            if status:
                borrows = borrows.filter(status=status)

            if supplier_id:
                borrows = borrows.filter(supplier_id=supplier_id)

            if date_from:
                borrows = borrows.filter(borrow_date__gte=date_from)

            if date_to:
                borrows = borrows.filter(borrow_date__lte=date_to)

            if keyword:
                borrows = borrows.filter(borrow_number__icontains=keyword)

            borrows = borrows.select_related("supplier").order_by("-borrow_date")[:limit]

            # 格式化结果
            results = []
            for borrow in borrows:
                results.append(
                    {
                        "id": borrow.id,
                        "borrow_number": borrow.borrow_number,
                        "supplier_name": borrow.supplier.name if borrow.supplier else "",
                        "borrow_date": borrow.borrow_date.strftime("%Y-%m-%d")
                        if borrow.borrow_date
                        else None,
                        "expected_return_date": borrow.expected_return_date.strftime("%Y-%m-%d")
                        if borrow.expected_return_date
                        else None,
                        "status": borrow.status,
                        "status_display": borrow.get_status_display(),
                        "items_count": borrow.items.count() if hasattr(borrow, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个采购借出单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询采购借出失败: {str(e)}")
