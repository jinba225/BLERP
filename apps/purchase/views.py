"""
Purchase views for the ERP system.
"""
import logging

from core.models import PAYMENT_METHOD_CHOICES
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from common.utils import DocumentNumberGenerator

from .models import (
    Borrow,
    BorrowItem,
    PurchaseInquiry,
    PurchaseInquiryItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    PurchaseRequest,
    PurchaseReturn,
    PurchaseReturnItem,
    SupplierQuotation,
)

logger = logging.getLogger(__name__)


@login_required
def order_list(request):
    """List all purchase orders with search and filter."""
    orders = PurchaseOrder.objects.filter(is_deleted=False).select_related(
        "supplier", "buyer", "warehouse"
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(supplier__name__icontains=search)
            | Q(reference_number__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        orders = orders.filter(status=status)

    # Filter by payment status
    payment_status = request.GET.get("payment_status", "")
    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    # Filter by supplier
    supplier_id = request.GET.get("supplier", "")
    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        orders = orders.filter(order_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    orders = orders.order_by("-created_at")

    # Pagination
    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Get suppliers for filter dropdown
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)

    # Calculate statistics
    all_orders = PurchaseOrder.objects.filter(is_deleted=False)
    stats = {
        "draft_count": all_orders.filter(status="draft").count(),
        "pending_count": all_orders.filter(
            status__in=["pending", "sent", "confirmed", "partial_received"]
        ).count(),
        "approved_count": all_orders.filter(status__in=["approved", "fully_received"]).count(),
        "completed_count": all_orders.filter(status="completed").count(),
    }

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "payment_status": payment_status,
        "supplier_id": supplier_id,
        "date_from": date_from,
        "date_to": date_to,
        "suppliers": suppliers,
        "total_count": paginator.count,
        "stats": stats,
        "order_statuses": PurchaseOrder.ORDER_STATUS,
    }
    return render(request, "modules/purchase/order_list.html", context)


@login_required
def order_detail(request, pk):
    """Display purchase order details."""
    order = get_object_or_404(
        PurchaseOrder.objects.filter(is_deleted=False)
        .select_related("supplier", "buyer", "warehouse", "approved_by", "invoice")
        .prefetch_related("items__product"),
        pk=pk,
    )

    # 计算每个订单明细的剩余数量
    items_with_remaining = []
    for item in order.items.all():
        remaining_quantity = item.quantity - item.received_quantity
        items_with_remaining.append(
            {
                "item": item,
                "remaining_quantity": remaining_quantity,
            }
        )

    # 检查是否有待收货状态的收货单
    pending_receipt = PurchaseReceipt.objects.filter(
        purchase_order=order, status="pending", is_deleted=False
    ).first()

    # 检查是否可以申请付款(已审核且有已收货产品,且未申请过付款)
    total_received = sum(item.received_quantity for item in order.items.all())
    can_request_payment = (
        order.status in ["approved", "partial_received", "fully_received"]
        and total_received > 0
        and order.payment_status == "unpaid"
    )

    # 检查是否可以开票
    can_invoice = (
        order.status in ["fully_received", "partial_received"]
        and not order.invoice  # 未关联发票
        and total_received > 0  # 有已收货产品
    )

    # 查询关联的入库单
    from inventory.models import InboundOrder

    inbound_orders = InboundOrder.objects.filter(
        reference_type="purchase_order", reference_id=order.id, is_deleted=False
    ).order_by("-created_at")

    # 查询关联的出库单(采购退货)
    from inventory.models import OutboundOrder

    outbound_orders = OutboundOrder.objects.filter(
        reference_type="purchase_return",
        reference_id__in=order.returns.filter(is_deleted=False).values_list("id", flat=True),
        is_deleted=False,
    ).order_by("-created_at")

    context = {
        "order": order,
        "items": order.items.all(),
        "items_with_remaining": items_with_remaining,
        "can_edit": order.status == "draft",
        "can_approve": order.status == "draft",
        "can_delete": order.status == "draft",  # 只有草稿状态可以删除
        "pending_receipt": pending_receipt,
        "can_request_payment": can_request_payment,
        "can_invoice": can_invoice,
        "inbound_orders": inbound_orders,
        "outbound_orders": outbound_orders,
    }
    return render(request, "modules/purchase/order_detail.html", context)


@login_required
@transaction.atomic
def order_create(request):
    """Create a new purchase order."""
    if request.method == "POST":
        import json
        from decimal import Decimal

        from .services import PurchaseOrderService

        order_data = {
            "supplier_id": request.POST.get("supplier"),
            "order_date": request.POST.get("order_date") or timezone.now().date(),  # 使用 date 对象
            "required_date": request.POST.get("required_date") or None,
            "promised_date": request.POST.get("promised_date") or None,
            "buyer_id": request.POST.get("buyer") or None,
            "warehouse_id": request.POST.get("warehouse") or None,
            "tax_rate": request.POST.get("tax_rate", 13),
            "discount_rate": request.POST.get("discount_rate", 0),
            "shipping_cost": request.POST.get("shipping_cost", 0),
            "currency": request.POST.get("currency", "CNY"),
            "delivery_address": request.POST.get("delivery_address", ""),
            "delivery_contact": request.POST.get("delivery_contact", ""),
            "delivery_phone": request.POST.get("delivery_phone", ""),
            "payment_terms": request.POST.get("payment_terms", ""),
            "reference_number": request.POST.get("reference_number", ""),
            "notes": request.POST.get("notes", ""),
            "internal_notes": request.POST.get("internal_notes", ""),
            "status": "draft",
        }

        # 处理日期字段 - 将字符串转换为 date 对象
        from datetime import datetime

        date_fields = ["order_date", "required_date", "promised_date"]
        for field in date_fields:
            value = order_data.get(field)
            if value and isinstance(value, str):
                try:
                    order_data[field] = datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    order_data[field] = None

        try:
            # Process order items
            items_json = request.POST.get("items_json", "[]")
            items_raw_data = json.loads(items_json)
            print(f"=== DEBUG: 收到 {len(items_raw_data)} 条明细 ===")
            print(f"items_json: {items_json}")
            items_data = []

            for item in items_raw_data:
                product_id = item.get("product_id")
                print(
                    f"DEBUG: 处理明细 - product_id={product_id}, 类型={type(product_id)}, 值={repr(product_id)}"
                )
                if product_id:
                    items_data.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": Decimal(item.get("quantity", 0)),
                            "unit_price": Decimal(item.get("unit_price", 0)),
                            "discount_rate": Decimal(item.get("discount_rate", 0)),
                        }
                    )
            print(f"DEBUG: 有效明细数量: {len(items_data)}")
            print(f"DEBUG: items_data={items_data}")

            order = PurchaseOrderService.create_order(request.user, order_data, items_data)

            messages.success(request, f"采购订单 {order.order_number} 创建成功！")
            return redirect("purchase:order_detail", pk=order.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    import json

    from django.contrib.auth import get_user_model
    from django.core.serializers.json import DjangoJSONEncoder
    from inventory.models import Warehouse
    from products.models import Product
    from suppliers.models import Supplier

    User = get_user_model()

    # 查询数据（保留原有查询用于兼容）
    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True).prefetch_related(
        "contacts"
    )
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    buyers = User.objects.filter(is_active=True)
    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    # 序列化JSON数据用于可搜索下拉框（包含联系人信息）
    suppliers_data = []
    for supplier in suppliers:
        # 获取主要联系人或第一个联系人
        primary_contact = None
        if hasattr(supplier, "contacts") and supplier.contacts.exists():
            primary_contact = (
                supplier.contacts.filter(is_deleted=False, is_active=True)
                .order_by("-is_primary")
                .first()
            )
            if primary_contact:
                primary_contact = {
                    "name": primary_contact.name,
                    "phone": primary_contact.phone or primary_contact.mobile or "",
                    "email": primary_contact.email or "",
                }

        suppliers_data.append(
            {
                "id": supplier.id,
                "name": supplier.name,
                "code": supplier.code,
                "payment_terms": supplier.payment_terms or "",
                "address": supplier.address or "",
                "primary_contact": primary_contact or {},
            }
        )

    suppliers_json = json.dumps(suppliers_data, cls=DjangoJSONEncoder)
    warehouses_json = json.dumps(
        list(warehouses.values("id", "name", "code")), cls=DjangoJSONEncoder
    )
    products_json = json.dumps(
        list(
            products.values(
                "id", "name", "code", "specifications", "unit__name", "cost_price", "selling_price"
            )
        ),
        cls=DjangoJSONEncoder,
    )

    # 获取默认采购员（当前登录用户）
    default_buyer = request.user if request.user.is_active else None

    # 获取默认收货仓库（主仓库）
    default_warehouse = None
    try:
        default_warehouse = Warehouse.get_main_warehouse()
    except Warehouse.DoesNotExist:
        pass

    context = {
        "suppliers": suppliers,
        "warehouses": warehouses,
        "buyers": buyers,
        "products": products,
        "suppliers_json": suppliers_json,
        "warehouses_json": warehouses_json,
        "products_json": products_json,
        "PAYMENT_METHOD_CHOICES": PAYMENT_METHOD_CHOICES,
        "action": "create",
        "default_buyer": default_buyer,
        "default_warehouse": default_warehouse,
    }
    return render(request, "modules/purchase/order_form.html", context)


@login_required
@transaction.atomic
def order_update(request, pk):
    """Update an existing purchase order."""
    import json
    from decimal import Decimal

    from .services import PurchaseOrderService

    order = get_object_or_404(
        PurchaseOrder.objects.select_related("supplier", "buyer", "warehouse").prefetch_related(
            "items__product"
        ),
        pk=pk,
        is_deleted=False,
    )

    if order.status != "draft":
        messages.error(request, "只有草稿状态的订单可以编辑")
        return redirect("purchase:order_detail", pk=pk)

    if request.method == "POST":
        order_data = {
            "supplier_id": request.POST.get("supplier"),
            "order_date": request.POST.get("order_date"),
            "required_date": request.POST.get("required_date") or None,
            "promised_date": request.POST.get("promised_date") or None,
            "buyer_id": request.POST.get("buyer") or None,
            "warehouse_id": request.POST.get("warehouse") or None,
            "tax_rate": request.POST.get("tax_rate", 13),
            "discount_rate": request.POST.get("discount_rate", 0),
            "shipping_cost": request.POST.get("shipping_cost", 0),
            "currency": request.POST.get("currency", "CNY"),
            "delivery_address": request.POST.get("delivery_address", ""),
            "delivery_contact": request.POST.get("delivery_contact", ""),
            "delivery_phone": request.POST.get("delivery_phone", ""),
            "payment_terms": request.POST.get("payment_terms", ""),
            "reference_number": request.POST.get("reference_number", ""),
            "notes": request.POST.get("notes", ""),
            "internal_notes": request.POST.get("internal_notes", ""),
        }

        try:
            # Process order items from JSON
            items_json = request.POST.get("items_json", "[]")
            items_raw_data = json.loads(items_json)
            items_data = []

            for item in items_raw_data:
                if item.get("product_id"):
                    items_data.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": Decimal(item.get("quantity", 0)),
                            "unit_price": Decimal(item.get("unit_price", 0)),
                            "discount_rate": Decimal(item.get("discount_rate", 0)),
                        }
                    )

            PurchaseOrderService.update_order(order, request.user, order_data, items_data)

            messages.success(request, f"采购订单 {order.order_number} 更新成功！")
            return redirect("purchase:order_detail", pk=order.pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET request
    import json

    from django.contrib.auth import get_user_model
    from django.core.serializers.json import DjangoJSONEncoder
    from inventory.models import Warehouse
    from products.models import Product
    from suppliers.models import Supplier

    User = get_user_model()

    # 查询数据（保留原有查询用于兼容）
    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)
    warehouses = Warehouse.objects.filter(is_deleted=False)
    buyers = User.objects.filter(is_active=True)
    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    # 序列化JSON数据用于可搜索下拉框
    suppliers_json = json.dumps(
        list(suppliers.values("id", "name", "code", "payment_terms", "address")),
        cls=DjangoJSONEncoder,
    )
    warehouses_json = json.dumps(
        list(warehouses.values("id", "name", "code")), cls=DjangoJSONEncoder
    )
    products_json = json.dumps(
        list(
            products.values(
                "id", "name", "code", "specifications", "unit__name", "cost_price", "selling_price"
            )
        ),
        cls=DjangoJSONEncoder,
    )

    context = {
        "order": order,
        "suppliers": suppliers,
        "warehouses": warehouses,
        "buyers": buyers,
        "products": products,
        "suppliers_json": suppliers_json,
        "warehouses_json": warehouses_json,
        "products_json": products_json,
        "PAYMENT_METHOD_CHOICES": PAYMENT_METHOD_CHOICES,
        "action": "update",
    }
    return render(request, "modules/purchase/order_form.html", context)


@login_required
def order_delete(request, pk):
    """Delete (soft delete) a purchase order."""
    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    if order.status != "draft":
        messages.error(request, "只有草稿状态的订单可以删除")
        return redirect("purchase:order_detail", pk=pk)

    if request.method == "POST":
        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.deleted_by = request.user
        order.save()

        messages.success(request, f"采购订单 {order.order_number} 已删除")
        return redirect("purchase:order_list")

    context = {
        "order": order,
    }
    return render(request, "modules/purchase/order_confirm_delete.html", context)


# ==================== Purchase Request (询价单) Views ====================


@login_required
def request_list(request):
    """
    List all purchase requests with search and filter capabilities.
    """
    requests = (
        PurchaseRequest.objects.filter(is_deleted=False)
        .select_related("department", "requester", "approved_by")
        .order_by("-created_at")
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        requests = requests.filter(
            Q(request_number__icontains=search)
            | Q(department__name__icontains=search)
            | Q(purpose__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        requests = requests.filter(status=status)

    # Filter by priority
    priority = request.GET.get("priority", "")
    if priority:
        requests = requests.filter(priority=priority)

    # Filter by department
    department_id = request.GET.get("department", "")
    if department_id:
        requests = requests.filter(department_id=department_id)

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        requests = requests.filter(request_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        requests = requests.filter(request_date__lte=date_to)

    # Pagination
    paginator = Paginator(requests, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Get departments for filter dropdown
    from departments.models import Department

    departments = Department.objects.filter(is_deleted=False)

    # Calculate statistics
    all_requests = PurchaseRequest.objects.filter(is_deleted=False)
    stats = {
        "pending_count": all_requests.filter(status="pending").count(),
        "approved_count": all_requests.filter(status="approved").count(),
        "converted_count": all_requests.filter(status="converted").count(),
        "rejected_count": all_requests.filter(status="rejected").count(),
    }

    context = {
        "page_obj": page_obj,
        "search_query": search,
        "search": search,
        "status": status,
        "priority": priority,
        "department_id": department_id,
        "date_from": date_from,
        "date_to": date_to,
        "departments": departments,
        "total_count": paginator.count,
        "stats": stats,
        "request_statuses": PurchaseRequest.REQUEST_STATUS,
    }
    return render(request, "modules/purchase/request_list.html", context)


@login_required
def request_detail(request, pk):
    """
    Display purchase request details.
    """
    purchase_request = get_object_or_404(
        PurchaseRequest.objects.filter(is_deleted=False)
        .select_related("department", "requester", "approved_by", "converted_order")
        .prefetch_related("items__product", "items__preferred_supplier"),
        pk=pk,
    )

    # Get suppliers and warehouses for approval modal
    from inventory.models import Warehouse
    from suppliers.models import Supplier

    # Find preferred supplier from items (if any)
    preferred_supplier = None
    for item in purchase_request.items.all():
        if item.preferred_supplier:
            preferred_supplier = item.preferred_supplier
            break

    context = {
        "request": purchase_request,
        "items": purchase_request.items.all(),
        "can_edit": purchase_request.status == "draft",
        "can_convert": False,  # 简化流程，不再需要手动转换
        "can_approve": purchase_request.status == "draft" and not purchase_request.approved_by,
        "suppliers": Supplier.objects.filter(is_deleted=False, is_active=True).order_by("name"),
        "warehouses": Warehouse.objects.filter(is_deleted=False).order_by("name"),
        "preferred_supplier": preferred_supplier,
    }
    return render(request, "modules/purchase/request_detail.html", context)


@login_required
@transaction.atomic
def request_create(request):
    """
    Create a new purchase request (draft status, pending approval).
    """
    if request.method == "POST":
        import json
        from decimal import Decimal

        from .services import PurchaseRequestService

        request_data = {
            "department_id": None,  # 不再使用部门字段
            "requester": request.user,  # 申请人默认为当前登录用户
            "request_date": request.POST.get("request_date"),
            "required_date": request.POST.get("required_date"),
            "priority": request.POST.get("priority", "normal"),
            "purpose": "",  # 不再使用采购目的字段
            "justification": request.POST.get("justification", ""),
            "budget_code": "",  # 不再使用预算科目字段
            "notes": "",  # 不再使用备注字段
            "status": "draft",  # 创建为草稿状态
        }

        try:
            # Process request items
            items_json = request.POST.get("items_json", "[]")
            items_raw_data = json.loads(items_json)
            items_data = []

            for item in items_raw_data:
                if item.get("product_id"):
                    items_data.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": Decimal(item.get("quantity", 0)),
                            "estimated_price": Decimal(item.get("estimated_price", 0)),
                            "preferred_supplier_id": item.get("preferred_supplier_id") or None,
                            "specifications": item.get("specifications", ""),
                            "notes": item.get("notes", ""),
                        }
                    )

            # 创建采购申请单（草稿状态）
            purchase_request = PurchaseRequestService.create_request(
                request.user, request_data, items_data
            )

            messages.success(request, f"采购申请单 {purchase_request.request_number} 创建成功！等待采购部门审核")
            return redirect("purchase:request_detail", pk=purchase_request.pk)

        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from products.models import Product
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code"
    )

    context = {
        "suppliers": suppliers,
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
        "action": "create",
    }
    return render(request, "modules/purchase/request_form.html", context)


@login_required
@transaction.atomic
def request_update(request, pk):
    """
    Update an existing purchase request.
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Only draft requests can be edited
    if purchase_request.status != "draft":
        messages.error(request, "只有草稿状态的采购申请单可以编辑")
        return redirect("purchase:request_detail", pk=pk)

    if request.method == "POST":
        import json
        from decimal import Decimal

        from .services import PurchaseRequestService

        request_data = {
            "department_id": None,  # 不再使用部门字段
            "request_date": request.POST.get("request_date"),
            "required_date": request.POST.get("required_date"),
            "priority": request.POST.get("priority", "normal"),
            "purpose": "",  # 不再使用采购目的字段
            "justification": request.POST.get("justification", ""),
            "budget_code": "",  # 不再使用预算科目字段
            "notes": "",  # 不再使用备注字段
        }

        try:
            # Process request items from JSON
            items_json = request.POST.get("items_json", "[]")
            items_raw_data = json.loads(items_json)
            items_data = []

            for item in items_raw_data:
                if item.get("product_id"):
                    items_data.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": Decimal(item.get("quantity", 0)),
                            "estimated_price": Decimal(item.get("estimated_price", 0)),
                            "preferred_supplier_id": item.get("preferred_supplier_id") or None,
                            "specifications": item.get("specifications", ""),
                            "notes": item.get("notes", ""),
                        }
                    )

            PurchaseRequestService.update_request(
                purchase_request, request.user, request_data, items_data
            )

            messages.success(request, f"采购申请单 {purchase_request.request_number} 更新成功！")
            return redirect("purchase:request_detail", pk=purchase_request.pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET request
    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from products.models import Product
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code"
    )

    context = {
        "request": purchase_request,
        "suppliers": suppliers,
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
        "action": "update",
    }
    return render(request, "modules/purchase/request_form.html", context)


@login_required
def request_delete(request, pk):
    """
    Delete (soft delete) a purchase request.
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Only draft requests can be deleted
    if purchase_request.status != "draft":
        messages.error(request, "只有草稿状态的采购申请单可以删除")
        return redirect("purchase:request_detail", pk=pk)

    if request.method == "POST":
        purchase_request.is_deleted = True
        purchase_request.deleted_at = timezone.now()
        purchase_request.deleted_by = request.user
        purchase_request.save()

        messages.success(request, f"采购申请单 {purchase_request.request_number} 已删除")
        return redirect("purchase:request_list")

    context = {
        "request": purchase_request,
    }
    return render(request, "modules/purchase/request_confirm_delete.html", context)


@login_required
@transaction.atomic
def request_convert_to_order(request, pk):
    """
    Convert a purchase request to a purchase order.
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Check if already converted
    if purchase_request.status == "ordered":
        messages.info(request, "此采购申请单已经转换为采购订单")
        return redirect("purchase:order_detail", pk=purchase_request.converted_order.pk)

    # Check if request is approved
    if purchase_request.status != "approved":
        messages.error(request, "只有已批准状态的采购申请单可以转换为采购订单")
        return redirect("purchase:request_detail", pk=pk)

    if request.method == "POST":
        try:
            from decimal import Decimal

            from .services import PurchaseRequestService

            # Get supplier from form
            supplier_id = request.POST.get("supplier")
            warehouse_id = request.POST.get("warehouse")

            # Validate supplier
            if not supplier_id:
                messages.error(request, "请选择供应商")
                return redirect("purchase:request_convert", pk=pk)

            # Collect prices for each item
            items_prices = {}
            missing_prices = []
            for item in purchase_request.items.all():
                price_key = f"price_{item.id}"
                price_value = request.POST.get(price_key)
                if price_value and price_value.strip():
                    try:
                        price = Decimal(price_value)
                        if price < 0:
                            messages.error(request, f"产品 {item.product.name} 的价格不能为负数")
                            return redirect("purchase:request_convert", pk=pk)
                        items_prices[item.id] = price
                    except Exception:
                        messages.error(request, f"产品 {item.product.name} 的价格格式不正确")
                        return redirect("purchase:request_convert", pk=pk)
                else:
                    missing_prices.append(item.product.name)

            if missing_prices:
                messages.error(request, f"请为以下产品输入单价：{', '.join(missing_prices)}")
                return redirect("purchase:request_convert", pk=pk)

            # Convert using service with prices
            order = PurchaseRequestService.convert_request_to_order(
                purchase_request, request.user, supplier_id, warehouse_id, items_prices=items_prices
            )

            messages.success(
                request, f"采购申请单 {purchase_request.request_number} 已成功转换为采购订单 {order.order_number}"
            )
            return redirect("purchase:order_update", pk=order.pk)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("purchase:request_convert", pk=pk)
        except Exception as e:
            messages.error(request, f"转换失败：{str(e)}")
            return redirect("purchase:request_convert", pk=pk)

    # GET request
    from inventory.models import Warehouse
    from suppliers.models import Supplier

    # Get preferred supplier from items
    preferred_supplier = None
    for item in purchase_request.items.all():
        if item.preferred_supplier:
            preferred_supplier = item.preferred_supplier
            break

    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        "request": purchase_request,
        "preferred_supplier": preferred_supplier,
        "suppliers": suppliers,
        "warehouses": warehouses,
    }
    return render(request, "modules/purchase/request_convert.html", context)


@login_required
@transaction.atomic
def request_approve(request, pk):
    """
    Approve a purchase request and optionally auto-create purchase order.
    """
    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:request_detail", pk=pk)

    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Check if already approved
    if purchase_request.approved_by:
        messages.warning(request, "此采购申请单已经审核过了")
        return redirect("purchase:request_detail", pk=pk)

    # Check status (must be draft)
    if purchase_request.status != "draft":
        messages.error(request, "只有草稿状态的采购申请单可以审核")
        return redirect("purchase:request_detail", pk=pk)

    try:
        from inventory.models import Warehouse

        # Get supplier and warehouse from form
        supplier_id = request.POST.get("supplier")
        warehouse_id = request.POST.get("warehouse")

        if not supplier_id:
            messages.error(request, "请选择供应商")
            return redirect("purchase:request_detail", pk=pk)

        # Auto-select main warehouse if not specified
        if not warehouse_id:
            # Try to find warehouse with "主仓库" in name, otherwise use first warehouse
            main_warehouse = Warehouse.objects.filter(
                is_deleted=False, name__icontains="主仓库"
            ).first()

            if not main_warehouse:
                # Fallback to first available warehouse
                main_warehouse = Warehouse.objects.filter(is_deleted=False).order_by("id").first()

            if main_warehouse:
                warehouse_id = main_warehouse.id

        # Approve and auto-create order using new model method
        order, success_message = purchase_request.approve_and_convert_to_order(
            approved_by_user=request.user,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id if warehouse_id else None,
        )

        messages.success(request, success_message)

        # Redirect to order detail if order was created, otherwise to request detail
        if order:
            return redirect("purchase:order_detail", pk=order.pk)
        else:
            return redirect("purchase:request_detail", pk=pk)

    except ValueError as e:
        messages.error(request, str(e))
        return redirect("purchase:request_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("purchase:request_detail", pk=pk)


@login_required
@transaction.atomic
def request_reject(request, pk):
    """
    Reject a purchase request.
    """
    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:request_detail", pk=pk)

    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Check status - only draft can be rejected
    if purchase_request.status != "draft":
        messages.error(request, "只有草稿状态的采购申请单可以拒绝")
        return redirect("purchase:request_detail", pk=pk)

    try:
        rejection_reason = request.POST.get("rejection_reason", "")

        # Keep status as draft, just record rejection info
        purchase_request.rejection_reason = rejection_reason
        purchase_request.save()

        messages.success(request, f"采购申请单 {purchase_request.request_number} 已拒绝")
        return redirect("purchase:request_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"操作失败：{str(e)}")
        return redirect("purchase:request_detail", pk=pk)


@login_required
def request_unapprove_confirm(request, pk):
    """显示撤销采购申请审核确认页面"""
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    if purchase_request.status != "approved":
        messages.error(request, "只有已审核状态的采购申请单才能撤销")
        return redirect("purchase:request_detail", pk=pk)

    # 检查是否已转换为采购订单
    if purchase_request.converted_order:
        messages.error(request, "采购申请单已转换为采购订单，无法撤销审核")
        return redirect("purchase:request_detail", pk=pk)

    context = {
        "purchase_request": purchase_request,
        "warning_message": "撤销审核后，将恢复为草稿状态。",
    }
    return render(request, "modules/purchase/request_confirm_unapprove.html", context)


@login_required
@transaction.atomic
def request_unapprove(request, pk):
    """撤销采购申请审核"""
    if request.method != "POST":
        purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)
        context = {
            "purchase_request": purchase_request,
            "warning_message": "撤销审核后，将恢复为草稿状态。",
        }
        return render(request, "modules/purchase/request_confirm_unapprove.html", context)

    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    try:
        purchase_request.unapprove_request(user=request.user)
        messages.success(request, f"采购申请单 {purchase_request.request_number} 审核已撤销")
        return redirect("purchase:request_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"撤销失败：{str(e)}")
        return redirect("purchase:request_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"撤销失败：{str(e)}")
        logger.error(f"撤销采购申请失败: {str(e)}", exc_info=True)
        return redirect("purchase:request_detail", pk=pk)


@login_required
@transaction.atomic
def request_submit(request, pk):
    """
    Submit a purchase request for approval.
    """
    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:request_detail", pk=pk)

    purchase_request = get_object_or_404(PurchaseRequest, pk=pk, is_deleted=False)

    # Check status
    if purchase_request.status != "draft":
        messages.error(request, "只有草稿状态的采购申请单可以提交")
        return redirect("purchase:request_detail", pk=pk)

    # Check if has items
    if not purchase_request.items.exists():
        messages.error(request, "采购申请单没有明细，无法提交")
        return redirect("purchase:request_detail", pk=pk)

    try:
        # Keep status as draft - no intermediate state needed
        # Just validate that it's ready for approval
        purchase_request.save()

        messages.success(request, f"采购申请单 {purchase_request.request_number} 已提交，等待审核")
        return redirect("purchase:request_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"提交失败：{str(e)}")
        return redirect("purchase:request_detail", pk=pk)


# ==================== Purchase Order Approval Views ====================


@login_required
@transaction.atomic
def order_approve(request, pk):
    """
    Approve a purchase order.
    """
    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:order_detail", pk=pk)

    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    try:
        receipt = order.approve_order(approved_by_user=request.user, warehouse=order.warehouse)

        if receipt:
            messages.success(
                request, f"采购订单 {order.order_number} 审核通过，已自动生成收货单 {receipt.receipt_number}"
            )
        else:
            messages.success(request, f"采购订单 {order.order_number} 审核通过")

        return redirect("purchase:order_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("purchase:order_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("purchase:order_detail", pk=pk)


@login_required
@transaction.atomic
def order_unapprove(request, pk):
    """
    Unapprove (cancel approval) a purchase order.
    撤销采购订单审核
    """
    if request.method != "POST":
        order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)
        # 显示确认页面
        context = {
            "order": order,
            "warning_message": "撤销审核后，订单将恢复到草稿状态，待收货状态的收货单将被删除。",
        }
        return render(request, "modules/purchase/order_confirm_unapprove.html", context)

    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    try:
        order.unapprove_order(user=request.user)
        logger.info(f"撤销审核订单 {order.order_number}，添加成功消息")
        messages.success(request, f"采购订单 {order.order_number} 审核已撤销")
        logger.info(f"消息已添加到请求对象")
        return redirect("purchase:order_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"撤销失败：{str(e)}")
        return redirect("purchase:order_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"撤销失败：{str(e)}")
        logger.error(f"撤销订单失败: {str(e)}", exc_info=True)
        return redirect("purchase:order_detail", pk=pk)


@login_required
@transaction.atomic
def order_invoice(request, pk):
    """
    Create supplier invoice for a purchase order.
    供应商开票：创建发票记录并更新订单状态为已开票
    """
    from decimal import Decimal

    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    # 验证：订单必须已收货（部分或全部）
    if order.status not in ["partial_received", "fully_received"]:
        messages.error(request, "只有已收货的订单才能开票")
        return redirect("purchase:order_detail", pk=pk)

    # 验证：订单未开票
    if order.invoice:
        messages.warning(request, f"该订单已开票，发票号：{order.invoice.invoice_number}")
        return redirect("purchase:order_detail", pk=pk)

    # 验证：必须有已收货产品
    total_received = sum(item.received_quantity for item in order.items.filter(is_deleted=False))
    if total_received <= 0:
        messages.error(request, "订单没有已收货的产品，无法开票")
        return redirect("purchase:order_detail", pk=pk)

    if request.method == "POST":
        try:
            from finance.models import Invoice, InvoiceItem

            # 生成发票号
            invoice_number = f"INV{timezone.now().strftime('%Y%m%d')}{str(order.pk).zfill(6)}"

            # 计算发票金额（基于订单总金额）
            amount_excluding_tax = order.subtotal
            tax_rate = order.tax_rate
            tax_amount = order.tax_amount
            total_amount = order.total_amount

            # 创建发票
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                invoice_type="purchase",  # 采购发票
                status="received",  # 供应商开具，我们已收到
                supplier=order.supplier,
                invoice_date=timezone.now().date(),
                amount_excluding_tax=amount_excluding_tax,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total_amount,
                reference_type="purchase_order",
                reference_id=str(order.pk),
                reference_number=order.order_number,
                remark=f"采购订单 {order.order_number} 供应商开票",
                created_by=request.user,
            )

            # 创建发票明细（基于订单明细）
            for order_item in order.items.filter(is_deleted=False):
                # 计算明细税额
                item_subtotal = order_item.line_total
                item_tax_rate = order_item.tax_rate if hasattr(order_item, "tax_rate") else tax_rate
                item_tax_amount = item_subtotal * (Decimal(str(item_tax_rate)) / Decimal("100"))

                # 获取产品单位名称（unit是外键，需要获取name属性）
                unit_name = ""
                if order_item.product.unit:
                    unit_name = order_item.product.unit.name

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=order_item.product,
                    description=order_item.product.name,  # InvoiceItem.description是必填字段
                    specification=order_item.product.specifications
                    if hasattr(order_item.product, "specifications")
                    else "",
                    unit=unit_name,
                    quantity=order_item.quantity,
                    unit_price=order_item.unit_price,
                    amount=item_subtotal,
                    tax_rate=item_tax_rate,
                    tax_amount=item_tax_amount,
                    sort_order=order_item.sort_order,
                    created_by=request.user,
                )

            # 更新订单状态
            order.invoice = invoice
            order.status = "invoiced"
            order.invoiced_by = request.user
            order.invoiced_at = timezone.now()
            order.save()

            messages.success(request, f"采购订单 {order.order_number} 已开票，发票号：{invoice.invoice_number}")
            return redirect("purchase:order_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"开票失败：{str(e)}")
            logger.error(f"开票失败: {str(e)}", exc_info=True)
            return redirect("purchase:order_detail", pk=pk)

    # GET请求：显示开票确认页面
    context = {
        "order": order,
        "total_received": total_received,
    }
    return render(request, "modules/purchase/order_invoice_confirm.html", context)


# ==================== Purchase Receipt Views ====================


@login_required
def receipt_list(request):
    """List all purchase receipts with search and filter."""
    receipts = PurchaseReceipt.objects.filter(is_deleted=False).select_related(
        "purchase_order__supplier", "warehouse", "received_by"
    )

    # 按订单号筛选（精确匹配或模糊匹配）
    order_number = request.GET.get("order_number", "")
    if order_number:
        receipts = receipts.filter(purchase_order__order_number__icontains=order_number)

    # Search
    search = request.GET.get("search", "")
    if search:
        receipts = receipts.filter(
            Q(receipt_number__icontains=search)
            | Q(purchase_order__supplier__name__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        receipts = receipts.filter(status=status)

    # Filter by warehouse
    warehouse_id = request.GET.get("warehouse", "")
    if warehouse_id:
        receipts = receipts.filter(warehouse_id=warehouse_id)

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        receipts = receipts.filter(receipt_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        receipts = receipts.filter(receipt_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    receipts = receipts.order_by("-created_at")

    # Pagination
    paginator = Paginator(receipts, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Get warehouses for filter dropdown
    from inventory.models import Warehouse

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        "page_obj": page_obj,
        "order_number": order_number,
        "search": search,
        "status": status,
        "warehouse_id": warehouse_id,
        "date_from": date_from,
        "date_to": date_to,
        "warehouses": warehouses,
        "total_count": paginator.count,
    }
    return render(request, "modules/purchase/receipt_list.html", context)


@login_required
def receipt_detail(request, pk):
    """Display purchase receipt details."""
    receipt = get_object_or_404(
        PurchaseReceipt.objects.filter(is_deleted=False)
        .select_related("purchase_order__supplier", "warehouse", "received_by")
        .prefetch_related("items__order_item__product"),
        pk=pk,
    )

    context = {
        "receipt": receipt,
        "items": receipt.items.all(),
        "can_edit": receipt.status == "draft",
        "can_receive": receipt.status in ["draft", "received"],
    }
    return render(request, "modules/purchase/receipt_detail.html", context)


@login_required
@transaction.atomic
def receipt_create(request, order_pk):
    """Create a new purchase receipt from order."""
    from decimal import Decimal

    order = get_object_or_404(PurchaseOrder, pk=order_pk, is_deleted=False)

    # 允许已审核、部分收货状态的订单创建收货单
    if order.status not in ["approved", "partial_received"]:
        messages.error(request, "只有已审核或部分收货状态的采购订单可以创建收货单")
        return redirect("purchase:order_detail", pk=order_pk)

    # 检查是否已存在该订单的待收货状态的收货单
    pending_receipt = PurchaseReceipt.objects.filter(
        purchase_order=order, status="pending", is_deleted=False
    ).first()

    if pending_receipt:
        messages.info(request, f"该订单已存在待收货单 {pending_receipt.receipt_number}，已自动跳转")
        return redirect("purchase:receipt_detail", pk=pending_receipt.pk)

    if request.method == "POST":
        receipt_data = {
            "receipt_number": DocumentNumberGenerator.generate(
                "receipt", model_class=PurchaseReceipt  # 传递模型类以支持重用已删除单据编号
            ),  # 使用 IN 前缀
            "purchase_order": order,
            "receipt_date": request.POST.get("receipt_date"),
            "warehouse_id": request.POST.get("warehouse"),
            "notes": request.POST.get("notes", ""),
            "status": "pending",  # 新创建的收货单为待收货状态
        }

        try:
            receipt = PurchaseReceipt(**receipt_data)
            receipt.created_by = request.user
            receipt.save()

            # Process receipt items from form data
            total_received = Decimal("0")
            for order_item in order.items.filter(is_deleted=False):
                # 获取每个明细的收货数量
                quantity_key = f"received_quantity_{order_item.id}"
                received_qty = request.POST.get(quantity_key, "0")

                try:
                    received_qty = Decimal(received_qty)
                except BaseException:
                    received_qty = Decimal("0")

                # 只处理有收货数量的明细
                if received_qty > 0:
                    # 计算剩余可收货数量（考虑已确认收货 + 已创建但未确认的收货）
                    confirmed_qty = order_item.received_quantity or Decimal("0")

                    # 获取该订单明细的所有收货单明细（包括未确认的）
                    pending_receipt_items = PurchaseReceiptItem.objects.filter(
                        order_item=order_item, is_deleted=False
                    ).exclude(receipt__status__in=["received", "cancelled"])

                    pending_qty = pending_receipt_items.aggregate(
                        total=models.Sum("received_quantity")
                    )["total"] or Decimal("0")

                    # 真正的剩余可收货数量
                    remaining_qty = order_item.quantity - confirmed_qty - pending_qty

                    if received_qty > remaining_qty:
                        raise ValueError(
                            f"产品 {order_item.product.name} 的收货数量 ({received_qty}) "
                            f"不能超过剩余数量 ({remaining_qty})。"
                            f"已确认收货: {confirmed_qty}, 已创建未确认: {pending_qty}, "
                            f"订单数量: {order_item.quantity}"
                        )

                    PurchaseReceiptItem.objects.create(
                        receipt=receipt,
                        order_item=order_item,
                        received_quantity=received_qty,
                        batch_number=request.POST.get(f"batch_number_{order_item.id}", ""),
                        notes=request.POST.get(f"notes_{order_item.id}", ""),
                        created_by=request.user,
                    )

                    total_received += received_qty

            if total_received == 0:
                raise ValueError("请至少输入一个产品的收货数量")

            messages.success(request, f"收货单 {receipt.receipt_number} 创建成功！请继续确认收货。")
            return redirect("purchase:receipt_detail", pk=receipt.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    from inventory.models import Warehouse

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    # Get order items with received quantity and calculate remaining
    order_items = []
    for item in order.items.filter(is_deleted=False):
        remaining_quantity = item.quantity - item.received_quantity
        order_items.append(
            {
                "item": item,
                "remaining_quantity": remaining_quantity,
            }
        )

    context = {
        "order": order,
        "order_items": order_items,
        "warehouses": warehouses,
        "action": "create",
    }
    return render(request, "modules/purchase/receipt_form.html", context)


@login_required
@transaction.atomic
def receipt_receive(request, pk):
    """
    Confirm receipt and create stock movement.
    """
    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:receipt_detail", pk=pk)

    receipt = get_object_or_404(PurchaseReceipt, pk=pk, is_deleted=False)

    # Check status - pending or partial can be confirmed
    if receipt.status not in ["pending", "partial"]:
        messages.error(request, "只有待收货或部分收货状态的收货单可以确认收货")
        return redirect("purchase:receipt_detail", pk=pk)

    try:
        from decimal import Decimal

        from inventory.models import InventoryTransaction

        # Process received quantities from form
        total_received = Decimal("0")
        items_to_receive = []

        for item in receipt.items.all():
            # Get received quantity from POST data
            quantity_key = f"received_quantity_{item.id}"
            batch_key = f"batch_number_{item.id}"
            notes_key = f"notes_{item.id}"

            received_qty = request.POST.get(quantity_key, "0")
            try:
                received_qty = Decimal(received_qty)
            except BaseException:
                received_qty = Decimal("0")

            # Update item with received quantity, batch number and notes
            if received_qty > 0:
                item.received_quantity = received_qty
                item.batch_number = request.POST.get(batch_key, "")
                item.notes = request.POST.get(notes_key, "")
                item.save()

                total_received += received_qty
                items_to_receive.append(item)

        # Validate that at least some items were received
        if total_received == 0:
            messages.error(request, "请至少输入一个产品的收货数量")
            return redirect("purchase:receipt_detail", pk=pk)

        # Update receipt status
        receipt.status = "received"
        receipt.received_by = request.user
        receipt.save()

        # 获取或创建应付主单
        from finance.models import SupplierAccount, SupplierAccountDetail

        from common.utils import DocumentNumberGenerator

        parent_account = SupplierAccount.get_or_create_for_order(receipt.purchase_order)

        # 检查是否为借用单转采购订单（通过订单备注是否包含借用单号判断）
        # 这与 Borrow.converted_orders 属性的逻辑保持一致
        from purchase.models import Borrow

        is_from_borrow = Borrow.objects.filter(
            borrow_number__in=receipt.purchase_order.notes.split(), is_deleted=False
        ).exists()

        source_borrow = None
        if is_from_borrow:
            # 获取来源借用单
            borrow_numbers = [b for b in receipt.purchase_order.notes.split() if b.startswith("BO")]
            if borrow_numbers:
                source_borrow = Borrow.objects.filter(
                    borrow_number=borrow_numbers[0], is_deleted=False
                ).first()

        if is_from_borrow and source_borrow:
            # ========== 借用单转采购订单：创建借用仓→主仓的调拨单据 ==========
            from inventory.models import StockTransfer, StockTransferItem, Warehouse
            from inventory.services import StockTransferService

            from common.utils import DocumentNumberGenerator

            try:
                borrow_wh = Warehouse.get_borrow_warehouse()
            except Warehouse.DoesNotExist:
                messages.error(request, "借用仓不存在，请先创建借用仓")
                return redirect("purchase:receipt_detail", pk=pk)

            # 获取目标仓库（主仓）
            main_wh = receipt.warehouse
            if not main_wh:
                messages.error(request, "收货仓库未设置")
                return redirect("purchase:receipt_detail", pk=pk)

            # 创建调拨单（系统自动生成）
            transfer = StockTransfer.objects.create(
                transfer_number=DocumentNumberGenerator.generate("transfer"),
                from_warehouse=borrow_wh,
                to_warehouse=main_wh,
                status="draft",
                transfer_date=receipt.receipt_date,
                notes=f"借用转采购自动调拨 - 采购订单：{receipt.purchase_order.order_number}",
                is_auto_generated=True,  # 标识为系统自动生成
                created_by=request.user,
            )

            # 创建调拨明细并执行调拨
            shipped_quantities = {}
            received_quantities = {}

            for item in items_to_receive:
                # 创建调拨明细
                transfer_item = StockTransferItem.objects.create(
                    transfer=transfer,
                    product=item.order_item.product,
                    requested_quantity=item.received_quantity,
                    unit_cost=item.order_item.unit_price,
                    notes=f"来自借用单 {source_borrow.borrow_number}",
                    created_by=request.user,
                )

                shipped_quantities[transfer_item.id] = item.received_quantity
                received_quantities[transfer_item.id] = item.received_quantity

            # 审核调拨单
            transfer.status = "approved"
            transfer.approved_by = request.user
            transfer.approved_at = timezone.now()
            transfer.save()

            # 发货（扣减借用仓库存）
            StockTransferService.ship_transfer(transfer, request.user, shipped_quantities)

            # 收货（增加主仓库存）
            StockTransferService.receive_transfer(transfer, request.user, received_quantities)

            messages.success(request, f"已创建调拨单 {transfer.transfer_number} 并完成库存调拨")

        else:
            # ========== 普通采购订单：正常入库到收货仓库 ==========
            for item in items_to_receive:
                InventoryTransaction.objects.create(
                    warehouse=receipt.warehouse,
                    product=item.order_item.product,
                    transaction_type="in",
                    quantity=item.received_quantity,
                    reference_type="purchase_receipt",
                    reference_id=str(receipt.id),
                    reference_number=receipt.receipt_number,
                    notes=f"采购收货 - {receipt.purchase_order.order_number}",
                    operator=request.user,
                    created_by=request.user,
                )

        # Update order item received quantity
        for item in items_to_receive:
            # 更新订单明细的已收货数量
            item.order_item.received_quantity += item.received_quantity
            item.order_item.save()

            # ========== 自动生成正应付明细 ==========
            # 计算应收金额：收货数量 × 单价
            detail_amount = item.received_quantity * item.order_item.unit_price

            # 生成明细单号
            detail_number = DocumentNumberGenerator.generate(
                "account_detail", model_class=SupplierAccountDetail  # 传递模型类以支持编号重用
            )

            # 创建正应付明细
            SupplierAccountDetail.objects.create(
                detail_number=detail_number,
                detail_type="receipt",  # 收货正应付
                supplier=receipt.purchase_order.supplier,
                purchase_order=receipt.purchase_order,
                receipt=receipt,
                amount=detail_amount,  # 正数
                allocated_amount=Decimal("0"),
                parent_account=parent_account,
                business_date=receipt.receipt_date,
                notes=f"收货单 {receipt.receipt_number} 收货 {item.received_quantity} 件",
                created_by=request.user,
            )

        # 自动归集应付主单
        parent_account.aggregate_from_details()

        # Check if order is fully received
        order = receipt.purchase_order
        all_received = all(item.received_quantity >= item.quantity for item in order.items.all())

        # 更新订单状态（如果已开票，则保持invoiced状态）
        if order.status != "invoiced":  # 只有未开票时才更新收货状态
            if all_received:
                order.status = "fully_received"
            else:
                order.status = "partial_received"
        order.save()

        messages.success(
            request, f"收货单 {receipt.receipt_number} 确认收货成功，共收货 {total_received} 件，库存已更新，应付明细已生成"
        )
        return redirect("purchase:receipt_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"收货确认失败：{str(e)}")
        return redirect("purchase:receipt_detail", pk=pk)


@login_required
def receipt_unapprove_confirm(request, pk):
    """显示撤销收货确认页面"""
    receipt = get_object_or_404(PurchaseReceipt, pk=pk, is_deleted=False)

    if receipt.status != "received":
        messages.error(request, "只有已收货状态的收货单才能撤销")
        return redirect("purchase:receipt_detail", pk=pk)

    context = {
        "receipt": receipt,
        "warning_message": "撤销收货后，将回滚库存变动，冲销应付账款明细，并更新订单状态。",
    }
    return render(request, "modules/purchase/receipt_confirm_unapprove.html", context)


@login_required
@transaction.atomic
def receipt_unapprove(request, pk):
    """撤销收货确认"""
    if request.method != "POST":
        receipt = get_object_or_404(PurchaseReceipt, pk=pk, is_deleted=False)
        # 显示确认页面
        context = {
            "receipt": receipt,
            "warning_message": "撤销收货后，将回滚库存变动，冲销应付账款明细，并更新订单状态。",
        }
        return render(request, "modules/purchase/receipt_confirm_unapprove.html", context)

    receipt = get_object_or_404(PurchaseReceipt, pk=pk, is_deleted=False)

    try:
        receipt.unapprove_receipt(user=request.user)
        messages.success(request, f"收货单 {receipt.receipt_number} 收货已撤销")
        return redirect("purchase:receipt_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"撤销失败：{str(e)}")
        return redirect("purchase:receipt_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"撤销失败：{str(e)}")
        logger.error(f"撤销收货失败: {str(e)}", exc_info=True)
        return redirect("purchase:receipt_detail", pk=pk)


@login_required
@transaction.atomic
def order_request_payment(request, pk):
    """
    申请付款：为采购订单创建应付账款记录

    根据已收货数量计算应付金额（支持分批收货）
    """
    from datetime import datetime, timedelta
    from decimal import Decimal

    from finance.models import SupplierAccount

    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    # 验证订单状态（已审核且有收货记录）
    if order.status not in ["approved", "partial_received", "fully_received"]:
        messages.error(request, "只能为已审核且已有收货的订单申请付款")
        return redirect("purchase:order_detail", pk=pk)

    # 检查是否有已收货的产品
    total_received = sum(item.received_quantity for item in order.items.all())
    if total_received == 0:
        messages.error(request, "该订单暂无已收货产品，无法申请付款")
        return redirect("purchase:order_detail", pk=pk)

    # 检查是否已存在应付账款
    existing_account = SupplierAccount.objects.filter(
        purchase_order=order, is_deleted=False
    ).first()

    if existing_account:
        messages.info(request, f"该订单已存在应付账款记录（编号：{existing_account.invoice_number}）")
        return redirect("finance:supplier_account_detail", pk=existing_account.pk)

    try:
        # 计算到期日期（默认30天后）
        due_date = datetime.now().date() + timedelta(days=30)

        # 生成应付账款编号（使用PAY前缀）
        from django.utils import timezone

        # 手动生成PAY格式的编号
        today = timezone.now().date()
        date_str = today.strftime("%y%m%d")
        # 获取当天已有的PAY编号数量
        today_count = SupplierAccount.objects.filter(
            invoice_number__startswith=f"PAY{date_str}", is_deleted=False
        ).count()
        account_number = f"PAY{date_str}{today_count + 1:03d}"

        # 根据已收货数量计算应付金额
        received_amount = Decimal("0")
        for item in order.items.all():
            if item.received_quantity > 0:
                # 已收货数量 × 单价 = 应付金额
                received_amount += item.received_quantity * item.unit_price

        # 创建应付账款记录（金额为已收货部分的金额）
        account = SupplierAccount.objects.create(
            supplier=order.supplier,
            purchase_order=order,
            invoice_number=account_number,
            invoice_date=datetime.now().date(),
            due_date=due_date,
            status="pending",
            invoice_amount=received_amount,
            paid_amount=Decimal("0"),
            balance=received_amount,
            notes=f"采购订单 {order.order_number} 应付账款（已收货{total_received}件，金额¥{received_amount:.2f}）",
            created_by=request.user,
        )

        # 更新订单付款状态
        order.payment_status = "unpaid"
        order.save()

        messages.success(
            request, f"已成功申请付款，生成应付账款记录（编号：{account_number}），应付金额：¥{received_amount:.2f}"
        )
        return redirect("finance:supplier_account_detail", pk=account.pk)

    except Exception as e:
        messages.error(request, f"申请付款失败：{str(e)}")
        return redirect("purchase:order_detail", pk=pk)


# ==================== Purchase Return Views ====================


@login_required
def return_list(request):
    """List all purchase returns with search and filter."""
    returns = PurchaseReturn.objects.filter(is_deleted=False).select_related(
        "purchase_order__supplier", "approved_by"
    )

    # 按订单号筛选（精确匹配或模糊匹配）
    order_number = request.GET.get("order_number", "")
    if order_number:
        returns = returns.filter(purchase_order__order_number__icontains=order_number)

    # Search
    search = request.GET.get("search", "")
    if search:
        returns = returns.filter(
            Q(return_number__icontains=search) | Q(purchase_order__supplier__name__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        returns = returns.filter(status=status)

    # Filter by reason
    reason = request.GET.get("reason", "")
    if reason:
        returns = returns.filter(reason=reason)

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        returns = returns.filter(return_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        returns = returns.filter(return_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    returns = returns.order_by("-created_at")

    # Pagination
    paginator = Paginator(returns, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "order_number": order_number,
        "search": search,
        "status": status,
        "reason": reason,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
    }
    return render(request, "modules/purchase/return_list.html", context)


@login_required
def return_detail(request, pk):
    """Display purchase return details."""
    return_order = get_object_or_404(
        PurchaseReturn.objects.filter(is_deleted=False)
        .select_related("purchase_order__supplier", "receipt", "approved_by")
        .prefetch_related("items__order_item__product"),
        pk=pk,
    )

    # 查询关联的出库单
    from inventory.models import OutboundOrder

    outbound_order = OutboundOrder.objects.filter(
        reference_type="purchase_return", reference_id=return_order.id, is_deleted=False
    ).first()

    context = {
        "return": return_order,
        "items": return_order.items.all(),
        "can_edit": return_order.status == "pending",
        "can_approve": return_order.status == "pending",
        "outbound_order": outbound_order,
    }
    return render(request, "modules/purchase/return_detail.html", context)


@login_required
@transaction.atomic
def return_create(request, order_pk):
    """Create a new purchase return from order."""
    from decimal import Decimal

    from django.db.models import Sum

    order = get_object_or_404(PurchaseOrder, pk=order_pk, is_deleted=False)

    if not order.approved_by:
        messages.error(request, "只有已审核的采购订单可以创建退货单")
        return redirect("purchase:order_detail", pk=order_pk)

    if request.method == "POST":
        import json

        return_data = {
            "return_number": DocumentNumberGenerator.generate(
                "purchase_return", model_class=PurchaseReturn  # 传递模型类以支持重用已删除单据编号
            ),
            "purchase_order": order,
            "return_date": request.POST.get("return_date"),
            "reason": request.POST.get("reason"),
            "notes": request.POST.get("notes", ""),
            "status": "pending",
        }

        try:
            return_order = PurchaseReturn(**return_data)
            return_order.created_by = request.user
            return_order.save()

            # Process return items
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)
            total_refund = Decimal("0")

            for item_data in items_data:
                if item_data.get("order_item_id") and int(item_data.get("return_quantity", 0)) > 0:
                    order_item = PurchaseOrderItem.objects.get(pk=item_data["order_item_id"])
                    return_quantity = int(item_data["return_quantity"])

                    # 验证1: 退货总量不能超过订单数量
                    if return_quantity > order_item.quantity:
                        raise ValueError(
                            f"产品 {order_item.product.name} 的退货数量 ({return_quantity}) "
                            f"不能超过订单数量 ({order_item.quantity})"
                        )

                    # 验证2: 退货数量不能超过可退货数量
                    from django.db.models import Sum

                    returned_quantity = (
                        PurchaseReturnItem.objects.filter(
                            order_item=order_item,
                            purchase_return__purchase_order=order,
                            purchase_return__is_deleted=False,
                            purchase_return__status__in=["approved", "returned", "completed"],
                        ).aggregate(total=Sum("quantity"))["total"]
                        or 0
                    )

                    returnable_quantity = order_item.received_quantity - returned_quantity

                    if return_quantity > returnable_quantity:
                        raise ValueError(
                            f"产品 {order_item.product.name} 的退货数量 ({return_quantity}) "
                            f"不能超过可退货数量 ({returnable_quantity}。"
                            f"已收货{order_item.received_quantity} - 已退货{returned_quantity})"
                        )

                    unit_price = order_item.unit_price

                    PurchaseReturnItem.objects.create(
                        purchase_return=return_order,
                        order_item=order_item,
                        quantity=return_quantity,
                        unit_price=unit_price,
                        condition="",
                        batch_number=item_data.get("batch_number", ""),
                        notes="",
                        created_by=request.user,
                    )

                    total_refund += return_quantity * unit_price

            # Update refund amount
            return_order.refund_amount = total_refund
            return_order.save()

            messages.success(request, f"退货单 {return_order.return_number} 创建成功！")
            return redirect("purchase:return_detail", pk=return_order.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    # 显示所有订单明细（订单数量、已收货数量、未收货数量、已退货数量、可退货数量）
    order_items_data = []
    for item in order.items.all():
        # 计算该订单明细的已退货数量（只计算已审核的退货单）
        from django.db.models import Sum

        returned_quantity = (
            PurchaseReturnItem.objects.filter(
                order_item=item,
                purchase_return__purchase_order=order,
                purchase_return__is_deleted=False,
                purchase_return__status__in=["approved", "returned", "completed"],
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        # 未收货数量 = 订单数量 - 已收货数量
        unreceived_quantity = item.quantity - item.received_quantity

        # 可退货数量 = 已收货数量 - 已退货数量
        returnable_quantity = item.received_quantity - returned_quantity

        order_items_data.append(
            {
                "pk": item.pk,
                "product": item.product,
                "quantity": item.quantity,
                "received_quantity": item.received_quantity,
                "unreceived_quantity": unreceived_quantity,
                "returned_quantity": returned_quantity,  # 已退货数量
                "returnable_quantity": returnable_quantity,  # 可退货数量
                "unit_price": item.unit_price,
                "line_total": item.line_total,
            }
        )

    context = {
        "order": order,
        "order_items": order_items_data,
        "action": "create",
    }
    return render(request, "modules/purchase/return_form.html", context)


@login_required
@transaction.atomic
def return_approve(request, pk):
    """
    Approve purchase return.

    业务逻辑（三种场景）：

    案例1：全收货场景
    - 订单数量100，已收货100，未收货0
    - 退货30 → 扣已收货30（已收货→70） → 生成30件负应付账款

    案例2：未全收货，退货量≤未收货量
    - 订单数量100，已收货60，未收货40
    - 退货20 → 减订单数量20（订单→80） → 已收货不变，无财务记录

    案例3：未全收货，退货量>未收货量
    - 订单数量100，已收货60，未收货40
    - 退货50 → 减订单数量40（订单→60） + 扣已收货10（已收货→50） → 生成10件负应付账款

    增强功能（2026-02-11）：
    - 负应付明细生成后自动直接核销到正应付明细
    - 如果原订单已开票，自动生成红字发票
    """
    from decimal import Decimal

    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("purchase:return_detail", pk=pk)

    return_order = get_object_or_404(PurchaseReturn, pk=pk, is_deleted=False)

    if return_order.status != "pending":
        messages.error(request, "只有待处理状态的退货单可以审核")
        return redirect("purchase:return_detail", pk=pk)

    try:
        # 更新退货单状态
        return_order.status = "approved"
        return_order.approved_by = request.user
        return_order.approved_at = timezone.now()
        return_order.save()

        # 获取订单的默认仓库(从收货单获取,如果有的话)
        warehouse = None
        first_receipt = (
            return_order.purchase_order.receipts.filter(is_deleted=False)
            .order_by("created_at")
            .first()
        )
        if first_receipt and first_receipt.warehouse:
            warehouse = first_receipt.warehouse

        # 创建出库单
        from inventory.models import OutboundOrder, OutboundOrderItem

        outbound_order = None
        if warehouse:
            outbound_order = OutboundOrder.objects.create(
                order_number=DocumentNumberGenerator.generate("OBO"),
                warehouse=warehouse,
                order_type="purchase_return",  # 采购退货出库
                status="approved",  # 退货审核即完成出库
                order_date=timezone.now().date(),
                reference_number=return_order.return_number,
                reference_type="purchase_return",
                reference_id=return_order.id,
                notes=f"采购退货单 {return_order.return_number} 审核自动生成",
                created_by=request.user,
            )

        total_refund = Decimal("0")
        items_with_received_return = []  # 记录需要生成红字发票明细的项目
        negative_details = []  # 记录创建的负应付明细

        # 处理每个退货明细
        for item in return_order.items.all():
            order_item = item.order_item
            return_quantity = item.quantity

            # 计算未收货数量
            unreceived_quantity = order_item.quantity - order_item.received_quantity

            if return_quantity <= unreceived_quantity:
                # === 案例2：退货量 ≤ 未收货量，只减订单数量 ===
                # 例如：订单100，已收60，未收40，退货20 → 订单数量-20 → 80
                order_item.quantity -= return_quantity
                order_item.save()

            else:
                # === 案例1或3：退货量 > 未收货量，需要扣已收货 ===

                # 先计算扣减未收货的数量
                unreceived_return = min(return_quantity, unreceived_quantity)
                # 剩余从已收货扣除
                received_return = return_quantity - unreceived_return

                if unreceived_return > 0:
                    # 减少订单数量（未收货部分）
                    order_item.quantity -= unreceived_return
                    order_item.save()

                if received_return > 0:
                    # 注意：不扣减received_quantity，保持实际收货数量不变
                    # received_quantity应该始终记录实际收到的数量
                    # 退货记录单独存储在PurchaseReturn表中
                    # 可退货数量 = received_quantity - 已退货数量

                    # 创建库存交易(退货出库)
                    if warehouse:
                        from inventory.models import InventoryTransaction

                        InventoryTransaction.objects.create(
                            transaction_type="out",
                            product=order_item.product,
                            warehouse=warehouse,
                            quantity=received_return,
                            unit_cost=order_item.unit_price,
                            total_cost=received_return * order_item.unit_price,
                            reference_type="return",
                            reference_id=str(return_order.pk),
                            reference_number=return_order.return_number,
                            notes=f"采购退货：{return_order.return_number}",
                            created_by=request.user,
                        )

                        # 创建出库单明细
                        if outbound_order:
                            OutboundOrderItem.objects.create(
                                outbound_order=outbound_order,
                                product=order_item.product,
                                location=None,
                                quantity=received_return,
                                batch_number=item.batch_number,
                                notes=item.notes,
                                created_by=request.user,
                            )

                    # 累计退款金额
                    total_refund += received_return * item.unit_price

                    # ========== 自动生成负应付明细 ==========
                    # 每个明细单独生成负应付记录
                    from finance.models import SupplierAccount, SupplierAccountDetail

                    # 获取或创建应付主单
                    parent_account = SupplierAccount.get_or_create_for_order(
                        return_order.purchase_order
                    )

                    # 计算负应付金额（负数）
                    negative_amount = -(received_return * item.unit_price)

                    # 生成明细单号
                    detail_number = DocumentNumberGenerator.generate(
                        "account_detail", model_class=SupplierAccountDetail  # 传递模型类以支持编号重用
                    )

                    # 创建负应付明细
                    negative_detail = SupplierAccountDetail.objects.create(
                        detail_number=detail_number,
                        detail_type="return",  # 退货负应付
                        supplier=return_order.purchase_order.supplier,
                        purchase_order=return_order.purchase_order,
                        return_order=return_order,
                        amount=negative_amount,  # 负数
                        allocated_amount=Decimal("0"),
                        parent_account=parent_account,
                        business_date=return_order.return_date,
                        notes=f"退货单 {return_order.return_number} 退货 {received_return} 件",
                        created_by=request.user,
                    )
                    negative_details.append(negative_detail)

                    # 记录需要生成红字发票明细的项目
                    items_with_received_return.append(
                        {
                            "item": item,
                            "order_item": order_item,
                            "received_return": received_return,
                            "negative_detail": negative_detail,
                        }
                    )

        # ========== 新增：直接核销负应付明细 ==========
        if total_refund > 0 and negative_details:
            written_off_amount = Decimal("0")
            for negative_detail in negative_details:
                # 计算该负应付明细的绝对金额
                abs_amount = abs(negative_detail.amount)
                # 执行直接核销
                negative_detail.direct_write_off(amount=abs_amount, write_off_by=request.user)
                written_off_amount += abs_amount

        # ========== 新增：生成红字发票 ==========
        original_invoice = return_order.purchase_order.invoice
        credit_note = None
        if original_invoice and total_refund > 0:
            from finance.models import Invoice, InvoiceItem

            # 生成红字发票
            credit_note = Invoice.objects.create(
                invoice_number=DocumentNumberGenerator.generate("invoice_cn"),
                invoice_type="purchase_credit",
                status="issued",
                supplier=return_order.purchase_order.supplier,
                invoice_date=timezone.now().date(),
                amount_excluding_tax=-total_refund,
                tax_rate=original_invoice.tax_rate,
                tax_amount=-(total_refund * original_invoice.tax_rate / Decimal("100")),
                total_amount=-(
                    total_refund * (Decimal("100") + original_invoice.tax_rate) / Decimal("100")
                ),
                is_credit_note=True,
                original_invoice=original_invoice,
                reference_type="purchase_return",
                reference_id=str(return_order.pk),
                reference_number=return_order.return_number,
                remark=f"退货单 {return_order.return_number} 红字发票",
                created_by=request.user,
            )

            # 创建红字发票明细
            for item_data in items_with_received_return:
                item = item_data["item"]
                order_item = item_data["order_item"]
                received_return = item_data["received_return"]

                item_total = received_return * item.unit_price
                InvoiceItem.objects.create(
                    invoice=credit_note,
                    product=order_item.product,
                    description=order_item.product.name,
                    specification=order_item.product.specification or "",
                    unit=order_item.product.unit,
                    quantity=received_return,
                    unit_price=item.unit_price,
                    amount=-item_total,
                    tax_rate=original_invoice.tax_rate,
                    tax_amount=-(item_total * original_invoice.tax_rate / Decimal("100")),
                    created_by=request.user,
                )

            # 关联红字发票到退货单
            return_order.credit_note = credit_note
            return_order.save()

        # 如果有已收货退货，自动归集应付主单
        if total_refund > 0:
            from finance.models import SupplierAccount

            # 获取应付主单并自动归集
            parent_account = SupplierAccount.get_or_create_for_order(return_order.purchase_order)
            parent_account.aggregate_from_details()

        # 重新计算订单总金额
        return_order.purchase_order.calculate_totals()

        # 构建成功消息
        if total_refund > 0:
            msg_parts = [
                f"退货单 {return_order.return_number} 审核通过！",
                f"已扣减订单数量,",
                f"生成 ¥{total_refund:.2f} 的负应付明细并直接核销,",
                f"应付余额已自动减少。",
            ]
            if credit_note:
                msg_parts.append(f"已生成红字发票 {credit_note.invoice_number}。")
            else:
                msg_parts.append("已自动生成出库单。")

            messages.success(request, "".join(msg_parts))
        else:
            messages.success(request, f"退货单 {return_order.return_number} 审核通过！" "已扣减订单数量(未收货部分退货)")

        return redirect("purchase:return_detail", pk=pk)

    except Exception as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("purchase:return_detail", pk=pk)


@login_required
def return_unapprove_confirm(request, pk):
    """显示撤销退货审核确认页面"""
    return_order = get_object_or_404(PurchaseReturn, pk=pk, is_deleted=False)

    if return_order.status not in ["approved", "returned", "completed"]:
        messages.error(request, "只有已审核、已退货或已完成状态的退货单才能撤销")
        return redirect("purchase:return_detail", pk=pk)

    # 检查是否已实际退货（已发货或已完成）
    if return_order.status in ["returned", "completed"]:
        messages.error(request, "退货单已发货或已完成，无法撤销审核")
        return redirect("purchase:return_detail", pk=pk)

    context = {
        "return_order": return_order,
        "warning_message": "撤销退货后，将回滚库存变动，冲销应收账款。",
    }
    return render(request, "modules/purchase/return_confirm_unapprove.html", context)


@login_required
@transaction.atomic
def return_unapprove(request, pk):
    """撤销退货审核"""
    if request.method != "POST":
        return_order = get_object_or_404(PurchaseReturn, pk=pk, is_deleted=False)
        context = {
            "return_order": return_order,
            "warning_message": "撤销退货后，将回滚库存变动，冲销应收账款。",
        }
        return render(request, "modules/purchase/return_confirm_unapprove.html", context)

    return_order = get_object_or_404(PurchaseReturn, pk=pk, is_deleted=False)

    try:
        return_order.unapprove_return(user=request.user)
        messages.success(request, f"退货单 {return_order.return_number} 审核已撤销")
        return redirect("purchase:return_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"撤销失败：{str(e)}")
        return redirect("purchase:return_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"撤销失败：{str(e)}")
        logger.error(f"撤销退货失败: {str(e)}", exc_info=True)
        return redirect("purchase:return_detail", pk=pk)


@login_required
def return_statistics(request):
    """Purchase return statistics."""
    from decimal import Decimal

    from django.db.models import Count, Sum

    # Get date range
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    returns = PurchaseReturn.objects.filter(is_deleted=False)

    if date_from:
        returns = returns.filter(return_date__gte=date_from)
    if date_to:
        returns = returns.filter(return_date__lte=date_to)

    # Statistics by supplier
    supplier_stats = (
        returns.values("purchase_order__supplier__name")
        .annotate(total_returns=Count("id"), total_amount=Sum("refund_amount"))
        .order_by("-total_amount")
    )

    # Statistics by reason
    reason_stats = (
        returns.values("reason")
        .annotate(count=Count("id"), total_amount=Sum("refund_amount"))
        .order_by("-count")
    )

    # Statistics by status
    status_stats = returns.values("status").annotate(count=Count("id"))

    # Overall statistics
    total_returns = returns.count()
    total_amount = returns.aggregate(Sum("refund_amount"))["refund_amount__sum"] or Decimal("0")

    context = {
        "supplier_stats": supplier_stats,
        "reason_stats": reason_stats,
        "status_stats": status_stats,
        "total_returns": total_returns,
        "total_amount": total_amount,
        "date_from": date_from,
        "date_to": date_to,
    }
    return render(request, "modules/purchase/return_statistics.html", context)


# ============================================================
# Purchase Inquiry Views (采购询价)
# ============================================================


@login_required
def inquiry_list(request):
    """List all purchase inquiries with search and filter."""
    inquiries = (
        PurchaseInquiry.objects.filter(is_deleted=False)
        .select_related("buyer", "department", "warehouse", "created_by")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    # Search by inquiry number or title
    search_query = request.GET.get("search", "").strip()
    if search_query:
        inquiries = inquiries.filter(
            Q(inquiry_number__icontains=search_query) | Q(title__icontains=search_query)
        )

    # Filter by status
    status = request.GET.get("status", "").strip()
    if status:
        inquiries = inquiries.filter(status=status)

    # Filter by buyer
    buyer_id = request.GET.get("buyer", "").strip()
    if buyer_id:
        inquiries = inquiries.filter(buyer_id=buyer_id)

    # Filter by date range
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if date_from:
        inquiries = inquiries.filter(inquiry_date__gte=date_from)
    if date_to:
        inquiries = inquiries.filter(inquiry_date__lte=date_to)

    # Pagination
    paginator = Paginator(inquiries, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Context
    from django.contrib.auth import get_user_model

    User = get_user_model()
    buyers = User.objects.filter(is_active=True)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status": status,
        "buyer_id": buyer_id,
        "date_from": date_from,
        "date_to": date_to,
        "buyers": buyers,
        "inquiry_statuses": PurchaseInquiry.INQUIRY_STATUS,
    }

    return render(request, "modules/purchase/inquiry_list.html", context)


@login_required
def inquiry_detail(request, pk):
    """View details of a purchase inquiry."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    items = (
        inquiry.items.filter(is_deleted=False)
        .select_related("product", "preferred_supplier")
        .order_by("sort_order")
    )

    # Get all quotations for this inquiry
    quotations = (
        inquiry.quotations.filter(is_deleted=False)
        .select_related("supplier")
        .order_by("-quotation_date")
    )

    # Count quotations by status
    from django.db.models import Count

    quotation_counts = quotations.values("status").annotate(count=Count("id"))

    context = {
        "inquiry": inquiry,
        "items": items,
        "quotations": quotations,
        "quotation_counts": quotation_counts,
    }

    return render(request, "modules/purchase/inquiry_detail.html", context)


@login_required
@transaction.atomic
def inquiry_create(request):
    """Create a new purchase inquiry."""
    if request.method == "POST":
        import json
        from decimal import Decimal

        from common.utils import DocumentNumberGenerator

        # Generate inquiry number
        inquiry_number = DocumentNumberGenerator.generate("INQ")

        # Parse items JSON
        items_json = request.POST.get("items_json", "[]")
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, "请至少添加一个产品明细")
            return redirect("purchase:inquiry_create")

        # Create inquiry
        inquiry = PurchaseInquiry.objects.create(
            inquiry_number=inquiry_number,
            status="draft",
            inquiry_date=request.POST.get("inquiry_date"),
            deadline=request.POST.get("deadline"),
            required_date=request.POST.get("required_date") or None,
            buyer=request.user if request.POST.get("set_buyer") else None,
            department_id=request.POST.get("department") or None,
            title=request.POST.get("title"),
            description=request.POST.get("description", ""),
            delivery_address=request.POST.get("delivery_address", ""),
            warehouse_id=request.POST.get("warehouse") or None,
            payment_terms=request.POST.get("payment_terms", ""),
            notes=request.POST.get("notes", ""),
            internal_notes=request.POST.get("internal_notes", ""),
            created_by=request.user,
            updated_by=request.user,
        )

        # Create inquiry items
        for idx, item_data in enumerate(items_data):
            PurchaseInquiryItem.objects.create(
                inquiry=inquiry,
                product_id=item_data["product_id"],
                quantity=Decimal(item_data["quantity"]),
                target_price=Decimal(item_data.get("target_price", 0)),
                specifications=item_data.get("specifications", ""),
                quality_requirements=item_data.get("quality_requirements", ""),
                preferred_supplier_id=item_data.get("preferred_supplier_id") or None,
                notes=item_data.get("notes", ""),
                sort_order=idx,
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f"询价单 {inquiry_number} 创建成功！")
        return redirect("purchase:inquiry_detail", pk=inquiry.pk)

    # GET request - show form
    from departments.models import Department
    from django.core.serializers.json import DjangoJSONEncoder
    from inventory.models import Warehouse
    from products.models import Product
    from suppliers.models import Supplier

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    departments = Department.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code", "unit"
    )
    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True).values("id", "name")

    context = {
        "action": "create",
        "warehouses": warehouses,
        "departments": departments,
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
        "suppliers": json.dumps(list(suppliers), cls=DjangoJSONEncoder),
        "payment_methods": PAYMENT_METHOD_CHOICES,
    }

    return render(request, "modules/purchase/inquiry_form.html", context)


@login_required
@transaction.atomic
def inquiry_update(request, pk):
    """Update an existing purchase inquiry."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    # Only draft status can be edited
    if inquiry.status != "draft":
        messages.error(request, "只有草稿状态的询价单可以编辑")
        return redirect("purchase:inquiry_detail", pk=pk)

    if request.method == "POST":
        import json
        from decimal import Decimal

        # Parse items JSON
        items_json = request.POST.get("items_json", "[]")
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, "请至少添加一个产品明细")
            return redirect("purchase:inquiry_update", pk=pk)

        # Update inquiry
        inquiry.inquiry_date = request.POST.get("inquiry_date")
        inquiry.deadline = request.POST.get("deadline")
        inquiry.required_date = request.POST.get("required_date") or None
        inquiry.buyer = request.user if request.POST.get("set_buyer") else None
        inquiry.department_id = request.POST.get("department") or None
        inquiry.title = request.POST.get("title")
        inquiry.description = request.POST.get("description", "")
        inquiry.delivery_address = request.POST.get("delivery_address", "")
        inquiry.warehouse_id = request.POST.get("warehouse") or None
        inquiry.payment_terms = request.POST.get("payment_terms", "")
        inquiry.notes = request.POST.get("notes", "")
        inquiry.internal_notes = request.POST.get("internal_notes", "")
        inquiry.updated_by = request.user
        inquiry.save()

        # Delete existing items and create new ones
        inquiry.items.all().delete()

        for idx, item_data in enumerate(items_data):
            PurchaseInquiryItem.objects.create(
                inquiry=inquiry,
                product_id=item_data["product_id"],
                quantity=Decimal(item_data["quantity"]),
                target_price=Decimal(item_data.get("target_price", 0)),
                specifications=item_data.get("specifications", ""),
                quality_requirements=item_data.get("quality_requirements", ""),
                preferred_supplier_id=item_data.get("preferred_supplier_id") or None,
                notes=item_data.get("notes", ""),
                sort_order=idx,
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f"询价单 {inquiry.inquiry_number} 更新成功！")
        return redirect("purchase:inquiry_detail", pk=inquiry.pk)

    # GET request - show form
    import json

    from departments.models import Department
    from django.core.serializers.json import DjangoJSONEncoder
    from inventory.models import Warehouse
    from products.models import Product
    from suppliers.models import Supplier

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    departments = Department.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code", "unit"
    )
    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True).values("id", "name")

    context = {
        "action": "update",
        "inquiry": inquiry,
        "warehouses": warehouses,
        "departments": departments,
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
        "suppliers": json.dumps(list(suppliers), cls=DjangoJSONEncoder),
        "payment_methods": PAYMENT_METHOD_CHOICES,
    }

    return render(request, "modules/purchase/inquiry_form.html", context)


@login_required
@transaction.atomic
def inquiry_delete(request, pk):
    """Delete a purchase inquiry (soft delete)."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    # Only draft status can be deleted
    if inquiry.status != "draft":
        messages.error(request, "只有草稿状态的询价单可以删除")
        return redirect("purchase:inquiry_detail", pk=pk)

    if request.method == "POST":
        inquiry.is_deleted = True
        inquiry.deleted_at = timezone.now()
        inquiry.deleted_by = request.user
        inquiry.save()

        # Soft delete all items
        for item in inquiry.items.all():
            item.is_deleted = True
            item.deleted_at = timezone.now()
            item.deleted_by = request.user
            item.save()

        messages.success(request, f"询价单 {inquiry.inquiry_number} 已删除")
        return redirect("purchase:inquiry_list")

    context = {
        "inquiry": inquiry,
        "items": inquiry.items.filter(is_deleted=False).select_related("product"),
    }

    return render(request, "modules/purchase/inquiry_confirm_delete.html", context)


@login_required
def inquiry_cancel_confirm(request, pk):
    """显示取消询价单确认页面"""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    if inquiry.status == "cancelled":
        messages.error(request, "询价单已经是取消状态")
        return redirect("purchase:inquiry_detail", pk=pk)

    if inquiry.status == "sent":
        messages.error(request, "询价单已发送给供应商，无法取消")
        return redirect("purchase:inquiry_detail", pk=pk)

    if inquiry.selected_quotation:
        messages.error(request, "询价单已选定报价，无法取消")
        return redirect("purchase:inquiry_detail", pk=pk)

    if inquiry.converted_order:
        messages.error(request, "询价单已转换为采购订单，无法取消")
        return redirect("purchase:inquiry_detail", pk=pk)

    context = {
        "inquiry": inquiry,
        "warning_message": "取消后，询价单将标记为已取消状态。",
    }
    return render(request, "modules/purchase/inquiry_confirm_cancel.html", context)


@login_required
@transaction.atomic
def inquiry_cancel(request, pk):
    """取消询价单"""
    if request.method != "POST":
        inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)
        context = {
            "inquiry": inquiry,
            "warning_message": "取消后，询价单将标记为已取消状态。",
        }
        return render(request, "modules/purchase/inquiry_confirm_cancel.html", context)

    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    try:
        reason = request.POST.get("reason", "")
        inquiry.cancel_inquiry(user=request.user, reason=reason)
        messages.success(request, f"询价单 {inquiry.inquiry_number} 已取消")
        return redirect("purchase:inquiry_detail", pk=pk)
    except ValueError as e:
        messages.error(request, f"取消失败：{str(e)}")
        return redirect("purchase:inquiry_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"取消失败：{str(e)}")
        logger.error(f"取消询价单失败: {str(e)}", exc_info=True)
        return redirect("purchase:inquiry_detail", pk=pk)


@login_required
@transaction.atomic
def inquiry_send(request, pk):
    """Send inquiry to suppliers."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    # Only draft status can be sent
    if inquiry.status != "draft":
        messages.error(request, "只有草稿状态的询价单可以发送")
        return redirect("purchase:inquiry_detail", pk=pk)

    if request.method == "POST":
        # Get selected suppliers
        supplier_ids = request.POST.getlist("suppliers")
        if not supplier_ids:
            messages.error(request, "请至少选择一个供应商")
            return redirect("purchase:inquiry_send", pk=pk)

        from suppliers.models import Supplier

        suppliers = Supplier.objects.filter(id__in=supplier_ids, is_deleted=False)

        try:
            inquiry.send_inquiry(suppliers)
            messages.success(request, f"询价单已发送给 {suppliers.count()} 个供应商")
            return redirect("purchase:inquiry_detail", pk=inquiry.pk)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("purchase:inquiry_send", pk=pk)

    # GET request - show form
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)

    # Get preferred suppliers from inquiry items
    preferred_supplier_ids = inquiry.items.values_list(
        "preferred_supplier_id", flat=True
    ).distinct()
    preferred_suppliers = suppliers.filter(id__in=preferred_supplier_ids)

    context = {
        "inquiry": inquiry,
        "suppliers": suppliers,
        "preferred_suppliers": preferred_suppliers,
        "items": inquiry.items.filter(is_deleted=False).select_related("product"),
    }

    return render(request, "modules/purchase/inquiry_send.html", context)


# ============================================================
# Supplier Quotation Views (供应商报价)
# ============================================================


@login_required
def quotation_list(request):
    """List all supplier quotations with search and filter."""
    quotations = (
        SupplierQuotation.objects.filter(is_deleted=False)
        .select_related("inquiry", "supplier", "created_by")
        .order_by("-created_at")
    )

    # Search by quotation number or inquiry number
    search_query = request.GET.get("search", "").strip()
    if search_query:
        quotations = quotations.filter(
            Q(quotation_number__icontains=search_query)
            | Q(inquiry__inquiry_number__icontains=search_query)
        )

    # Filter by status
    status = request.GET.get("status", "").strip()
    if status:
        quotations = quotations.filter(status=status)

    # Filter by supplier
    supplier_id = request.GET.get("supplier", "").strip()
    if supplier_id:
        quotations = quotations.filter(supplier_id=supplier_id)

    # Filter by inquiry
    inquiry_id = request.GET.get("inquiry", "").strip()
    if inquiry_id:
        quotations = quotations.filter(inquiry_id=inquiry_id)

    # Pagination
    paginator = Paginator(quotations, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Context
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status": status,
        "supplier_id": supplier_id,
        "inquiry_id": inquiry_id,
        "suppliers": suppliers,
        "quotation_statuses": SupplierQuotation.QUOTATION_STATUS,
    }

    return render(request, "modules/purchase/quotation_list.html", context)


@login_required
def quotation_detail(request, pk):
    """View details of a supplier quotation."""
    quotation = get_object_or_404(SupplierQuotation, pk=pk, is_deleted=False)

    items = (
        quotation.items.filter(is_deleted=False)
        .select_related("product", "inquiry_item")
        .order_by("sort_order")
    )

    context = {
        "quotation": quotation,
        "items": items,
    }

    return render(request, "modules/purchase/quotation_detail.html", context)


@login_required
@transaction.atomic
def quotation_update(request, pk):
    """Update a supplier quotation (fill in prices)."""
    quotation = get_object_or_404(SupplierQuotation, pk=pk, is_deleted=False)

    # Only pending status can be edited
    if quotation.status != "pending":
        messages.error(request, "只有待报价状态的报价单可以编辑")
        return redirect("purchase:quotation_detail", pk=pk)

    if request.method == "POST":
        import json
        from decimal import Decimal

        # Parse items JSON
        items_json = request.POST.get("items_json", "[]")
        items_data = json.loads(items_json)

        # Update quotation header
        quotation.quotation_date = request.POST.get("quotation_date")
        quotation.valid_until = request.POST.get("valid_until")
        quotation.contact_person = request.POST.get("contact_person", "")
        quotation.contact_phone = request.POST.get("contact_phone", "")
        quotation.contact_email = request.POST.get("contact_email", "")
        quotation.tax_rate = Decimal(request.POST.get("tax_rate", 0))
        quotation.shipping_cost = Decimal(request.POST.get("shipping_cost", 0))
        quotation.payment_terms = request.POST.get("payment_terms", "")
        quotation.delivery_period = int(request.POST.get("delivery_period", 0))
        quotation.warranty_period = int(request.POST.get("warranty_period", 0))
        quotation.quality_certificate = request.POST.get("quality_certificate", "")
        quotation.notes = request.POST.get("notes", "")
        quotation.status = "submitted"
        quotation.updated_by = request.user
        quotation.save(skip_calculate=True)

        # Update quotation items
        for item_data in items_data:
            item_id = item_data.get("item_id")
            if item_id:
                item = quotation.items.get(id=item_id)
                item.unit_price = Decimal(item_data["unit_price"])
                item.discount_rate = Decimal(item_data.get("discount_rate", 0))
                item.brand = item_data.get("brand", "")
                item.model = item_data.get("model", "")
                item.origin = item_data.get("origin", "")
                item.delivery_period = int(item_data.get("delivery_period", 0))
                item.min_order_quantity = Decimal(item_data.get("min_order_quantity", 0))
                item.notes = item_data.get("notes", "")
                item.updated_by = request.user
                item.save()

        # Calculate totals
        quotation.calculate_totals()
        quotation.save()

        # Update inquiry status
        if quotation.inquiry.status == "sent":
            quotation.inquiry.status = "quoted"
            quotation.inquiry.save()

        messages.success(request, f"报价单 {quotation.quotation_number} 已提交")
        return redirect("purchase:quotation_detail", pk=quotation.pk)

    # GET request - show form
    items = (
        quotation.items.filter(is_deleted=False)
        .select_related("product", "inquiry_item")
        .order_by("sort_order")
    )

    context = {
        "quotation": quotation,
        "items": items,
        "payment_methods": PAYMENT_METHOD_CHOICES,
    }

    return render(request, "modules/purchase/quotation_form.html", context)


@login_required
def quotation_compare(request, inquiry_pk):
    """Compare all quotations for an inquiry."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=inquiry_pk, is_deleted=False)

    # Get all submitted quotations
    quotations = (
        inquiry.quotations.filter(is_deleted=False, status="submitted")
        .select_related("supplier")
        .prefetch_related("items__product")
    )

    if not quotations.exists():
        messages.warning(request, "暂无可对比的报价")
        return redirect("purchase:inquiry_detail", pk=inquiry_pk)

    # Organize data for comparison
    inquiry_items = (
        inquiry.items.filter(is_deleted=False).select_related("product").order_by("sort_order")
    )

    # Build comparison table
    comparison_data = []
    for inquiry_item in inquiry_items:
        item_data = {"inquiry_item": inquiry_item, "quotations": []}

        for quotation in quotations:
            quotation_item = quotation.items.filter(
                inquiry_item=inquiry_item, is_deleted=False
            ).first()

            item_data["quotations"].append(
                {
                    "quotation": quotation,
                    "item": quotation_item,
                }
            )

        comparison_data.append(item_data)

    context = {
        "inquiry": inquiry,
        "quotations": quotations,
        "comparison_data": comparison_data,
    }

    return render(request, "modules/purchase/quotation_compare.html", context)


@login_required
@transaction.atomic
def quotation_select(request, pk):
    """Select a quotation as the winner."""
    quotation = get_object_or_404(SupplierQuotation, pk=pk, is_deleted=False)

    # Only submitted quotations can be selected
    if quotation.status != "submitted":
        messages.error(request, "只有已提交的报价可以选定")
        return redirect("purchase:quotation_detail", pk=pk)

    if request.method == "POST":
        # Update quotation status
        quotation.status = "selected"
        quotation.evaluation_score = request.POST.get("evaluation_score", 0)
        quotation.evaluation_notes = request.POST.get("evaluation_notes", "")
        quotation.updated_by = request.user
        quotation.save()

        # Update inquiry
        inquiry = quotation.inquiry
        inquiry.selected_quotation = quotation
        inquiry.status = "selected"
        inquiry.save()

        # Reject other quotations
        inquiry.quotations.filter(is_deleted=False, status="submitted").exclude(pk=pk).update(
            status="rejected"
        )

        messages.success(request, f"已选定供应商 {quotation.supplier.name} 的报价")
        return redirect("purchase:inquiry_detail", pk=inquiry.pk)

    context = {
        "quotation": quotation,
        "items": quotation.items.filter(is_deleted=False).select_related("product"),
    }

    return render(request, "modules/purchase/quotation_confirm_select.html", context)


@login_required
@transaction.atomic
def inquiry_create_order(request, pk):
    """Create purchase order from inquiry."""
    inquiry = get_object_or_404(PurchaseInquiry, pk=pk, is_deleted=False)

    # Check if already created order
    if inquiry.purchase_order:
        messages.warning(request, f"已创建采购订单: {inquiry.purchase_order.order_number}")
        return redirect("purchase:order_detail", pk=inquiry.purchase_order.pk)

    if request.method == "POST":
        from common.utils import DocumentNumberGenerator

        # 获取报价信息（如果有选定的话）
        quotation = inquiry.selected_quotation

        # 根据是否有报价来决定数据来源
        if quotation:
            # 有报价：使用报价的数据
            supplier = quotation.supplier
            subtotal = quotation.subtotal
            tax_rate = quotation.tax_rate
            tax_amount = quotation.tax_amount
            shipping_cost = quotation.shipping_cost
            total_amount = quotation.total_amount
            currency = quotation.currency
            payment_terms = quotation.payment_terms
            notes = f"根据询价单 {inquiry.inquiry_number} 和报价 {quotation.quotation_number} 创建"
        else:
            # 没有报价：使用询价单的基础数据，供应商为空
            supplier = None
            subtotal = 0
            tax_rate = 0
            tax_amount = 0
            shipping_cost = 0
            total_amount = 0
            currency = "CNY"
            payment_terms = ""
            notes = f"根据询价单 {inquiry.inquiry_number} 创建（未指定供应商）"

        # Create purchase order
        order = PurchaseOrder.objects.create(
            order_number=DocumentNumberGenerator.generate(
                "purchase_order", model_class=PurchaseOrder  # 传递模型类以支持重用已删除订单编号
            ),
            supplier=supplier,
            status="draft",
            payment_status="unpaid",
            order_date=timezone.now().date(),
            required_date=inquiry.required_date,
            buyer=inquiry.buyer,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            currency=currency,
            delivery_address=inquiry.delivery_address,
            warehouse=inquiry.warehouse,
            payment_terms=payment_terms,
            notes=notes,
            created_by=request.user,
            updated_by=request.user,
        )

        # Create order items
        if quotation:
            # 有报价：从报价明细创建订单明细
            for idx, quotation_item in enumerate(quotation.items.filter(is_deleted=False)):
                PurchaseOrderItem.objects.create(
                    order=order,
                    product=quotation_item.product,
                    quantity=quotation_item.quantity,
                    unit_price=quotation_item.unit_price,
                    discount_rate=quotation_item.discount_rate,
                    discount_amount=quotation_item.discount_amount,
                    line_total=quotation_item.line_total,
                    notes=quotation_item.notes,
                    sort_order=idx,
                    created_by=request.user,
                    updated_by=request.user,
                )
        else:
            # 没有报价：从询价明细创建订单明细（价格为0）
            for idx, inquiry_item in enumerate(inquiry.items.filter(is_deleted=False)):
                PurchaseOrderItem.objects.create(
                    order=order,
                    product=inquiry_item.product,
                    quantity=inquiry_item.quantity,
                    unit_price=inquiry_item.target_price or 0,  # 使用目标价或0
                    discount_rate=0,
                    discount_amount=0,
                    line_total=0,
                    notes=inquiry_item.notes,
                    sort_order=idx,
                    created_by=request.user,
                    updated_by=request.user,
                )

        # Link order to inquiry
        inquiry.purchase_order = order
        inquiry.status = "ordered"
        inquiry.save()

        messages.success(request, f"采购订单 {order.order_number} 创建成功！")
        return redirect("purchase:order_detail", pk=order.pk)

    # GET request - show confirmation page
    quotation = inquiry.selected_quotation

    context = {
        "inquiry": inquiry,
        "quotation": quotation,
        "items": quotation.items.filter(is_deleted=False).select_related("product")
        if quotation
        else inquiry.items.filter(is_deleted=False).select_related("product"),
        "has_quotation": bool(quotation),
    }

    return render(request, "modules/purchase/inquiry_confirm_create_order.html", context)


# ============================================
# 采购报表
# ============================================


@login_required
def purchase_order_report(request):
    """
    采购订单报表 - 高级筛选和统计功能

    支持多维度筛选：
    - 单据编号、状态、日期范围
    - 供应商、采购员、产品
    - 金额范围、交货日期范围
    """
    from django.core.paginator import Paginator
    from django.db.models import Count, Q, Sum
    from products.models import Product
    from suppliers.models import Supplier
    from users.models import User

    # 基础查询集
    queryset = (
        PurchaseOrder.objects.filter(is_deleted=False)
        .select_related("supplier", "created_by")
        .prefetch_related("items__product")
    )

    # === 筛选条件 ===
    # 单据编号
    order_number = request.GET.get("order_number", "").strip()
    if order_number:
        queryset = queryset.filter(order_number__icontains=order_number)

    # 单据状态
    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    # 订单日期范围
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if date_from:
        queryset = queryset.filter(order_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(order_date__lte=date_to)

    # 供应商
    supplier_id = request.GET.get("supplier", "").strip()
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    # 采购员
    purchaser_id = request.GET.get("purchaser", "").strip()
    if purchaser_id:
        queryset = queryset.filter(created_by_id=purchaser_id)

    # 备注/说明
    notes = request.GET.get("notes", "").strip()
    if notes:
        queryset = queryset.filter(Q(notes__icontains=notes) | Q(remark__icontains=notes))

    # 金额范围
    amount_min = request.GET.get("amount_min", "").strip()
    amount_max = request.GET.get("amount_max", "").strip()
    if amount_min:
        queryset = queryset.filter(total_amount__gte=amount_min)
    if amount_max:
        queryset = queryset.filter(total_amount__lte=amount_max)

    # 预计到货日期范围
    delivery_from = request.GET.get("delivery_from", "").strip()
    delivery_to = request.GET.get("delivery_to", "").strip()
    if delivery_from:
        queryset = queryset.filter(expected_date__gte=delivery_from)
    if delivery_to:
        queryset = queryset.filter(expected_date__lte=delivery_to)

    # 产品筛选
    product_id = request.GET.get("product", "").strip()
    if product_id:
        queryset = queryset.filter(items__product_id=product_id).distinct()

    # 排序
    queryset = queryset.order_by("-order_date", "-created_at")

    # 统计信息
    stats = queryset.aggregate(
        total_count=Count("id"),
        total_amount=Sum("total_amount"),
    )

    # 计算平均值（避免除以0）
    if stats["total_count"] and stats["total_count"] > 0:
        stats["avg_amount"] = (
            stats["total_amount"] / stats["total_count"] if stats["total_amount"] else 0
        )
    else:
        stats["avg_amount"] = 0

    # 分页
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # 获取筛选选项数据
    suppliers = Supplier.objects.filter(is_deleted=False).order_by("name")
    purchasers = User.objects.filter(is_active=True).order_by("username")
    products = Product.objects.filter(is_deleted=False).order_by("name")

    context = {
        "page_obj": page_obj,
        "stats": stats,
        "status_choices": PurchaseOrder.ORDER_STATUS,
        "suppliers": suppliers,
        "purchasers": purchasers,
        "products": products,
        # 保留筛选条件（用于表单回显）
        "filter_order_number": order_number,
        "filter_status": status,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_supplier": supplier_id,
        "filter_purchaser": purchaser_id,
        "filter_notes": notes,
        "filter_amount_min": amount_min,
        "filter_amount_max": amount_max,
        "filter_delivery_from": delivery_from,
        "filter_delivery_to": delivery_to,
        "filter_product": product_id,
    }

    return render(request, "modules/purchase/order_report.html", context)


# ==================== Borrow Management Views (采购借用管理) ====================


@login_required
def borrow_list(request):
    """借用单列表"""
    from suppliers.models import Supplier

    # 基础查询
    borrows = (
        Borrow.objects.filter(is_deleted=False)
        .select_related("supplier", "buyer", "created_by", "converted_order")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    # 搜索：借用单号或供应商名称
    search_query = request.GET.get("search", "").strip()
    if search_query:
        borrows = borrows.filter(
            Q(borrow_number__icontains=search_query) | Q(supplier__name__icontains=search_query)
        )

    # 筛选：状态
    status = request.GET.get("status", "").strip()
    if status:
        borrows = borrows.filter(status=status)

    # 筛选：供应商
    supplier_id = request.GET.get("supplier", "").strip()
    if supplier_id:
        borrows = borrows.filter(supplier_id=supplier_id)

    # 筛选：日期范围
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if date_from:
        borrows = borrows.filter(borrow_date__gte=date_from)
    if date_to:
        borrows = borrows.filter(borrow_date__lte=date_to)

    # 统计卡片数据
    stats = {
        "draft_count": borrows.filter(status="draft").count(),
        "borrowed_count": borrows.filter(status="borrowed").count(),
        "completed_count": borrows.filter(status="completed").count(),
    }

    # 分页
    paginator = Paginator(borrows, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 获取筛选选项数据
    suppliers = Supplier.objects.filter(is_deleted=False).order_by("name")

    context = {
        "page_obj": page_obj,
        "stats": stats,
        "search_query": search_query,
        "status": status,
        "supplier_id": supplier_id,
        "date_from": date_from,
        "date_to": date_to,
        "suppliers": suppliers,
        "borrow_statuses": Borrow.BORROW_STATUS,
    }

    return render(request, "modules/purchase/borrow_list.html", context)


@login_required
@transaction.atomic
def borrow_create(request):
    """创建借用单"""
    if request.method == "POST":
        import json
        from decimal import Decimal

        # 解析明细数据
        items_json = request.POST.get("items_json", "[]")
        items_data = json.loads(items_json)

        # 验证错误
        errors = {}

        # 验证供应商
        supplier_id = request.POST.get("supplier")
        if not supplier_id or supplier_id == "":
            errors["supplier"] = "请选择供应商"

        # 验证日期 - 归还日期不能小于借用日期
        borrow_date = request.POST.get("borrow_date")
        expected_return_date = request.POST.get("expected_return_date")

        if borrow_date and expected_return_date:
            from datetime import datetime

            try:
                borrow_date_obj = datetime.strptime(borrow_date, "%Y-%m-%d").date()
                return_date_obj = datetime.strptime(expected_return_date, "%Y-%m-%d").date()

                if return_date_obj < borrow_date_obj:
                    errors["expected_return_date"] = "归还日期不能小于借用日期"
            except ValueError:
                errors["date_format"] = "日期格式不正确"

        # 验证明细
        if not items_data:
            errors["items"] = "请至少添加一个产品明细"

        # 如果有错误，返回表单页面并显示错误
        if errors:
            from django.core.serializers.json import DjangoJSONEncoder
            from products.models import Product
            from suppliers.models import Supplier

            suppliers = Supplier.objects.filter(is_deleted=False, is_active=True).values(
                "id", "name", "code"
            )
            products = Product.objects.filter(is_deleted=False, status="active").values(
                "id", "name", "code", "unit"
            )

            # 处理明细数据，返回给模板以保留用户输入
            existing_items_for_template = []
            if items_data:
                for item in items_data:
                    product = Product.objects.filter(id=item.get("product_id")).first()
                    if product:
                        existing_items_for_template.append(
                            {
                                "product_id": item.get("product_id"),
                                "product_name": product.name,
                                "quantity": str(item.get("quantity", 0)),
                                "notes": item.get("notes", ""),
                            }
                        )

            context = {
                "action": "create",
                "suppliers": json.dumps(list(suppliers), cls=DjangoJSONEncoder),
                "products": json.dumps(list(products), cls=DjangoJSONEncoder),
                "existing_items": json.dumps(existing_items_for_template, cls=DjangoJSONEncoder),
                "errors": errors,
                "form_data": request.POST,
            }
            return render(request, "modules/purchase/borrow_form.html", context)

        # 生成借用单号
        borrow_number = DocumentNumberGenerator.generate(
            "borrow", model_class=Borrow  # 传递模型类以支持重用已删除单据编号
        )

        # 创建借用单
        borrow = Borrow.objects.create(
            borrow_number=borrow_number,
            supplier_id=request.POST.get("supplier"),
            buyer=request.user,
            status="borrowed",  # 直接进入借用中状态（无需审核）
            borrow_date=request.POST.get("borrow_date"),
            expected_return_date=request.POST.get("expected_return_date") or None,
            purpose=request.POST.get("purpose", ""),
            notes=request.POST.get("notes", ""),
            created_by=request.user,
            updated_by=request.user,
        )

        # 创建明细
        for item_data in items_data:
            BorrowItem.objects.create(
                borrow=borrow,
                product_id=item_data["product_id"],
                quantity=Decimal(item_data["quantity"]),
                notes=item_data.get("notes", ""),
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f"借用单 {borrow_number} 创建成功！")
        return redirect("purchase:borrow_detail", pk=borrow.pk)

    # GET request - 显示表单
    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from products.models import Product
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "code"
    )
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code", "unit"
    )

    context = {
        "action": "create",
        "suppliers": json.dumps(list(suppliers), cls=DjangoJSONEncoder),
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
    }

    return render(request, "modules/purchase/borrow_form.html", context)


@login_required
def borrow_detail(request, pk):
    """借用单详情"""
    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 获取明细列表
    items = borrow.items.filter(is_deleted=False).select_related("product").order_by("id")

    # 操作权限判断
    can_edit = borrow.status == "draft"

    # 计算总的可借用数量
    total_borrowable = sum(item.borrowable_quantity for item in items)
    can_confirm_receipt = (
        borrow.status == "borrowed" and total_borrowable > 0  # 只有还有剩余可借用数量时才显示入库按钮
    )

    can_return = borrow.status == "borrowed" and borrow.total_remaining_quantity > 0
    can_request_conversion = borrow.status == "borrowed" and borrow.total_remaining_quantity > 0
    can_approve_conversion = False  # 已删除转换中状态

    context = {
        "borrow": borrow,
        "items": items,
        "can_edit": can_edit,
        "can_confirm_receipt": can_confirm_receipt,
        "can_return": can_return,
        "can_request_conversion": can_request_conversion,
        "can_approve_conversion": can_approve_conversion,
    }

    return render(request, "modules/purchase/borrow_detail.html", context)


@login_required
@transaction.atomic
def borrow_update(request, pk):
    """编辑借用单"""
    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 只有草稿状态可以编辑
    if borrow.status != "draft":
        messages.error(request, "只有草稿状态的借用单可以编辑")
        return redirect("purchase:borrow_detail", pk=pk)

    if request.method == "POST":
        import json
        from decimal import Decimal

        # 解析明细数据
        items_json = request.POST.get("items_json", "[]")
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, "请至少添加一个产品明细")
            return redirect("purchase:borrow_update", pk=pk)

        # 验证日期 - 归还日期不能小于借用日期
        borrow_date = request.POST.get("borrow_date")
        expected_return_date = request.POST.get("expected_return_date")

        if borrow_date and expected_return_date:
            from datetime import datetime

            try:
                borrow_date_obj = datetime.strptime(borrow_date, "%Y-%m-%d").date()
                return_date_obj = datetime.strptime(expected_return_date, "%Y-%m-%d").date()

                if return_date_obj < borrow_date_obj:
                    messages.error(request, "归还日期不能小于借用日期")
                    return redirect("purchase:borrow_update", pk=pk)
            except ValueError:
                messages.error(request, "日期格式不正确")
                return redirect("purchase:borrow_update", pk=pk)

        # 更新借用单
        borrow.supplier_id = request.POST.get("supplier")
        borrow.borrow_date = request.POST.get("borrow_date")
        borrow.expected_return_date = request.POST.get("expected_return_date") or None
        borrow.purpose = request.POST.get("purpose", "")
        borrow.notes = request.POST.get("notes", "")
        borrow.updated_by = request.user
        borrow.save()

        # 删除旧明细并创建新明细
        borrow.items.all().delete()

        for item_data in items_data:
            BorrowItem.objects.create(
                borrow=borrow,
                product_id=item_data["product_id"],
                quantity=Decimal(item_data["quantity"]),
                batch_number=item_data.get("batch_number", ""),
                serial_numbers=item_data.get("serial_numbers", ""),
                specifications=item_data.get("specifications", ""),
                notes=item_data.get("notes", ""),
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f"借用单 {borrow.borrow_number} 更新成功！")
        return redirect("purchase:borrow_detail", pk=borrow.pk)

    # GET request - 显示表单
    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from products.models import Product
    from suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "code"
    )
    products = Product.objects.filter(is_deleted=False, status="active").values(
        "id", "name", "code", "unit"
    )

    # 序列化现有明细数据
    existing_items = []
    for item in borrow.items.filter(is_deleted=False).select_related("product"):
        existing_items.append(
            {
                "product_id": item.product.id,
                "product_name": item.product.name,
                "quantity": str(item.quantity),
                "batch_number": item.batch_number,
                "serial_numbers": item.serial_numbers,
                "specifications": item.specifications,
                "notes": item.notes,
            }
        )

    context = {
        "action": "update",
        "borrow": borrow,
        "suppliers": json.dumps(list(suppliers), cls=DjangoJSONEncoder),
        "products": json.dumps(list(products), cls=DjangoJSONEncoder),
        "existing_items": json.dumps(existing_items, cls=DjangoJSONEncoder),
    }

    return render(request, "modules/purchase/borrow_form.html", context)


@login_required
@transaction.atomic
def borrow_confirm_receipt(request, pk):
    """借用入库确认"""
    from decimal import Decimal

    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 检查状态
    if borrow.status != "borrowed":
        messages.error(request, "只有借用中状态的借用单才能确认入库")
        return redirect("purchase:borrow_detail", pk=pk)

    if request.method == "POST":
        try:
            # 收集本次入库的明细数据
            items_to_receive = []
            for item in borrow.items.filter(is_deleted=False):
                receive_qty_str = request.POST.get(f"receive_qty_{item.pk}", "0").strip()
                receive_qty = Decimal(receive_qty_str) if receive_qty_str else Decimal("0")

                if receive_qty > 0:
                    items_to_receive.append({"item_id": item.pk, "quantity": receive_qty})

            if not items_to_receive:
                messages.warning(request, "请至少选择一个产品进行入库")
                return redirect("purchase:borrow_confirm_receipt", pk=pk)

            # 调用模型的入库确认方法
            borrow.confirm_borrow_receipt(request.user, items_to_receive)
            messages.success(request, f"借用单 {borrow.borrow_number} 入库确认成功！")
            return redirect("purchase:borrow_detail", pk=pk)

        except ValueError as e:
            messages.error(request, f"入库确认失败: {str(e)}")
            return redirect("purchase:borrow_confirm_receipt", pk=pk)

    # GET request - 显示入库确认表单
    items = borrow.items.filter(is_deleted=False).select_related("product").order_by("id")

    # 计算每个明细的剩余可借用数量
    for item in items:
        item.borrowable_qty = item.borrowable_quantity  # 剩余可借用
        item.borrowed_qty = item.borrowed_quantity  # 已借用

    context = {
        "borrow": borrow,
        "items": items,
    }

    return render(request, "modules/purchase/borrow_confirm_receipt.html", context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def borrow_confirm_all_receipt(request, pk):
    """一键全部入库确认（默认将所有剩余可借用数量全部入库）"""
    print(f"\n[DEBUG] borrow_confirm_all_receipt 被调用: pk={pk}, user={request.user}")
    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)
    print(f"[DEBUG] 借用单: {borrow.borrow_number}, 状态: {borrow.status}")

    # 检查状态
    if borrow.status != "borrowed":
        print(f"[DEBUG] 状态检查失败: {borrow.status} != borrowed")
        messages.error(request, "只有借用中状态的借用单才能确认入库")
        logger.warning(f"借用单 {borrow.borrow_number} 状态不是borrowed，当前状态: {borrow.status}")
        return redirect("purchase:borrow_detail", pk=pk)

    # 检查是否还有剩余可借用数量
    total_borrowable = sum(
        item.borrowable_quantity for item in borrow.items.filter(is_deleted=False)
    )
    print(f"[DEBUG] 可借用数量: {total_borrowable}")

    if total_borrowable == 0:
        print("[DEBUG] 没有可入库数量")
        messages.warning(request, "该借用单的所有产品已全部入库，无需再次入库")
        logger.info(f"借用单 {borrow.borrow_number} 没有可入库数量")
        return redirect("purchase:borrow_detail", pk=pk)

    try:
        print("[DEBUG] 开始执行入库操作...")
        # 调用模型的入库确认方法（传入None表示全部入库，模型会自动处理）
        borrow.confirm_borrow_receipt(request.user, None)
        print("[DEBUG] 入库操作完成")
        messages.success(request, f"借用单 {borrow.borrow_number} 已全部入库成功！共入库 {total_borrowable} 件产品")
        logger.info(f"借用单 {borrow.borrow_number} 全部入库成功，入库数量: {total_borrowable}，将重定向到借用单详情页")
        print(f"[DEBUG] 准备重定向到: purchase:borrow_detail, pk={pk}")
        return redirect("purchase:borrow_detail", pk=pk)
    except ValueError as e:
        print(f"[DEBUG] 入库失败: {e}")
        messages.error(request, f"入库确认失败: {str(e)}")
        logger.error(f"借用单 {borrow.borrow_number} 入库失败: {str(e)}")
        return redirect("purchase:borrow_detail", pk=pk)
    except Exception as e:
        print(f"[DEBUG] 未预期的错误: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        messages.error(request, f"系统错误: {str(e)}")
        logger.error(f"借用单 {borrow.borrow_number} 系统错误: {str(e)}")
        return redirect("purchase:borrow_detail", pk=pk)


@login_required
@transaction.atomic
def borrow_return(request, pk):
    """归还处理（支持部分归还）"""
    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 检查状态
    if borrow.status != "borrowed":
        messages.error(request, "当前状态不允许归还操作")
        return redirect("purchase:borrow_detail", pk=pk)

    if request.method == "POST":
        from decimal import Decimal

        # 处理归还明细
        has_return = False
        for item in borrow.items.filter(is_deleted=False):
            return_qty_str = request.POST.get(f"return_qty_{item.pk}", "").strip()
            if not return_qty_str:
                continue

            return_qty = Decimal(return_qty_str)
            if return_qty <= 0:
                continue

            # 验证归还数量
            if return_qty > item.remaining_quantity:
                messages.error(
                    request, f"产品 {item.product.name} 的归还数量不能超过剩余数量 {item.remaining_quantity}"
                )
                return redirect("purchase:borrow_return", pk=pk)

            # 更新已归还数量
            item.returned_quantity += return_qty
            item.save()
            has_return = True

        if not has_return:
            messages.warning(request, "请至少归还一个产品")
            return redirect("purchase:borrow_return", pk=pk)

        # 归还后检查剩余数量，如果为0则状态改为已完成
        if borrow.total_remaining_quantity == 0:
            borrow.status = "completed"

        borrow.updated_by = request.user
        borrow.save()

        messages.success(request, "归还处理成功！")
        return redirect("purchase:borrow_detail", pk=pk)

    # GET request - 显示归还表单
    items = borrow.items.filter(is_deleted=False).select_related("product").order_by("id")

    context = {
        "borrow": borrow,
        "items": items,
    }

    return render(request, "modules/purchase/borrow_return.html", context)


@login_required
@transaction.atomic
def borrow_request_conversion(request, pk):
    """直接转采购（无需审核）"""
    from decimal import Decimal

    from core.utils.document_number import DocumentNumberGenerator

    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 检查状态
    if borrow.status != "borrowed":
        messages.error(request, "当前状态不允许转采购操作")
        return redirect("purchase:borrow_detail", pk=pk)

    # 检查是否有剩余数量
    if borrow.total_remaining_quantity <= 0:
        messages.error(request, "没有可转采购的数量")
        return redirect("purchase:borrow_detail", pk=pk)

    if request.method == "POST":
        # 收集转换数据
        items_with_price = []
        for item in borrow.items.filter(is_deleted=False):
            convert_qty_str = request.POST.get(f"convert_qty_{item.pk}", "").strip()
            unit_price_str = request.POST.get(f"unit_price_{item.pk}", "").strip()

            if not convert_qty_str or not unit_price_str:
                continue

            convert_qty = Decimal(convert_qty_str)
            unit_price = Decimal(unit_price_str)

            if convert_qty <= 0:
                continue

            # 验证转换数量
            if convert_qty > item.remaining_quantity:
                messages.error(
                    request, f"产品 {item.product.name} 的转采购数量不能超过剩余数量 {item.remaining_quantity}"
                )
                return redirect("purchase:borrow_request_conversion", pk=pk)

            # 验证单价
            if unit_price <= 0:
                messages.error(request, f"产品 {item.product.name} 的单价必须大于0")
                return redirect("purchase:borrow_request_conversion", pk=pk)

            items_with_price.append(
                {
                    "item": item,
                    "convert_qty": convert_qty,
                    "unit_price": unit_price,
                }
            )

        if not items_with_price:
            messages.warning(request, "请至少选择一个产品转采购，并输入数量和单价")
            return redirect("purchase:borrow_request_conversion", pk=pk)

        try:
            # 直接创建采购订单
            order = PurchaseOrder.objects.create(
                order_number=DocumentNumberGenerator.generate(
                    "purchase_order", model_class=PurchaseOrder  # 传递模型类以支持重用已删除订单编号
                ),
                supplier=borrow.supplier,
                buyer=borrow.buyer,
                order_date=timezone.now().date(),
                status="draft",
                notes=f"由借用单 {borrow.borrow_number} 转换而来\n借用目的：{borrow.purpose}",
                internal_notes=request.POST.get("conversion_notes", ""),
                created_by=request.user,
            )

            # 创建订单明细
            total = 0
            for data in items_with_price:
                item = data["item"]
                notes_text = f"从借用单 {borrow.borrow_number} 转换"
                if item.specifications:
                    notes_text = f"{notes_text}\n规格要求: {item.specifications}"

                order_item = PurchaseOrderItem.objects.create(
                    purchase_order=order,
                    product=item.product,
                    quantity=data["convert_qty"],
                    unit_price=data["unit_price"],
                    notes=notes_text,
                    created_by=request.user,
                )
                total += order_item.line_total

                # 更新借用单明细的转换信息（累加转采购数量）
                from decimal import Decimal

                item.conversion_quantity = (item.conversion_quantity or Decimal("0")) + data[
                    "convert_qty"
                ]
                item.conversion_unit_price = data["unit_price"]
                item.save()

            # 更新订单总金额
            order.total_amount = total
            order.subtotal = total
            order.save()

            # 更新借用单状态
            # 只有当转采购后剩余数量为0时，状态才改为已完成
            # 否则保持借用中状态
            if borrow.total_remaining_quantity == 0:
                borrow.status = "completed"

            # 注意：不再设置 converted_order 字段，因为一个借用单可能转多个采购订单
            # 使用 converted_orders 属性来获取所有关联的采购订单
            borrow.conversion_approved_by = request.user
            borrow.conversion_approved_at = timezone.now()
            borrow.conversion_notes = request.POST.get("conversion_notes", "")
            borrow.updated_by = request.user
            borrow.save()

            messages.success(request, f"转采购成功！已生成采购订单：{order.order_number}")
            return redirect("purchase:order_detail", pk=order.pk)

        except Exception as e:
            messages.error(request, f"转采购失败：{str(e)}")
            return redirect("purchase:borrow_detail", pk=pk)

    # GET request - 显示转换表单
    items = borrow.items.filter(is_deleted=False).select_related("product").order_by("id")
    # 过滤掉没有剩余数量的明细
    items_with_remaining = [item for item in items if item.remaining_quantity > 0]

    if not items_with_remaining:
        messages.error(request, "没有可转采购的产品明细")
        return redirect("purchase:borrow_detail", pk=pk)

    context = {
        "borrow": borrow,
        "items": items_with_remaining,
    }

    return render(request, "modules/purchase/borrow_request_conversion.html", context)


@login_required
def borrow_cancel_conversion_confirm(request, pk):
    """显示取消借用转采购确认页面"""
    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    # 检查是否已转采购
    if not borrow.converted_order:
        messages.error(request, "借用单未转换为采购订单，无法取消")
        return redirect("purchase:borrow_detail", pk=pk)

    # 检查关联的采购订单状态
    order = borrow.converted_order
    if order.status not in ["draft", "pending"]:
        messages.error(request, f"关联的采购订单状态为{order.get_status_display()}，无法取消转采购")
        return redirect("purchase:borrow_detail", pk=pk)

    context = {
        "borrow": borrow,
        "order": order,
        "warning_message": f"取消转采购后，将删除关联的采购订单 {order.order_number}。",
    }
    return render(request, "modules/purchase/borrow_confirm_cancel.html", context)


@login_required
@transaction.atomic
def borrow_cancel_conversion(request, pk):
    """取消借用转采购"""
    if request.method != "POST":
        borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)
        order = borrow.converted_order
        context = {
            "borrow": borrow,
            "order": order,
            "warning_message": f"取消转采购后，将删除关联的采购订单 {order.order_number}。",
        }
        return render(request, "modules/purchase/borrow_confirm_cancel.html", context)

    borrow = get_object_or_404(Borrow, pk=pk, is_deleted=False)

    if not borrow.converted_order:
        messages.error(request, "借用单未转换为采购订单，无法取消")
        return redirect("purchase:borrow_detail", pk=pk)

    try:
        order = borrow.converted_order

        # 检查订单状态
        if order.status not in ["draft", "pending"]:
            raise ValueError(f"关联的采购订单状态为{order.get_status_display()}，无法取消转采购")

        # 删除关联的采购订单（软删除）
        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.deleted_by = request.user
        order.save()

        # 软删除订单明细
        for item in order.items.all():
            item.is_deleted = True
            item.deleted_at = timezone.now()
            item.deleted_by = request.user
            item.save()

        # 更新借用单状态
        borrow.converted_order = None
        borrow.conversion_approved_by = None
        borrow.conversion_approved_at = None
        borrow.conversion_notes = ""
        # 恢复借用单状态为借用中
        if borrow.status == "completed":
            borrow.status = "borrowed"
        borrow.updated_by = request.user
        borrow.save()

        messages.success(request, f"已取消转采购，采购订单 {order.order_number} 已删除")
        return redirect("purchase:borrow_detail", pk=pk)

    except ValueError as e:
        messages.error(request, f"取消失败：{str(e)}")
        return redirect("purchase:borrow_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"取消失败：{str(e)}")
        logger.error(f"取消借用转采购失败: {str(e)}", exc_info=True)
        return redirect("purchase:borrow_detail", pk=pk)


# borrow_approve_conversion 视图已删除 - 转采购无需审核，直接生成订单


@login_required
def supplier_contacts_api(request, supplier_id):
    """
    API: 获取供应商的联系人列表
    用于采购订单表单的联系人下拉选择
    """
    from django.http import JsonResponse
    from suppliers.models import Supplier, SupplierContact

    try:
        supplier = get_object_or_404(Supplier, pk=supplier_id, is_deleted=False)

        # 获取所有启用的联系人，按主联系人排序
        contacts = supplier.contacts.filter(is_deleted=False, is_active=True).order_by(
            "-is_primary", "id"
        )

        contacts_data = []
        for contact in contacts:
            contacts_data.append(
                {
                    "id": contact.id,
                    "name": contact.name,
                    "position": contact.position or "",
                    "phone": contact.phone or "",
                    "email": contact.email or "",
                    "is_primary": contact.is_primary,
                }
            )

        return JsonResponse({"success": True, "contacts": contacts_data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
