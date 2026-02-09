"""
Sales views for the ERP system.
"""
import json

from core.models import Notification
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from common.utils import DocumentNumberGenerator

from .forms import ConvertToOrderForm, QuoteForm, QuoteItemFormSet, QuoteSearchForm
from .models import (
    Delivery,
    DeliveryItem,
    Quote,
    QuoteItem,
    SalesLoan,
    SalesLoanItem,
    SalesOrder,
    SalesOrderItem,
    SalesReturn,
    SalesReturnItem,
)


def _create_return_notification(sales_return, action, recipient, extra_message=""):
    """
    Helper function to create notifications for sales return operations.

    Args:
        sales_return: SalesReturn instance
        action: Action performed (created, approved, received, processed, rejected)
        recipient: User to receive the notification
        extra_message: Additional message to append
    """
    action_messages = {
        "created": f"新退货单 {sales_return.return_number} 已创建",
        "approved": f"退货单 {sales_return.return_number} 已审核通过",
        "received": f"退货单 {sales_return.return_number} 已确认收货",
        "processed": f"退货单 {sales_return.return_number} 已处理完成",
        "rejected": f"退货单 {sales_return.return_number} 已被拒绝",
    }

    title = action_messages.get(action, f"退货单 {sales_return.return_number} 状态更新")
    message = f"客户：{sales_return.sales_order.customer.name}\n"
    message += f"订单号：{sales_return.sales_order.order_number}\n"
    message += f"退款金额：¥{sales_return.refund_amount}\n"
    if extra_message:
        message += f"\n{extra_message}"

    notification_type = "success" if action in ["approved", "processed"] else "info"
    if action == "rejected":
        notification_type = "warning"

    Notification.create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        category="sales_return",
        reference_type="sales_return",
        reference_id=str(sales_return.id),
        reference_url=reverse("sales:return_detail", args=[sales_return.pk]),
    )


@login_required
def quote_list(request):
    """
    List all quotes with search and filter capabilities.
    """
    quotes = (
        Quote.objects.filter(is_deleted=False)
        .select_related("customer", "sales_rep")
        .order_by("-quote_date", "-created_at")
    )

    # Apply search and filters
    search_form = QuoteSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        if search:
            quotes = quotes.filter(
                Q(quote_number__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(reference_number__icontains=search)
            )

        quote_type = search_form.cleaned_data.get("quote_type")
        if quote_type:
            quotes = quotes.filter(quote_type=quote_type)

        status = search_form.cleaned_data.get("status")
        if status:
            quotes = quotes.filter(status=status)

        customer = search_form.cleaned_data.get("customer")
        if customer:
            quotes = quotes.filter(customer__name__icontains=customer)

        date_from = search_form.cleaned_data.get("date_from")
        if date_from:
            quotes = quotes.filter(quote_date__gte=date_from)

        date_to = search_form.cleaned_data.get("date_to")
        if date_to:
            quotes = quotes.filter(quote_date__lte=date_to)

    # Pagination
    paginator = Paginator(quotes, 20)  # 20 quotes per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_count": quotes.count(),
    }
    return render(request, "modules/sales/quote_list.html", context)


@login_required
def quote_detail(request, pk):
    """
    Display quote details.
    """
    quote = get_object_or_404(
        Quote.objects.filter(is_deleted=False)
        .select_related("customer", "contact_person", "sales_rep", "converted_order")
        .prefetch_related("items__product"),
        pk=pk,
    )

    # 使用新的模板选择服务
    from core.services.template_selector import TemplateSelector

    # 确定完整的单据类型（用于获取默认模板）
    document_type_full = (
        "quote_domestic" if quote.quote_type.upper() == "DOMESTIC" else "quote_overseas"
    )

    # 获取可用模板（整个销售类）
    print_templates = TemplateSelector.get_available_templates(
        document_type="quote", category="sales"
    )

    # 获取默认模板（根据国内/海外区分）
    default_template = TemplateSelector.get_default_template(document_type_full)

    context = {
        "quote": quote,
        "items": quote.items.all(),
        "can_edit": quote.status == "draft",
        "can_convert": quote.status in ["draft", "sent"] and not quote.is_expired,
        "print_templates": print_templates,
        "default_template": default_template,
    }
    return render(request, "modules/sales/quote_detail.html", context)


@login_required
@transaction.atomic
def quote_create(request):
    """
    Create a new quote.
    """
    if request.method == "POST":
        form = QuoteForm(request.POST, request=request)
        # For create, don't pass instance to formset during initialization
        # Django will try to access the relationship which requires a pk
        formset = QuoteItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Save quote first to get primary key
            quote = form.save(commit=False)
            quote.quote_number = DocumentNumberGenerator.generate("quotation")
            quote.created_by = request.user
            quote.save()

            # Now set the instance for formset and save items
            formset.instance = quote
            items = formset.save(commit=False)
            for item in items:
                item.created_by = request.user
                item.save()

            # Delete removed items (should be none for create)
            for item in formset.deleted_objects:
                item.delete()

            # Recalculate totals
            quote.calculate_totals()
            quote.save()

            messages.success(request, f"报价单 {quote.quote_number} 创建成功！")
            return redirect("sales:quote_detail", pk=quote.pk)
        else:
            messages.error(request, "请检查表单数据")
    else:
        form = QuoteForm(request=request)
        formset = QuoteItemFormSet()

    # Get products for the template
    from products.models import Product

    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    context = {
        "form": form,
        "formset": formset,
        "action": "create",
        "products": products,
    }
    return render(request, "modules/sales/quote_form.html", context)


@login_required
@transaction.atomic
def quote_update(request, pk):
    """
    Update an existing quote.
    """
    quote = get_object_or_404(Quote, pk=pk, is_deleted=False)

    # Only draft quotes can be edited
    if quote.status != "draft":
        messages.error(request, "只有草稿状态的报价单可以编辑")
        return redirect("sales:quote_detail", pk=pk)

    if request.method == "POST":
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteItemFormSet(request.POST, instance=quote)

        if form.is_valid() and formset.is_valid():
            # Update quote
            quote = form.save(commit=False)
            quote.updated_by = request.user
            quote.save()

            # Update quote items
            items = formset.save(commit=False)
            for item in items:
                if not item.pk:
                    item.created_by = request.user
                item.updated_by = request.user
                item.save()

            # Delete removed items
            for item in formset.deleted_objects:
                item.delete()

            # Recalculate totals
            quote.calculate_totals()
            quote.save()

            messages.success(request, f"报价单 {quote.quote_number} 更新成功！")
            return redirect("sales:quote_detail", pk=quote.pk)
        else:
            messages.error(request, "请检查表单数据")
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteItemFormSet(instance=quote)

    # Get products for the template
    from products.models import Product

    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    context = {
        "form": form,
        "formset": formset,
        "quote": quote,
        "action": "update",
        "products": products,
    }
    return render(request, "modules/sales/quote_form.html", context)


@login_required
def quote_delete(request, pk):
    """
    Delete (soft delete) a quote.
    """
    quote = get_object_or_404(Quote, pk=pk, is_deleted=False)

    # Only draft quotes can be deleted
    if quote.status != "draft":
        messages.error(request, "只有草稿状态的报价单可以删除")
        return redirect("sales:quote_detail", pk=pk)

    if request.method == "POST":
        quote.is_deleted = True
        quote.deleted_at = timezone.now()
        quote.deleted_by = request.user
        quote.save()

        messages.success(request, f"报价单 {quote.quote_number} 已删除")
        return redirect("sales:quote_list")

    context = {
        "quote": quote,
    }
    return render(request, "modules/sales/quote_confirm_delete.html", context)


@login_required
@transaction.atomic
def quote_convert_to_order(request, pk):
    """
    Convert a quote to a sales order.
    """
    quote = get_object_or_404(Quote, pk=pk, is_deleted=False)

    # Check if already converted
    if quote.status == "converted":
        messages.info(request, "此报价单已经转换为订单")
        return redirect("sales:order_detail", pk=quote.converted_order.pk)

    # Check if quote is valid
    if quote.is_expired:
        messages.error(request, "报价单已过期，无法转换为订单")
        return redirect("sales:quote_detail", pk=pk)

    if quote.status not in ["draft", "sent", "accepted"]:
        messages.error(request, "只有草稿、已发送或已接受状态的报价单可以转换为订单")
        return redirect("sales:quote_detail", pk=pk)

    if request.method == "POST":
        form = ConvertToOrderForm(request.POST)
        if form.is_valid():
            try:
                from .services import OrderService

                # Prepare extra data
                extra_data = {}
                if form.cleaned_data.get("order_date"):
                    extra_data["order_date"] = form.cleaned_data["order_date"]
                if form.cleaned_data.get("required_date"):
                    extra_data["required_date"] = form.cleaned_data["required_date"]
                if form.cleaned_data.get("notes"):
                    extra_data["notes"] = form.cleaned_data["notes"]

                # Convert quote to order using service
                order = OrderService.convert_quote_to_order(quote, request.user, extra_data)

                messages.success(request, f"报价单 {quote.quote_number} 已成功转换为订单 {order.order_number}")
                return redirect("sales:order_detail", pk=order.pk)
            except Exception as e:
                messages.error(request, f"转换失败: {str(e)}")
                return redirect("sales:quote_detail", pk=pk)
        else:
            messages.error(request, "请检查表单数据")
    else:
        from datetime import timedelta

        from django.utils import timezone

        form = ConvertToOrderForm(
            initial={
                "order_date": timezone.now().date(),
                "required_date": timezone.now().date() + timedelta(days=15),
            }
        )

    context = {
        "quote": quote,
        "form": form,
    }
    return render(request, "modules/sales/quote_convert.html", context)


@login_required
def quote_change_status(request, pk):
    """
    Change quote status.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    quote = get_object_or_404(Quote, pk=pk, is_deleted=False)
    new_status = request.POST.get("status")

    if new_status not in dict(Quote.QUOTE_STATUS):
        return JsonResponse({"error": "无效的状态"}, status=400)

    # Validate status transitions
    allowed_transitions = {
        "draft": ["sent"],
        "sent": ["accepted", "rejected", "expired"],
        "accepted": ["converted"],
        "rejected": [],
        "expired": [],
        "converted": [],
    }

    if new_status not in allowed_transitions.get(quote.status, []):
        return JsonResponse({"error": "不允许的状态转换"}, status=400)

    quote.status = new_status
    quote.updated_by = request.user
    quote.save()

    messages.success(request, f"报价单状态已更新为：{quote.get_status_display()}")
    return JsonResponse({"success": True, "status": new_status})


@login_required
def quote_print(request, pk):
    """
    Print quote as PDF using custom print template.
    """
    quote = get_object_or_404(
        Quote.objects.select_related("customer", "contact_person", "sales_rep").prefetch_related(
            "items__product"
        ),
        pk=pk,
        is_deleted=False,
    )

    # 使用新的模板选择服务
    from core.models import PrintTemplate
    from core.services.template_selector import TemplateSelector

    # 确定完整的单据类型
    document_type_full = (
        "quote_domestic" if quote.quote_type.upper() == "DOMESTIC" else "quote_overseas"
    )

    # 获取打印模板（优先使用用户指定的，否则使用默认）
    print_template = None
    template_id = request.GET.get("template_id")

    if template_id:
        # 使用用户指定的模板
        print_template = PrintTemplate.objects.filter(
            pk=template_id, is_deleted=False, is_active=True
        ).first()
    else:
        # 使用默认模板
        print_template = TemplateSelector.get_default_template(document_type_full)

    # Fallback to basic print if no template configured
    if not print_template:
        context = {
            "quote": quote,
            "items": quote.items.all(),
            "print_date": timezone.now(),
        }
        return render(request, "modules/sales/quote_print.html", context)

    # Use custom template with HiPrint
    context = {
        "quote": quote,
        "items": quote.items.all(),
        "print_date": timezone.now(),
        "template": print_template,
        "layout_config": print_template.layout_config,
        "layout_config_json": json.dumps(print_template.layout_config, ensure_ascii=False),
    }
    return render(request, "modules/sales/quote_print_hiprint.html", context)


@login_required
def quote_duplicate(request, pk):
    """
    Duplicate an existing quote.
    """
    original_quote = get_object_or_404(Quote, pk=pk, is_deleted=False)

    if request.method == "POST":
        with transaction.atomic():
            # Create new quote
            new_quote = Quote.objects.create(
                quote_number=DocumentNumberGenerator.generate("quotation"),
                quote_type=original_quote.quote_type,
                customer=original_quote.customer,
                contact_person=original_quote.contact_person,
                quote_date=timezone.now().date(),
                valid_until=timezone.now().date() + timezone.timedelta(days=30),
                sales_rep=original_quote.sales_rep,
                currency=original_quote.currency,
                exchange_rate=original_quote.exchange_rate,
                tax_rate=original_quote.tax_rate,
                discount_rate=original_quote.discount_rate,
                payment_terms=original_quote.payment_terms,
                delivery_terms=original_quote.delivery_terms,
                warranty_terms=original_quote.warranty_terms,
                notes=f"复制自: {original_quote.quote_number}",
                created_by=request.user,
                status="draft",
            )

            # Copy items
            for item in original_quote.items.all():
                QuoteItem.objects.create(
                    quote=new_quote,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_rate=item.discount_rate,
                    lead_time=item.lead_time,
                    notes=item.notes,
                    sort_order=item.sort_order,
                    created_by=request.user,
                )

            # Calculate totals
            new_quote.calculate_totals()
            new_quote.save()

            messages.success(request, f"已复制报价单，新报价单号：{new_quote.quote_number}")
            return redirect("sales:quote_detail", pk=new_quote.pk)

    messages.error(request, "无效的请求")
    return redirect("sales:quote_detail", pk=pk)


# ==================== Sales Order Views ====================


@login_required
def order_list(request):
    """List all sales orders with search and filter."""
    from sales.models import SalesOrderItem, SalesReturnItem

    orders = SalesOrder.objects.filter(is_deleted=False).select_related("customer", "sales_rep")

    # Search
    search = request.GET.get("search", "")
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(customer__name__icontains=search)
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

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        orders = orders.filter(order_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    orders = orders.order_by("-created_at")

    # 为每个订单计算已退货数量
    for order in orders:
        # 计算该订单的总退货数量
        total_returned = (
            SalesReturnItem.objects.filter(
                return_order__sales_order=order, return_order__is_deleted=False
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        order.total_returned_quantity = total_returned

    # Pagination
    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "payment_status": payment_status,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
    }
    return render(request, "modules/sales/order_list.html", context)


@login_required
def order_detail(request, pk):
    """Display sales order details."""
    order = get_object_or_404(
        SalesOrder.objects.filter(is_deleted=False)
        .select_related("customer", "sales_rep", "approved_by")
        .prefetch_related("items__product"),
        pk=pk,
    )

    # Check if can create delivery
    can_create_delivery = False
    if order.approved_by:
        # Check if any items have remaining quantity
        can_create_delivery = any(item.remaining_quantity > 0 for item in order.items.all())

    context = {
        "order": order,
        "items": order.items.all(),
        "can_edit": order.status == "draft",
        "can_approve": order.status in ["draft", "pending"],
        "can_create_delivery": can_create_delivery,
    }
    return render(request, "modules/sales/order_detail.html", context)


@login_required
@transaction.atomic
@login_required
@transaction.atomic
def order_create(request):
    """Create a new sales order."""
    if request.method == "POST":
        import json
        from decimal import Decimal

        from .services import OrderService

        # Extract form data
        order_data = {
            "customer_id": request.POST.get("customer"),
            "order_date": request.POST.get("order_date"),
            "required_date": request.POST.get("required_date") or None,
            "promised_date": request.POST.get("promised_date") or None,
            "sales_rep_id": request.POST.get("sales_rep") or None,
            "tax_rate": request.POST.get("tax_rate", 0),
            "discount_rate": request.POST.get("discount_rate", 0),
            "shipping_cost": request.POST.get("shipping_cost", 0),
            "currency": request.POST.get("currency", "CNY"),
            "shipping_address": request.POST.get("shipping_address", ""),
            "shipping_contact": request.POST.get("shipping_contact", ""),
            "shipping_phone": request.POST.get("shipping_phone", ""),
            "payment_terms": request.POST.get("payment_terms", ""),
            "reference_number": request.POST.get("reference_number", ""),
            "notes": request.POST.get("notes", ""),
            "status": "draft",
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
                            "required_date": item.get("required_date") or None,
                            "notes": item.get("notes", ""),
                        }
                    )

            order = OrderService.create_order(request.user, order_data, items_data)

            messages.success(request, f"销售订单 {order.order_number} 创建成功！")
            return redirect("sales:order_detail", pk=order.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    from customers.models import Customer
    from django.contrib.auth import get_user_model
    from products.models import Product

    User = get_user_model()

    customers = Customer.objects.filter(is_deleted=False, status="active")
    sales_reps = User.objects.filter(is_active=True)
    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    context = {
        "customers": customers,
        "sales_reps": sales_reps,
        "products": products,
        "action": "create",
    }
    return render(request, "modules/sales/order_form.html", context)


@login_required
@transaction.atomic
def order_update(request, pk):
    """Update an existing sales order."""
    import json
    from decimal import Decimal

    from .services import OrderService

    order = get_object_or_404(SalesOrder, pk=pk, is_deleted=False)

    if order.status not in ["draft", "pending"]:
        messages.error(request, "只有草稿或待审核状态的订单可以编辑")
        return redirect("sales:order_detail", pk=pk)

    if request.method == "POST":
        order_data = {
            "customer_id": request.POST.get("customer"),
            "order_date": request.POST.get("order_date"),
            "required_date": request.POST.get("required_date") or None,
            "promised_date": request.POST.get("promised_date") or None,
            "sales_rep_id": request.POST.get("sales_rep") or None,
            "tax_rate": request.POST.get("tax_rate", 0),
            "discount_rate": request.POST.get("discount_rate", 0),
            "shipping_cost": request.POST.get("shipping_cost", 0),
            "currency": request.POST.get("currency", "CNY"),
            "shipping_address": request.POST.get("shipping_address", ""),
            "shipping_contact": request.POST.get("shipping_contact", ""),
            "shipping_phone": request.POST.get("shipping_phone", ""),
            "payment_terms": request.POST.get("payment_terms", ""),
            "reference_number": request.POST.get("reference_number", ""),
            "notes": request.POST.get("notes", ""),
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
                            "required_date": item.get("required_date") or None,
                            "notes": item.get("notes", ""),
                        }
                    )

            OrderService.update_order(order, request.user, order_data, items_data)

            messages.success(request, f"销售订单 {order.order_number} 更新成功！")
            return redirect("sales:order_detail", pk=order.pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET request
    from customers.models import Customer
    from django.contrib.auth import get_user_model
    from products.models import Product

    User = get_user_model()

    customers = Customer.objects.filter(is_deleted=False, status="active")
    sales_reps = User.objects.filter(is_active=True)
    products = Product.objects.filter(is_deleted=False, status="active").select_related("unit")

    context = {
        "order": order,
        "customers": customers,
        "sales_reps": sales_reps,
        "products": products,
        "action": "update",
    }
    return render(request, "modules/sales/order_form.html", context)


@login_required
def order_delete(request, pk):
    """Delete (soft delete) a sales order."""
    order = get_object_or_404(SalesOrder, pk=pk, is_deleted=False)

    if order.status not in ["draft", "cancelled"]:
        messages.error(request, "只有草稿或已取消状态的订单可以删除")
        return redirect("sales:order_detail", pk=pk)

    if request.method == "POST":
        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.deleted_by = request.user
        order.save()

        messages.success(request, f"销售订单 {order.order_number} 已删除")
        return redirect("sales:order_list")

    context = {
        "order": order,
    }
    return render(request, "modules/sales/order_confirm_delete.html", context)


@login_required
def get_customer_info(request, customer_id):
    """
    AJAX API to get customer contact information.
    """
    from customers.models import Customer, CustomerContact
    from django.http import JsonResponse

    try:
        customer = Customer.objects.get(pk=customer_id, is_deleted=False)
        contacts = CustomerContact.objects.filter(customer=customer, is_deleted=False)

        contacts_data = []
        primary_contact = None

        for contact in contacts:
            contact_dict = {
                "id": contact.id,
                "name": contact.name,
                "phone": contact.phone or "",
                "mobile": contact.mobile or "",
                "email": contact.email or "",
                "is_primary": contact.is_primary,
            }
            contacts_data.append(contact_dict)

            if contact.is_primary:
                primary_contact = contact_dict

        # 从主联系人获取联系信息（如果有的话）
        contact_person_name = primary_contact["name"] if primary_contact else ""
        contact_phone = primary_contact["phone"] if primary_contact else ""
        contact_mobile = primary_contact["mobile"] if primary_contact else ""

        return JsonResponse(
            {
                "success": True,
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "contact_person": contact_person_name,
                    "phone": contact_phone,
                    "mobile": contact_mobile,
                    "payment_terms": customer.get_payment_terms_display()
                    if customer.payment_terms
                    else "",
                },
                "contacts": contacts_data,
                "primary_contact": primary_contact,
            }
        )
    except Customer.DoesNotExist:
        return JsonResponse({"success": False, "error": "客户不存在"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def get_product_info(request, product_id):
    """
    AJAX API to get product information including price.
    """
    from django.http import JsonResponse
    from products.models import Product

    try:
        product = Product.objects.get(pk=product_id, is_deleted=False)

        return JsonResponse(
            {
                "success": True,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "code": product.code,
                    "unit_price": float(product.selling_price),
                    "unit": product.unit.symbol if product.unit else "",
                    "specifications": product.specifications or "",
                },
            }
        )
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "error": "产品不存在"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@transaction.atomic
def order_approve(request, pk):
    """
    Approve sales order and generate delivery.
    """
    order = get_object_or_404(SalesOrder.objects.filter(is_deleted=False), pk=pk)

    # Check if user has permission to approve
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限审核订单")
        return redirect("sales:order_detail", pk=pk)

    # Check if order can be approved
    if order.approved_by:
        messages.warning(request, "订单已经审核过了")
        return redirect("sales:order_detail", pk=pk)

    if order.status not in ["draft", "pending"]:
        messages.warning(request, f"订单状态为 {order.get_status_display()}，无法审核")
        return redirect("sales:order_detail", pk=pk)

    try:
        # Approve order and generate delivery
        delivery, _ = order.approve_order(
            approved_by_user=request.user, warehouse=None  # Will use default warehouse
        )

        # Check if delivery was created (depends on system configuration)
        if delivery:
            messages.success(request, f"订单审核成功!已生成发货单 {delivery.delivery_number}")
        else:
            messages.success(request, "订单审核成功!")
        return redirect("sales:order_detail", pk=pk)

    except ValueError as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("sales:order_detail", pk=pk)
    except Exception as e:
        messages.error(request, f"审核时发生错误：{str(e)}")
        return redirect("sales:order_detail", pk=pk)


@login_required
@transaction.atomic
def order_unapprove(request, pk):
    """
    Unapprove (cancel approval) sales order.
    This will delete related deliveries and customer accounts.
    """
    order = get_object_or_404(SalesOrder.objects.filter(is_deleted=False), pk=pk)

    # Check if user has permission to unapprove
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限撤销审核")
        return redirect("sales:order_detail", pk=pk)

    # Check if order is approved
    if not order.approved_by:
        messages.warning(request, "订单未审核，无需撤销")
        return redirect("sales:order_detail", pk=pk)

    if request.method == "POST":
        try:
            # Unapprove order
            order.unapprove_order()

            messages.success(request, f"订单 {order.order_number} 审核已撤销，相关发货单和应收账款已删除")
            return redirect("sales:order_detail", pk=pk)

        except ValueError as e:
            messages.error(request, f"撤销失败：{str(e)}")
            return redirect("sales:order_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"撤销时发生错误：{str(e)}")
            return redirect("sales:order_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "order": order,
        "deliveries": order.deliveries.all(),
    }
    return render(request, "modules/sales/order_confirm_unapprove.html", context)


# ==================== Delivery Views ====================


@login_required
def delivery_list(request):
    """List all deliveries with search and filter."""
    deliveries = Delivery.objects.filter(is_deleted=False).select_related(
        "sales_order", "sales_order__customer", "warehouse", "prepared_by", "shipped_by"
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        deliveries = deliveries.filter(
            Q(delivery_number__icontains=search)
            | Q(sales_order__order_number__icontains=search)
            | Q(sales_order__customer__name__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        deliveries = deliveries.filter(status=status)

    # Filter by date range
    date_from = request.GET.get("date_from", "")
    if date_from:
        deliveries = deliveries.filter(planned_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        deliveries = deliveries.filter(planned_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    deliveries = deliveries.order_by("-created_at")

    # Pagination
    paginator = Paginator(deliveries, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
    }
    return render(request, "modules/sales/delivery_list.html", context)


@login_required
def delivery_detail(request, pk):
    """Display delivery details."""
    delivery = get_object_or_404(
        Delivery.objects.filter(is_deleted=False)
        .select_related(
            "sales_order", "sales_order__customer", "warehouse", "prepared_by", "shipped_by"
        )
        .prefetch_related("items__order_item__product"),
        pk=pk,
    )

    context = {
        "delivery": delivery,
        "items": delivery.items.all(),
        "can_ship": delivery.status in ["preparing", "ready"],
    }
    return render(request, "modules/sales/delivery_detail.html", context)


@login_required
@transaction.atomic
def delivery_create(request, order_pk):
    """Create a new delivery from an order (supports partial delivery)."""
    order = get_object_or_404(
        SalesOrder.objects.filter(is_deleted=False).prefetch_related("items__product"), pk=order_pk
    )

    # Check if order is approved
    if not order.approved_by:
        messages.error(request, "订单未审核，无法创建发货单")
        return redirect("sales:order_detail", pk=order_pk)

    # Check if order has items with remaining quantity
    items_with_remaining = [item for item in order.items.all() if item.remaining_quantity > 0]
    if not items_with_remaining:
        messages.error(request, "订单所有产品已全部发货")
        return redirect("sales:order_detail", pk=order_pk)

    if request.method == "POST":
        try:
            # Get warehouse
            warehouse_id = request.POST.get("warehouse")
            if not warehouse_id:
                messages.error(request, "请选择仓库")
                return redirect("sales:delivery_create", order_pk=order_pk)

            from inventory.models import Warehouse

            warehouse = Warehouse.objects.get(pk=warehouse_id, is_deleted=False, is_active=True)

            # Create delivery
            delivery = Delivery.objects.create(
                delivery_number=DocumentNumberGenerator.generate("delivery"),
                sales_order=order,
                status="preparing",
                planned_date=request.POST.get("planned_date") or timezone.now().date(),
                shipping_address=request.POST.get("shipping_address") or order.shipping_address,
                shipping_contact=request.POST.get("shipping_contact") or order.shipping_contact,
                shipping_phone=request.POST.get("shipping_phone") or order.shipping_phone,
                shipping_method=request.POST.get("shipping_method") or order.shipping_method,
                warehouse=warehouse,
                notes=request.POST.get("notes", ""),
                created_by=request.user,
            )

            # Process delivery items from JSON
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            for item_data in items_data:
                if item_data.get("order_item_id") and float(item_data.get("quantity", 0)) > 0:
                    order_item = SalesOrderItem.objects.get(pk=item_data["order_item_id"])

                    # Validate quantity
                    quantity = Decimal(str(item_data["quantity"]))
                    if quantity > order_item.remaining_quantity:
                        raise ValueError(f"产品 {order_item.product.name} 发货数量超过剩余数量")

                    DeliveryItem.objects.create(
                        delivery=delivery,
                        order_item=order_item,
                        quantity=quantity,
                        created_by=request.user,
                    )

            if not delivery.items.exists():
                delivery.delete()
                messages.error(request, "请至少选择一项产品发货")
                return redirect("sales:delivery_create", order_pk=order_pk)

            messages.success(request, f"发货单 {delivery.delivery_number} 创建成功！")
            return redirect("sales:delivery_detail", pk=delivery.pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    from inventory.models import Warehouse

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        "order": order,
        "items": items_with_remaining,
        "warehouses": warehouses,
        "action": "create",
    }
    return render(request, "modules/sales/delivery_form.html", context)


@login_required
@transaction.atomic
def delivery_update(request, pk):
    """Update an existing delivery (pre-ship only)."""
    delivery = get_object_or_404(Delivery, pk=pk, is_deleted=False)
    if delivery.status not in ["preparing", "ready"]:
        messages.error(request, "只有准备中或待发货的发货单可以编辑")
        return redirect("sales:delivery_detail", pk=pk)

    if request.method == "POST":
        try:
            delivery.planned_date = request.POST.get("planned_date") or delivery.planned_date
            delivery.shipping_address = request.POST.get(
                "shipping_address", delivery.shipping_address
            )
            delivery.shipping_contact = request.POST.get(
                "shipping_contact", delivery.shipping_contact
            )
            delivery.shipping_phone = request.POST.get("shipping_phone", delivery.shipping_phone)
            delivery.shipping_method = request.POST.get("shipping_method", delivery.shipping_method)
            delivery.carrier = request.POST.get("carrier", delivery.carrier)
            delivery.tracking_number = request.POST.get("tracking_number", delivery.tracking_number)
            delivery.warehouse_id = request.POST.get("warehouse") or delivery.warehouse_id
            delivery.updated_by = request.user
            delivery.save()

            messages.success(request, f"发货单 {delivery.delivery_number} 更新成功！")
            return redirect("sales:delivery_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    context = {
        "delivery": delivery,
        "action": "update",
    }
    return render(request, "modules/sales/delivery_form.html", context)


@login_required
def delivery_delete(request, pk):
    """Delete (soft delete) a delivery."""
    delivery = get_object_or_404(Delivery, pk=pk, is_deleted=False)
    if delivery.status in ["shipped", "in_transit", "delivered"]:
        messages.error(request, "已发货/在途/已送达的发货单不可删除")
        return redirect("sales:delivery_detail", pk=pk)

    if request.method == "POST":
        delivery.is_deleted = True
        delivery.deleted_at = timezone.now()
        delivery.deleted_by = request.user
        delivery.save()
        messages.success(request, f"发货单 {delivery.delivery_number} 已删除")
        return redirect("sales:delivery_list")

    messages.info(request, "请在发货单详情页使用删除按钮提交确认")
    return redirect("sales:delivery_detail", pk=pk)


@login_required
@transaction.atomic
def delivery_ship(request, pk):
    """Mark delivery as shipped and update delivered quantities."""
    delivery = get_object_or_404(Delivery, pk=pk, is_deleted=False)

    # Check permission
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限执行此操作")
        return redirect("sales:delivery_detail", pk=pk)

    # Check status - 允许部分发货状态的发货单继续发货
    if delivery.status not in ["preparing", "ready", "partially_shipped"]:
        messages.error(request, f"发货单状态为 {delivery.get_status_display()}，无法发货")
        return redirect("sales:delivery_detail", pk=pk)

    if request.method == "POST":
        try:
            # 从POST数据中获取实际发货数量
            # 格式: shipped_quantity_[item_id] = actual_quantity
            import json
            from decimal import Decimal

            # 处理JSON格式的发货数量数据
            items_data_json = request.POST.get("items_data", "[]")
            items_data = json.loads(items_data_json)

            # 将数据转换为字典，方便查找
            shipped_quantities = {}
            for item_data in items_data:
                item_id = item_data.get("item_id")
                shipped_qty = Decimal(str(item_data.get("shipped_quantity", 0)))
                if item_id:
                    shipped_quantities[int(item_id)] = shipped_qty

            # 验证发货数量
            for delivery_item in delivery.items.all():
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))

                # 验证不能超过未发货数量
                if shipped_qty > delivery_item.unshipped_quantity:
                    raise ValueError(
                        f"产品 {delivery_item.order_item.product.name} 的发货数量 ({shipped_qty}) "
                        f"不能超过未发货数量 ({delivery_item.unshipped_quantity})"
                    )

                # 验证发货数量必须大于0
                if shipped_qty <= 0:
                    raise ValueError(f"产品 {delivery_item.order_item.product.name} 的发货数量必须大于0")

            # Check inventory availability before shipment (库存检查)
            # 只对需要库存管理的产品进行检查
            from inventory.models import InventoryStock

            insufficient_stock_items = []
            for delivery_item in delivery.items.all():
                product = delivery_item.order_item.product
                warehouse = delivery.warehouse
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))

                # Skip inventory check if product doesn't track inventory
                # 跳过不需要库存管理的产品（如服务类产品）
                if not product.track_inventory:
                    continue

                # Get current stock
                try:
                    stock = InventoryStock.objects.get(
                        product=product, warehouse=warehouse, is_deleted=False
                    )
                    available_quantity = stock.available_quantity
                except InventoryStock.DoesNotExist:
                    available_quantity = 0

                # Check if stock is sufficient for this shipment
                if available_quantity < shipped_qty:
                    insufficient_stock_items.append(
                        {
                            "product": product.name,
                            "code": product.code,
                            "required": shipped_qty,
                            "available": available_quantity,
                            "shortage": shipped_qty - available_quantity,
                        }
                    )

            # If any item has insufficient stock, raise error
            if insufficient_stock_items:
                error_message = "库存不足，无法发货：\n"
                for item in insufficient_stock_items:
                    error_message += f'\n• {item["product"]} ({item["code"]}): '
                    error_message += f'需要 {item["required"]}，可用 {item["available"]}，'
                    error_message += f'缺少 {item["shortage"]}'
                raise ValueError(error_message)

            # 更新发货明细的实际发货数量
            for delivery_item in delivery.items.all():
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))
                delivery_item.actual_shipped_quantity += shipped_qty
                delivery_item.save()

            # 判断是全部发货还是部分发货
            if delivery.is_fully_shipped:
                delivery.status = "shipped"
            else:
                delivery.status = "partially_shipped"

            delivery.actual_date = timezone.now().date()
            delivery.shipped_by = request.user
            delivery.tracking_number = request.POST.get("tracking_number", "")
            delivery.carrier = request.POST.get("carrier", "")
            delivery.save()

            # Update delivered_quantity for each order item (使用实际发货数量)
            for delivery_item in delivery.items.all():
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))
                order_item = delivery_item.order_item
                order_item.delivered_quantity += shipped_qty
                order_item.save()

            # Create inventory transactions for stock deduction (库存出库)
            # 只对需要库存管理的产品创建库存交易
            from inventory.models import InventoryTransaction

            for delivery_item in delivery.items.all():
                product = delivery_item.order_item.product
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))

                # Skip inventory transaction if product doesn't track inventory
                # 跳过不需要库存管理的产品（如服务类产品）
                if not product.track_inventory:
                    continue

                # 只有实际发货数量大于0时才创建库存交易
                if shipped_qty <= 0:
                    continue

                InventoryTransaction.objects.create(
                    transaction_type="out",
                    product=product,
                    warehouse=delivery.warehouse,
                    location=None,  # Can be set if location tracking is needed
                    quantity=shipped_qty,  # 使用实际发货数量
                    unit_cost=product.cost_price,
                    reference_type="sales_order",
                    reference_id=str(order.id),
                    reference_number=delivery.delivery_number,
                    batch_number=delivery_item.batch_number,
                    operator=request.user,
                    notes=f"销售出库 - 订单 {order.order_number}",
                    created_by=request.user,
                )

            # Update sales order status based on delivery progress
            order = delivery.sales_order

            # Check if all items are fully delivered
            all_items_delivered = all(
                item.delivered_quantity >= item.quantity for item in order.items.all()
            )

            # Check if any items are partially delivered
            any_items_delivered = any(item.delivered_quantity > 0 for item in order.items.all())

            if all_items_delivered:
                # All items fully delivered
                order.status = "shipped"
                order.shipped_date = delivery.actual_date
                order.tracking_number = delivery.tracking_number
            elif any_items_delivered and order.status == "confirmed":
                # Partial delivery - update to ready_to_ship if not already
                order.status = "ready_to_ship"

            order.save()

            # 生成发票和应收账款（仅针对本次实际发货的数量）
            from decimal import Decimal

            from core.utils.document_number import DocumentNumberGenerator
            from finance.models import CustomerAccount, Invoice, InvoiceItem

            invoice_number = DocumentNumberGenerator.generate("invoice")
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                invoice_type="sales",
                customer=order.customer,
                invoice_date=timezone.now().date(),
                tax_rate=order.tax_rate,
                reference_type="sales_order",
                reference_id=str(order.id),
                reference_number=order.order_number,
                created_by=request.user,
            )

            # 为每个发货明细创建发票明细（使用本次实际发货数量）
            for delivery_item in delivery.items.all():
                shipped_qty = shipped_quantities.get(delivery_item.id, Decimal("0"))

                # 跳过未发货的明细
                if shipped_qty <= 0:
                    continue

                oi = delivery_item.order_item
                discount_factor = (Decimal("100") - (oi.discount_rate or Decimal("0"))) / Decimal(
                    "100"
                )
                # Calculate tax-exclusive unit price
                # SalesOrder uses tax-inclusive pricing, but Invoice uses tax-exclusive pricing + tax
                unit_price_after_discount = oi.unit_price * discount_factor
                tax_rate_decimal = order.tax_rate / Decimal("100")
                unit_price_exclusive = unit_price_after_discount / (Decimal("1") + tax_rate_decimal)

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=oi.product,
                    description=oi.product.name,
                    specification=getattr(oi.product, "specification", ""),
                    unit=getattr(oi.product.unit, "symbol", ""),
                    quantity=shipped_qty,  # 使用实际发货数量
                    unit_price=unit_price_exclusive,
                    tax_rate=order.tax_rate,
                    created_by=request.user,
                )

            invoice.calculate_totals()
            invoice.save()

            due_date = timezone.now().date()
            if order.payment_terms:
                terms = order.payment_terms.lower()
                from datetime import timedelta

                if "net_30" in terms:
                    due_date = due_date + timedelta(days=30)
                elif "net_60" in terms:
                    due_date = due_date + timedelta(days=60)

            CustomerAccount.objects.create(
                customer=order.customer,
                sales_order=order,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                due_date=due_date,
                invoice_amount=invoice.total_amount,
                paid_amount=Decimal("0"),
                balance=invoice.total_amount,
                currency=order.currency,
                notes=f'发货单 {delivery.delivery_number} 对应应收账款（{"全部发货" if delivery.is_fully_shipped else "部分发货"}）',
                created_by=request.user,
            )

            # 根据发货状态显示不同的消息
            if delivery.is_fully_shipped:
                messages.success(request, f"发货单 {delivery.delivery_number} 已全部发货完成，并生成销售发票与应收账款")
            else:
                messages.success(
                    request,
                    f"发货单 {delivery.delivery_number} 部分发货成功，并生成销售发票与应收账款。剩余未发货数量: {delivery.total_unshipped_quantity}",
                )
            return redirect("sales:delivery_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"发货失败：{str(e)}")
            import traceback

            traceback.print_exc()
            return redirect("sales:delivery_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "delivery": delivery,
    }
    return render(request, "modules/sales/delivery_confirm_ship.html", context)


# ==================== Sales Return Views ====================


@login_required
def return_list(request):
    """List all sales returns with search and filter."""
    from finance.models import Payment

    returns = SalesReturn.objects.filter(is_deleted=False).select_related(
        "sales_order", "sales_order__customer", "delivery", "approved_by"
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        returns = returns.filter(
            Q(return_number__icontains=search)
            | Q(sales_order__order_number__icontains=search)
            | Q(sales_order__customer__name__icontains=search)
        )

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        returns = returns.filter(status=status)

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

    # 为每个退货单添加退款支付信息
    for return_item in page_obj:
        refund_payment = Payment.objects.filter(
            is_deleted=False,
            payment_type="payment",
            customer=return_item.sales_order.customer,
            reference_type="sales_return",
            reference_id=str(return_item.id),
        ).first()
        return_item.refund_payment = refund_payment

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
    }
    return render(request, "modules/sales/return_list.html", context)


@login_required
def return_detail(request, pk):
    """Display sales return details."""
    sales_return = get_object_or_404(
        SalesReturn.objects.filter(is_deleted=False)
        .select_related("sales_order", "sales_order__customer", "delivery", "approved_by")
        .prefetch_related("items__order_item__product"),
        pk=pk,
    )

    from finance.models import Payment

    refund_payment = Payment.objects.filter(
        is_deleted=False,
        payment_type="payment",
        customer=sales_return.sales_order.customer,
        reference_type="sales_return",
        reference_id=str(sales_return.id),
    ).first()

    context = {
        "return": sales_return,
        "items": sales_return.items.all(),
        "can_approve": sales_return.status == "pending",
        "can_receive": sales_return.status == "approved",
        "can_process": sales_return.status == "received",  # 在已收货状态时显示处理按钮，但通常不会出现，因为确认收货后直接跳到已处理
        "refund_payment": refund_payment,
    }
    return render(request, "modules/sales/return_detail.html", context)


@login_required
@transaction.atomic
def return_create(request, order_pk):
    """Create a new sales return from an order."""
    order = get_object_or_404(
        SalesOrder.objects.filter(is_deleted=False).prefetch_related("items__product"), pk=order_pk
    )

    # Check if order can be returned
    if order.status not in ["shipped", "delivered", "completed"]:
        messages.error(request, "只有已发货、已送达或已完成的订单可以退货")
        return redirect("sales:order_detail", pk=order_pk)

    if request.method == "POST":
        sales_return = None  # Initialize sales_return to None
        try:
            # Extract form data
            return_data = {
                "return_number": DocumentNumberGenerator.generate("sales_return"),
                "sales_order": order,
                "delivery_id": request.POST.get("delivery") or None,
                "status": "pending",
                "reason": request.POST.get("reason"),
                "return_date": request.POST.get("return_date"),
                "notes": request.POST.get("notes", ""),
            }

            sales_return = SalesReturn(**return_data)
            sales_return.created_by = request.user
            sales_return.save()

            # Process return items from JSON
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            from decimal import ROUND_HALF_UP, Decimal

            from django.db.models import Sum

            total_refund = Decimal("0.00")
            for idx, item_data in enumerate(items_data):
                order_item_id = item_data.get("order_item_id")
                quantity_raw = item_data.get("quantity", 0)
                # Normalize to Decimal and validate
                try:
                    quantity = Decimal(str(quantity_raw))
                except Exception:
                    quantity = Decimal("0")

                if order_item_id and quantity > 0:
                    order_item = SalesOrderItem.objects.get(pk=order_item_id)

                    # 计算该订单项的总退货数量（退货单还未保存,所以只考虑其他退货单的退货数量）
                    existing_return_quantity = SalesReturnItem.objects.filter(
                        order_item=order_item, return_order__sales_order=order_item.order
                    ).aggregate(total=Sum("quantity"))["total"] or Decimal("0")

                    # 验证退货数量不能大于(已交付数量 - 已退货数量)
                    available_return_quantity = (
                        order_item.delivered_quantity - existing_return_quantity
                    )
                    if quantity > available_return_quantity:
                        raise ValueError(
                            f"产品 {order_item.product.name} 的退货数量 ({quantity}) 不能大于可退数量 ({available_return_quantity})"
                        )

                    unit_price_raw = item_data.get("unit_price", None)
                    if unit_price_raw is None or unit_price_raw == "":
                        unit_price = order_item.unit_price
                    else:
                        unit_price = Decimal(str(unit_price_raw))

                    # Quantize to match model precision
                    quantity = quantity.quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
                    unit_price = unit_price.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

                    return_item = SalesReturnItem.objects.create(
                        return_order=sales_return,
                        order_item=order_item,
                        quantity=quantity,
                        unit_price=unit_price,
                        condition=item_data.get("condition", ""),
                        notes=item_data.get("notes", ""),
                        created_by=request.user,
                    )
                    total_refund += return_item.line_total

            # Update refund amount
            sales_return.refund_amount = total_refund.quantize(
                Decimal("0.00"), rounding=ROUND_HALF_UP
            )
            sales_return.save()

            # Create notifications
            # Notify sales rep if exists
            if order.sales_rep:
                _create_return_notification(
                    sales_return,
                    "created",
                    order.sales_rep,
                    f"退货原因：{sales_return.get_reason_display()}",
                )

            # Notify all staff users (managers)
            from django.contrib.auth import get_user_model

            User = get_user_model()
            managers = User.objects.filter(is_staff=True, is_active=True).exclude(
                id=request.user.id
            )
            if order.sales_rep:
                managers = managers.exclude(id=order.sales_rep.id)

            for manager in managers[:5]:  # Notify up to 5 managers
                _create_return_notification(
                    sales_return,
                    "created",
                    manager,
                    f"创建人：{request.user.username}\n退货原因：{sales_return.get_reason_display()}",
                )

            messages.success(request, f"退货单 {sales_return.return_number} 创建成功！")
            return redirect("sales:return_detail", pk=sales_return.pk)
        except Exception as e:
            # 如果退货单已经被创建，删除它以避免留下空的退货单
            if sales_return:
                try:
                    sales_return.delete()
                except:
                    pass  # 如果删除失败，忽略错误
            messages.error(request, f"创建失败：{str(e)}")
            return redirect("sales:order_detail", pk=order_pk)

    # GET request
    deliveries = order.deliveries.filter(is_deleted=False, status__in=["shipped", "delivered"])

    # 为每个订单项计算已退货数量和剩余可退数量
    order_items_with_return_info = []
    for item in order.items.all():
        # 计算该订单项的已退货数量
        returned_quantity = (
            SalesReturnItem.objects.filter(
                order_item=item, return_order__sales_order=order
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        # 计算剩余可退数量
        available_return_quantity = item.delivered_quantity - returned_quantity

        # 添加到列表中
        item.returned_quantity = returned_quantity
        item.available_return_quantity = available_return_quantity
        order_items_with_return_info.append(item)

    context = {
        "order": order,
        "items": order_items_with_return_info,
        "deliveries": deliveries,
        "action": "create",
    }
    return render(request, "modules/sales/return_form.html", context)


@login_required
@transaction.atomic
def return_update(request, pk):
    """Update a sales return (pending only)."""
    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)
    if sales_return.status != "pending":
        messages.error(request, "只有待审核的退货单可以编辑")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        try:
            sales_return.reason = request.POST.get("reason", sales_return.reason)
            sales_return.return_date = request.POST.get("return_date") or sales_return.return_date
            sales_return.notes = request.POST.get("notes", sales_return.notes)
            sales_return.updated_by = request.user
            sales_return.save()

            messages.success(request, f"退货单 {sales_return.return_number} 更新成功！")
            return redirect("sales:return_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    context = {
        "return": sales_return,
        "action": "update",
    }
    return render(request, "modules/sales/return_form.html", context)


@login_required
def return_delete(request, pk):
    """Delete (soft delete) a sales return."""
    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)
    if sales_return.status not in ["pending", "rejected"]:
        messages.error(request, "只有待审核或已拒绝的退货单可以删除")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        sales_return.is_deleted = True
        sales_return.deleted_at = timezone.now()
        sales_return.deleted_by = request.user
        sales_return.save()
        messages.success(request, f"退货单 {sales_return.return_number} 已删除")
        return redirect("sales:return_list")

    messages.info(request, "请在退货单详情页使用删除按钮提交确认")
    return redirect("sales:return_detail", pk=pk)


@login_required
def return_approve(request, pk):
    """审核销售退货并自动生成退款应付"""
    from django.db import transaction

    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)

    # Check permission
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限审核退货单")
        return redirect("sales:return_detail", pk=pk)

    # Check status
    if sales_return.status != "pending":
        messages.error(request, f"退货单状态为 {sales_return.get_status_display()}，无法审核")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        # ============ 第一步：在独立事务中生成唯一的付款单号 ============
        payment_number = None

        if sales_return.refund_amount and sales_return.refund_amount > 0:
            # 检查是否已经存在关联的退款付款记录
            existing_payment = Payment.objects.filter(
                is_deleted=False,
                payment_type="payment",
                customer=sales_return.sales_order.customer,
                reference_type="sales_return",
                reference_id=str(sales_return.id),
            ).first()

            if not existing_payment:
                # 生成唯一单号（带重试机制）
                def generate_unique_payment_number():
                    from django.db import IntegrityError

                    from common.utils import DocumentNumberGenerator

                    max_retries = 5
                    for attempt in range(max_retries):
                        try:
                            with transaction.atomic(savepoint=False):
                                pn = DocumentNumberGenerator.generate("RF")
                                # 创建占位记录来验证单号唯一性
                                placeholder = Payment.objects.create(
                                    payment_number=pn,
                                    payment_type="payment",
                                    payment_method="bank_transfer",
                                    status="pending",
                                    amount=Decimal("0"),
                                    currency="CNY",
                                    payment_date=timezone.now().date(),
                                    description="PLACEHOLDER",
                                    created_by=request.user,
                                )
                                # 立即硬删除占位记录（只用于验证单号唯一性）
                                placeholder.hard_delete()
                            return pn
                        except IntegrityError:
                            continue
                    raise Exception(f"生成付款单号失败：已尝试 {max_retries} 次")

                try:
                    payment_number = generate_unique_payment_number()
                except Exception as e:
                    messages.error(request, f"生成付款单号失败：{str(e)}")
                    return redirect("sales:return_detail", pk=pk)

        # ============ 第二步：在主事务中执行所有操作 ============
        try:
            with transaction.atomic():
                # Update return
                sales_return.status = "approved"
                sales_return.approved_by = request.user
                sales_return.approved_at = timezone.now()
                sales_return.save()

                # 自动创建退款应付
                from decimal import Decimal

                from finance.models import Payment, SupplierAccount

                from common.utils import DocumentNumberGenerator

                # 检查是否已经存在关联的应付账款记录
                existing_supplier_account = SupplierAccount.objects.filter(
                    is_deleted=False,
                    customer=sales_return.sales_order.customer,
                    sales_return=sales_return,
                ).first()

                if payment_number:
                    # 创建付款记录
                    Payment.objects.create(
                        payment_number=payment_number,
                        payment_type="payment",
                        payment_method="bank_transfer",
                        status="pending",  # 设置为待付款状态
                        payment_date=timezone.now().date(),
                        amount=sales_return.refund_amount,
                        currency=sales_return.sales_order.currency,
                        customer=sales_return.sales_order.customer,
                        reference_type="sales_return",
                        reference_id=str(sales_return.id),
                        reference_number=sales_return.return_number,
                        description=f"销售退货退款（待付款） - {sales_return.return_number}",
                        created_by=request.user,
                    )

                if (
                    not existing_supplier_account
                    and sales_return.refund_amount
                    and sales_return.refund_amount > 0
                ):
                    # 创建应付账款记录（用于退款给客户）
                    due_date = timezone.now().date() + timezone.timedelta(days=7)  # 默认7天内退款
                    SupplierAccount.objects.create(
                        customer=sales_return.sales_order.customer,
                        sales_return=sales_return,
                        invoice_number=sales_return.return_number,
                        invoice_date=timezone.now().date(),
                        due_date=due_date,
                        status="pending",
                        invoice_amount=sales_return.refund_amount,
                        paid_amount=Decimal("0"),
                        balance=sales_return.refund_amount,
                        currency=sales_return.sales_order.currency,
                        notes=f"销售退货退款 - 订单号: {sales_return.sales_order.order_number}",
                        created_by=request.user,
                    )

                # Notify creator
                if sales_return.created_by:
                    _create_return_notification(
                        sales_return,
                        "approved",
                        sales_return.created_by,
                        f"审核人：{request.user.username}",
                    )

                messages.success(request, f"退货单 {sales_return.return_number} 已批准，退款应付已自动生成")
                return redirect("sales:return_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"审核失败：{str(e)}")
            return redirect("sales:return_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "return": sales_return,
    }
    return render(request, "modules/sales/return_confirm_approve.html", context)


@login_required
@transaction.atomic
def return_receive(request, pk):
    """Mark return as received and process the return completely."""
    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)

    # Check permission
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限执行此操作")
        return redirect("sales:return_detail", pk=pk)

    # Check status
    if sales_return.status != "approved":
        messages.error(request, f"退货单状态为 {sales_return.get_status_display()}，无法收货")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        try:
            # Update return status to received first
            sales_return.status = "received"
            sales_return.received_date = timezone.now().date()
            sales_return.save()

            # 1. 创建库存调整单 - 将退货商品退回库存
            from inventory.models import InventoryTransaction

            from common.utils import DocumentNumberGenerator

            # 获取原发货的仓库
            warehouse = sales_return.delivery.warehouse if sales_return.delivery else None
            if not warehouse:
                # 如果没有关联发货单，使用默认仓库
                from inventory.models import Warehouse

                warehouse = Warehouse.objects.filter(is_deleted=False, is_active=True).first()
                if not warehouse:
                    raise ValueError("找不到可用的仓库")

            # 为每个退货明细创建库存入库交易
            # 只对需要库存管理的产品创建库存交易
            for return_item in sales_return.items.all():
                product = return_item.order_item.product

                # Skip inventory transaction if product doesn't track inventory
                # 跳过不需要库存管理的产品（如服务类产品）
                if not product.track_inventory:
                    continue

                # 创建库存交易记录 - 退货入库
                transaction = InventoryTransaction.objects.create(
                    transaction_type="return",
                    product=product,
                    warehouse=warehouse,
                    quantity=return_item.quantity,
                    unit_cost=product.cost_price,
                    reference_type="return",
                    reference_id=str(sales_return.id),
                    reference_number=sales_return.return_number,
                    operator=request.user,
                    notes=f"销售退货入库 - {sales_return.return_number}",
                    created_by=request.user,
                )

            # 2. 创建或更新退款记录并更新客户账户
            from decimal import Decimal

            from finance.models import CustomerAccount, Payment

            # 查找原订单关联的客户账款
            customer_account = CustomerAccount.objects.filter(
                sales_order=sales_return.sales_order, customer=sales_return.sales_order.customer
            ).first()

            # 计算实际退款金额（退款金额 - 重新入库费）
            actual_refund = sales_return.refund_amount

            if customer_account and actual_refund > 0:
                customer_account.balance -= actual_refund
                if customer_account.balance < 0:
                    customer_account.balance = 0
                customer_account.save()

            # 获取或创建退款支付记录
            existing_payment = Payment.objects.filter(
                is_deleted=False,
                payment_type="payment",
                customer=sales_return.sales_order.customer,
                reference_type="sales_return",
                reference_id=str(sales_return.id),
            ).first()

            if existing_payment:
                existing_payment.amount = actual_refund
                # existing_payment.status = 'completed'  # Do not auto-complete
                if existing_payment.status == "completed":
                    # If it was somehow completed (e.g. manual), leave it?
                    # Or should we enforce pending?
                    # Usually if we are receiving, we are confirming the amount.
                    # If we haven't paid yet, it should be pending.
                    pass
                else:
                    existing_payment.status = "pending"

                existing_payment.payment_date = timezone.now().date()
                existing_payment.description = f"销售退货退款（待付款） - {sales_return.return_number}"
                existing_payment.save()
            else:
                # ============ 在独立事务中生成唯一的付款单号 ============
                payment_number = None

                def generate_unique_payment_number():
                    from django.db import IntegrityError

                    from common.utils import DocumentNumberGenerator

                    max_retries = 5
                    for attempt in range(max_retries):
                        try:
                            with transaction.atomic(savepoint=False):
                                pn = DocumentNumberGenerator.generate("RF")
                                # 创建占位记录来验证单号唯一性
                                placeholder = Payment.objects.create(
                                    payment_number=pn,
                                    payment_type="payment",
                                    payment_method="bank_transfer",
                                    status="pending",
                                    amount=Decimal("0"),
                                    currency="CNY",
                                    payment_date=timezone.now().date(),
                                    description="PLACEHOLDER",
                                    created_by=request.user,
                                )
                                # 立即硬删除占位记录（只用于验证单号唯一性）
                                placeholder.hard_delete()
                            return pn
                        except IntegrityError:
                            continue
                    raise Exception(f"生成付款单号失败：已尝试 {max_retries} 次")

                try:
                    payment_number = generate_unique_payment_number()
                except Exception as e:
                    raise Exception(f"生成付款单号失败：{str(e)}")

                # 创建真正的付款记录
                Payment.objects.create(
                    payment_number=payment_number,
                    payment_type="payment",
                    payment_method="bank_transfer",
                    payment_date=timezone.now().date(),
                    amount=actual_refund,
                    currency=sales_return.sales_order.currency,
                    customer=sales_return.sales_order.customer,
                    reference_type="sales_return",
                    reference_id=str(sales_return.id),
                    reference_number=sales_return.return_number,
                    description=f"销售退货退款 - {sales_return.return_number}",
                    notes=f"退货单号: {sales_return.return_number}, 原订单号: {sales_return.sales_order.order_number}",
                    created_by=request.user,
                )

            # 3. 更新退货单状态为已处理（完成）
            sales_return.status = "processed"  # 直接设置为已处理，跳过处理步骤
            sales_return.save()

            # Notify creator and related parties
            if sales_return.created_by:
                _create_return_notification(
                    sales_return,
                    "processed",
                    sales_return.created_by,
                    f"处理人：{request.user.username}\n收货并处理完成",
                )

            if sales_return.approved_by and sales_return.approved_by != sales_return.created_by:
                _create_return_notification(
                    sales_return,
                    "processed",
                    sales_return.approved_by,
                    f"处理人：{request.user.username}\n收货并处理完成",
                )

            # Notify sales rep
            if sales_return.sales_order.sales_rep and sales_return.sales_order.sales_rep not in [
                sales_return.created_by,
                sales_return.approved_by,
            ]:
                _create_return_notification(
                    sales_return,
                    "processed",
                    sales_return.sales_order.sales_rep,
                    f"处理人：{request.user.username}\n收货并处理完成",
                )

            messages.success(
                request, f"退货单 {sales_return.return_number} 已收货并处理完成。" f"已创建库存入库记录，退款已更新。"
            )
            return redirect("sales:return_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"收货处理失败：{str(e)}")
            import traceback

            traceback.print_exc()
            return redirect("sales:return_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "return": sales_return,
    }
    return render(request, "modules/sales/return_confirm_receive.html", context)


@login_required
def return_process(request, pk):
    """Process a received return (refund, restock, etc.)."""
    from django.db import transaction

    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)

    # Check permission
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限执行此操作")
        return redirect("sales:return_detail", pk=pk)

    # Check status
    if sales_return.status != "received":
        messages.error(request, f"退货单状态为 {sales_return.get_status_display()}，无法处理")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Update restocking fee if provided
                restocking_fee = request.POST.get("restocking_fee", 0)
                if restocking_fee:
                    sales_return.restocking_fee = restocking_fee

                # 1. 创建库存调整单 - 将退货商品退回库存
                from inventory.models import InventoryTransaction

                from common.utils import DocumentNumberGenerator

                # 获取原发货的仓库
                warehouse = sales_return.delivery.warehouse if sales_return.delivery else None
                if not warehouse:
                    # 如果没有关联发货单，使用默认仓库
                    from inventory.models import Warehouse

                    warehouse = Warehouse.objects.filter(is_deleted=False, is_active=True).first()
                    if not warehouse:
                        raise ValueError("找不到可用的仓库")

                # 为每个退货明细创建库存入库交易
                # 只对需要库存管理的产品创建库存交易
                for return_item in sales_return.items.all():
                    product = return_item.order_item.product

                    # Skip inventory transaction if product doesn't track inventory
                    # 跳过不需要库存管理的产品（如服务类产品）
                    if not product.track_inventory:
                        continue

                    # 创建库存交易记录 - 退货入库
                    transaction = InventoryTransaction.objects.create(
                        transaction_type="return",
                        product=product,
                        warehouse=warehouse,
                        quantity=return_item.quantity,
                        unit_cost=product.cost_price,
                        reference_type="return",
                        reference_id=str(sales_return.id),
                        reference_number=sales_return.return_number,
                        operator=request.user,
                        notes=f"销售退货入库 - {sales_return.return_number}",
                        created_by=request.user,
                    )

                # 2. 创建退款记录并更新客户账户
                from decimal import Decimal

                from finance.models import CustomerAccount, Payment

                # 查找原订单关联的客户账款
                customer_account = CustomerAccount.objects.filter(
                    sales_order=sales_return.sales_order, customer=sales_return.sales_order.customer
                ).first()

                # 计算实际退款金额（退款金额 - 重新入库费）
                actual_refund = sales_return.refund_amount - Decimal(
                    str(sales_return.restocking_fee)
                )

                if customer_account and actual_refund > 0:
                    customer_account.balance -= actual_refund
                    if customer_account.balance < 0:
                        customer_account.balance = 0
                    customer_account.save()

                    existing_payment = Payment.objects.filter(
                        is_deleted=False,
                        payment_type="payment",
                        customer=sales_return.sales_order.customer,
                        reference_type="sales_return",
                        reference_id=str(sales_return.id),
                    ).first()

                    if existing_payment:
                        existing_payment.amount = actual_refund
                        existing_payment.status = "completed"
                        existing_payment.payment_date = timezone.now().date()
                        existing_payment.description = f"销售退货退款 - {sales_return.return_number}"
                        existing_payment.save()
                    else:
                        # ============ 在独立事务中生成唯一的付款单号 ============
                        payment_number = None

                        def generate_unique_payment_number():
                            from django.db import IntegrityError

                            from common.utils import DocumentNumberGenerator

                            max_retries = 5
                            for attempt in range(max_retries):
                                try:
                                    with transaction.atomic(savepoint=False):
                                        pn = DocumentNumberGenerator.generate("RF")
                                        # 创建占位记录来验证单号唯一性
                                        placeholder = Payment.objects.create(
                                            payment_number=pn,
                                            payment_type="payment",
                                            payment_method="bank_transfer",
                                            status="pending",
                                            amount=Decimal("0"),
                                            currency="CNY",
                                            payment_date=timezone.now().date(),
                                            description="PLACEHOLDER",
                                            created_by=request.user,
                                        )
                                        # 立即硬删除占位记录（只用于验证单号唯一性）
                                        placeholder.hard_delete()
                                    return pn
                                except IntegrityError:
                                    continue
                            raise Exception(f"生成付款单号失败：已尝试 {max_retries} 次")

                        try:
                            payment_number = generate_unique_payment_number()
                        except Exception as e:
                            raise Exception(f"生成付款单号失败：{str(e)}")

                        # 创建真正的付款记录
                        Payment.objects.create(
                            payment_number=payment_number,
                            payment_type="payment",
                            payment_method="bank_transfer",
                            payment_date=timezone.now().date(),
                            amount=actual_refund,
                            currency=sales_return.sales_order.currency,
                            customer=sales_return.sales_order.customer,
                            reference_type="sales_return",
                            reference_id=str(sales_return.id),
                            reference_number=sales_return.return_number,
                            description=f"销售退货退款 - {sales_return.return_number}",
                            notes=f"退货单号: {sales_return.return_number}, 原订单号: {sales_return.sales_order.order_number}",
                            created_by=request.user,
                        )

                # 3. 更新退货单状态
                sales_return.status = "processed"
                sales_return.save()

                # Notify creator and related parties
                if sales_return.created_by:
                    _create_return_notification(
                        sales_return,
                        "processed",
                        sales_return.created_by,
                        f"处理人：{request.user.username}\n实际退款：¥{actual_refund}\n重新入库费：¥{sales_return.restocking_fee}",
                    )

                if sales_return.approved_by and sales_return.approved_by != sales_return.created_by:
                    _create_return_notification(
                        sales_return,
                        "processed",
                        sales_return.approved_by,
                        f"处理人：{request.user.username}\n实际退款：¥{actual_refund}",
                    )

                # Notify sales rep
                if (
                    sales_return.sales_order.sales_rep
                    and sales_return.sales_order.sales_rep
                    not in [sales_return.created_by, sales_return.approved_by]
                ):
                    _create_return_notification(
                        sales_return,
                        "processed",
                        sales_return.sales_order.sales_rep,
                        f"处理人：{request.user.username}\n实际退款：¥{actual_refund}",
                    )

                messages.success(
                    request,
                    f"退货单 {sales_return.return_number} 已处理完成。" f"已创建库存入库记录，实际退款金额：¥{actual_refund}",
                )
                return redirect("sales:return_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"处理失败：{str(e)}")
            import traceback

            traceback.print_exc()
            return redirect("sales:return_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "return": sales_return,
    }
    return render(request, "modules/sales/return_confirm_process.html", context)


@login_required
def return_reject(request, pk):
    """Reject a sales return."""
    sales_return = get_object_or_404(SalesReturn, pk=pk, is_deleted=False)

    # Check permission
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "您没有权限执行此操作")
        return redirect("sales:return_detail", pk=pk)

    # Check status
    if sales_return.status not in ["pending", "approved"]:
        messages.error(request, f"退货单状态为 {sales_return.get_status_display()}，无法拒绝")
        return redirect("sales:return_detail", pk=pk)

    if request.method == "POST":
        try:
            sales_return.status = "rejected"
            sales_return.save()

            # Notify creator
            if sales_return.created_by:
                _create_return_notification(
                    sales_return,
                    "rejected",
                    sales_return.created_by,
                    f"拒绝人：{request.user.username}\n请联系相关负责人了解拒绝原因",
                )

            # Notify sales rep
            if (
                sales_return.sales_order.sales_rep
                and sales_return.sales_order.sales_rep != sales_return.created_by
            ):
                _create_return_notification(
                    sales_return,
                    "rejected",
                    sales_return.sales_order.sales_rep,
                    f"拒绝人：{request.user.username}",
                )

            messages.success(request, f"退货单 {sales_return.return_number} 已拒绝")
            return redirect("sales:return_detail", pk=pk)
        except Exception as e:
            messages.error(request, f"操作失败：{str(e)}")
            return redirect("sales:return_detail", pk=pk)

    # GET request - show confirmation page
    context = {
        "return": sales_return,
    }
    return render(request, "modules/sales/return_confirm_reject.html", context)


@login_required
def return_statistics(request):
    """Sales return statistics and analysis report."""
    import json
    from datetime import datetime, timedelta

    # Get date range from request
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    # Default to last 3 months if not specified
    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

    if not date_from:
        date_from = date_to - timedelta(days=90)
    else:
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

    # Base queryset
    returns = SalesReturn.objects.filter(
        is_deleted=False, return_date__gte=date_from, return_date__lte=date_to
    )

    # 1. 总体统计
    total_returns = returns.count()
    total_refund = returns.aggregate(total=Sum("refund_amount"))["total"] or 0

    # 按状态统计
    status_stats = (
        returns.values("status")
        .annotate(count=Count("id"), total_refund=Sum("refund_amount"))
        .order_by("-count")
    )

    # 2. 退货原因统计
    reason_stats = (
        returns.values("reason")
        .annotate(
            count=Count("id"),
            total_refund=Sum("refund_amount"),
            percentage=Count("id") * 100.0 / total_returns if total_returns > 0 else 0,
        )
        .order_by("-count")
    )

    # 准备退货原因图表数据
    reason_labels = [
        dict(SalesReturn.RETURN_REASONS).get(item["reason"], item["reason"])
        for item in reason_stats
    ]
    reason_data = [item["count"] for item in reason_stats]

    # 3. 按月统计退货趋势
    monthly_stats = (
        returns.annotate(month=TruncMonth("return_date"))
        .values("month")
        .annotate(count=Count("id"), total_refund=Sum("refund_amount"))
        .order_by("month")
    )

    # 准备月度趋势图表数据
    monthly_labels = [item["month"].strftime("%Y-%m") for item in monthly_stats]
    monthly_counts = [item["count"] for item in monthly_stats]
    monthly_refunds = [float(item["total_refund"] or 0) for item in monthly_stats]

    # 4. 按产品统计
    from sales.models import SalesReturnItem

    product_stats = (
        SalesReturnItem.objects.filter(return_order__in=returns)
        .values("order_item__product__code", "order_item__product__name")
        .annotate(
            return_count=Count("id"),
            total_quantity=Sum("quantity"),
            total_refund=Sum(F("quantity") * F("unit_price")),
        )
        .order_by("-return_count")[:10]
    )  # Top 10

    # 5. 按客户统计
    customer_stats = (
        returns.values("sales_order__customer__name")
        .annotate(return_count=Count("id"), total_refund=Sum("refund_amount"))
        .order_by("-return_count")[:10]
    )  # Top 10

    # 6. 退货率分析（基于已完成的订单）
    completed_orders = SalesOrder.objects.filter(
        is_deleted=False,
        order_date__gte=date_from,
        order_date__lte=date_to,
        status__in=["shipped", "delivered", "completed"],
    )
    total_orders = completed_orders.count()
    orders_with_returns = (
        completed_orders.filter(salesreturn__isnull=False, salesreturn__is_deleted=False)
        .distinct()
        .count()
    )

    return_rate = (orders_with_returns / total_orders * 100) if total_orders > 0 else 0

    # 7. 平均处理时间分析
    processed_returns = returns.filter(status="processed")
    avg_processing_days = 0
    if processed_returns.exists():
        total_days = 0
        count = 0
        for ret in processed_returns:
            if ret.return_date and ret.updated_at:
                days = (ret.updated_at.date() - ret.return_date).days
                total_days += days
                count += 1
        avg_processing_days = total_days / count if count > 0 else 0

    context = {
        "date_from": date_from,
        "date_to": date_to,
        # 总体统计
        "total_returns": total_returns,
        "total_refund": total_refund,
        "return_rate": round(return_rate, 2),
        "avg_processing_days": round(avg_processing_days, 1),
        # 详细统计
        "status_stats": status_stats,
        "reason_stats": reason_stats,
        "monthly_stats": monthly_stats,
        "product_stats": product_stats,
        "customer_stats": customer_stats,
        # 图表数据
        "reason_labels_json": json.dumps(reason_labels, ensure_ascii=False),
        "reason_data_json": json.dumps(reason_data),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_counts_json": json.dumps(monthly_counts),
        "monthly_refunds_json": json.dumps(monthly_refunds),
    }

    return render(request, "modules/sales/return_statistics.html", context)


# ============================================
# 打印模板选择 API
# ============================================


@login_required
def api_get_available_templates(request):
    """
    获取当前单据类型的可用模板列表

    URL参数:
        - document_type: 单据类型 (如 'quote', 'sales_order')
        - quote_type: 报价单类型 (可选，如 'DOMESTIC', 'OVERSEAS')

    返回:
        JSON: {
            'success': True,
            'templates': [
                {'id': 1, 'name': '标准报价单', 'is_default': True},
                ...
            ],
            'current_template_id': 1
        }
    """
    from core.models import DefaultTemplateMapping, PrintTemplate
    from core.services.template_selector import TemplateSelector

    document_type = request.GET.get("document_type", "quote")
    quote_type = request.GET.get("quote_type", "").upper()

    # 确定完整的单据类型（如果是报价单，区分国内/海外）
    if document_type == "quote" and quote_type:
        document_type_full = f"quote_domestic" if quote_type == "DOMESTIC" else "quote_overseas"
    else:
        document_type_full = document_type

    # 获取可用模板列表
    templates = TemplateSelector.get_available_templates(document_type)

    # 获取默认模板
    default_template = TemplateSelector.get_default_template(document_type_full)
    default_template_id = default_template.id if default_template else None

    # 构建返回数据
    template_data = [
        {
            "id": template.id,
            "name": template.name,
            "is_default": template.id == default_template_id,
            "category": template.get_template_category_display(),
        }
        for template in templates
    ]

    return JsonResponse(
        {
            "success": True,
            "templates": template_data,
            "current_template_id": default_template_id,
            "document_type": document_type_full,
        }
    )


@login_required
def api_set_default_template(request):
    """
    设置默认打印模板

    POST参数:
        - template_id: 模板ID
        - document_type: 单据类型 (如 'quote_domestic', 'quote_overseas')

    返回:
        JSON: {'success': True, 'message': '已设置为默认模板'}
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "仅支持POST请求"}, status=405)

    from core.models import DefaultTemplateMapping, PrintTemplate

    try:
        template_id = request.POST.get("template_id")
        document_type = request.POST.get("document_type")

        if not template_id or not document_type:
            return JsonResponse(
                {"success": False, "error": "缺少必要参数: template_id 或 document_type"}, status=400
            )

        # 验证模板是否存在
        template = get_object_or_404(
            PrintTemplate, pk=template_id, is_deleted=False, is_active=True
        )

        # 更新或创建默认模板映射
        mapping, created = DefaultTemplateMapping.objects.update_or_create(
            document_type=document_type,
            defaults={
                "template": template,
                "updated_by": request.user,
            },
        )

        if created:
            mapping.created_by = request.user
            mapping.save()

        return JsonResponse(
            {
                "success": True,
                "message": f'已将"{template.name}"设为默认模板',
                "template_id": template.id,
                "template_name": template.name,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": f"设置默认模板失败: {str(e)}"}, status=500)


# ============================================
@login_required
@transaction.atomic
def order_mark_invoiced(request, pk):
    """Mark sales order as invoiced (update invoice status only)."""
    order = get_object_or_404(SalesOrder, pk=pk, is_deleted=False)

    if request.method != "POST":
        messages.error(request, "无效的请求方式")
        return redirect("sales:order_detail", pk=pk)

    try:
        order.invoice_status = "invoiced"
        order.save()
        messages.success(request, f"订单 {order.order_number} 已标记为已开票")
    except Exception as e:
        messages.error(request, f"更新开票状态失败：{str(e)}")

    return redirect("sales:order_detail", pk=pk)


# ============================================
# 销售报表
# ============================================


@login_required
def sales_order_report(request):
    """
    销售订单报表 - 高级筛选和统计功能

    支持多维度筛选：
    - 单据编号、状态、日期范围
    - 客户、业务员、部门
    - 产品、金额范围
    - 交付日期范围
    """
    from customers.models import Customer
    from products.models import Product
    from users.models import User

    # 基础查询集
    queryset = (
        SalesOrder.objects.filter(is_deleted=False)
        .select_related("customer", "sales_rep", "created_by")
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

    # 客户
    customer_id = request.GET.get("customer", "").strip()
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)

    # 业务员
    salesperson_id = request.GET.get("salesperson", "").strip()
    if salesperson_id:
        queryset = queryset.filter(sales_rep_id=salesperson_id)

    # 备注/说明
    notes = request.GET.get("notes", "").strip()
    if notes:
        queryset = queryset.filter(Q(notes__icontains=notes) | Q(customer_notes__icontains=notes))

    # 金额范围
    amount_min = request.GET.get("amount_min", "").strip()
    amount_max = request.GET.get("amount_max", "").strip()
    if amount_min:
        queryset = queryset.filter(total_amount__gte=amount_min)
    if amount_max:
        queryset = queryset.filter(total_amount__lte=amount_max)

    # 交付日期范围
    delivery_from = request.GET.get("delivery_from", "").strip()
    delivery_to = request.GET.get("delivery_to", "").strip()
    if delivery_from:
        queryset = queryset.filter(required_date__gte=delivery_from)
    if delivery_to:
        queryset = queryset.filter(required_date__lte=delivery_to)

    # 产品筛选
    product_id = request.GET.get("product", "").strip()
    if product_id:
        queryset = queryset.filter(items__product_id=product_id).distinct()

    # 排序
    # 按创建时间降序（最新的在最上面）
    queryset = queryset.order_by("-created_at")

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
    customers = Customer.objects.filter(is_deleted=False).order_by("name")
    salespersons = User.objects.filter(is_active=True).order_by("username")
    products = Product.objects.filter(is_deleted=False).order_by("name")

    context = {
        "page_obj": page_obj,
        "stats": stats,
        "status_choices": SalesOrder.ORDER_STATUS,
        "customers": customers,
        "salespersons": salespersons,
        "products": products,
        # 保留筛选条件（用于表单回显）
        "filter_order_number": order_number,
        "filter_status": status,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_customer": customer_id,
        "filter_salesperson": salesperson_id,
        "filter_notes": notes,
        "filter_amount_min": amount_min,
        "filter_amount_max": amount_max,
        "filter_delivery_from": delivery_from,
        "filter_delivery_to": delivery_to,
        "filter_product": product_id,
    }

    return render(request, "modules/sales/order_report.html", context)


# ============================================
# 销售借用管理视图
# ============================================


def _create_loan_notification(sales_loan, action, recipient, extra_message=""):
    """
    Helper function to create notifications for sales loan operations.

    Args:
        sales_loan: SalesLoan instance
        action: Action performed (created, returned, converting, converted, rejected)
        recipient: User to receive the notification
        extra_message: Additional message to append
    """
    action_messages = {
        "created": f"新借用单 {sales_loan.loan_number} 已创建",
        "returned": f"借用单 {sales_loan.loan_number} 已归还",
        "converting": f"借用单 {sales_loan.loan_number} 申请转销售",
        "converted": f"借用单 {sales_loan.loan_number} 已转销售订单",
        "rejected": f"借用单 {sales_loan.loan_number} 转销售申请被拒绝",
    }

    title = action_messages.get(action, f"借用单 {sales_loan.loan_number} 状态更新")
    message = f"客户：{sales_loan.customer.name}\n"
    message += f"借出日期：{sales_loan.loan_date}\n"
    if extra_message:
        message += f"\n{extra_message}"

    notification_type = "success" if action in ["converted", "returned"] else "info"
    if action == "rejected":
        notification_type = "warning"

    Notification.create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        category="sales",
        reference_type="sales_loan",
        reference_id=str(sales_loan.id),
        reference_url=reverse("sales:loan_detail", args=[sales_loan.pk]),
    )


@login_required
def loan_list(request):
    """销售借用单列表"""
    from customers.models import Customer

    loans = SalesLoan.objects.filter(is_deleted=False).select_related(
        "customer", "salesperson", "converted_order"
    )

    # 搜索
    search = request.GET.get("search", "")
    if search:
        loans = loans.filter(
            Q(loan_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(purpose__icontains=search)
        )

    # 状态筛选
    status = request.GET.get("status", "")
    if status:
        loans = loans.filter(status=status)

    # 客户筛选
    customer_id = request.GET.get("customer", "")
    if customer_id:
        loans = loans.filter(customer_id=customer_id)

    # 日期范围筛选
    date_from = request.GET.get("date_from", "")
    if date_from:
        loans = loans.filter(loan_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        loans = loans.filter(loan_date__lte=date_to)

    # 按创建时间降序（最新的在最上面）
    loans = loans.order_by("-created_at")

    # 统计卡片数据
    stats = {
        "loaned_count": loans.filter(status="loaned").count(),
        "partially_returned_count": loans.filter(status="partially_returned").count(),
        "converting_count": loans.filter(status="converting").count(),
        "converted_count": loans.filter(status="converted").count(),
    }

    # 分页
    paginator = Paginator(loans, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # 获取客户列表用于筛选
    customers = Customer.objects.filter(is_deleted=False).order_by("name")

    context = {
        "page_obj": page_obj,
        "stats": stats,
        "search": search,
        "status": status,
        "customer_id": customer_id,
        "date_from": date_from,
        "date_to": date_to,
        "customers": customers,
        "total_count": paginator.count,
        "status_choices": SalesLoan.LOAN_STATUS,
    }
    return render(request, "modules/sales/loan_list.html", context)


@login_required
@transaction.atomic
def loan_create(request):
    """创建借用单"""
    from customers.models import Customer
    from django.contrib.auth import get_user_model
    from inventory.models import InventoryTransaction, Warehouse
    from products.models import Product

    User = get_user_model()

    if request.method == "POST":
        try:
            # 获取借用仓
            try:
                borrow_warehouse = Warehouse.get_borrow_warehouse()
            except Warehouse.DoesNotExist:
                raise ValueError("借用仓不存在，请先创建借用仓")

            # 提取表单数据
            loan_data = {
                "loan_number": DocumentNumberGenerator.generate("sales_loan"),
                "customer_id": request.POST.get("customer"),
                "salesperson_id": request.POST.get("salesperson") or request.user.id,
                "loan_date": request.POST.get("loan_date"),
                "expected_return_date": request.POST.get("expected_return_date") or None,
                "purpose": request.POST.get("purpose", ""),
                "delivery_address": request.POST.get("delivery_address", ""),
                "contact_person": request.POST.get("contact_person", ""),
                "contact_phone": request.POST.get("contact_phone", ""),
                "notes": request.POST.get("notes", ""),
                "status": "loaned",  # 直接进入借出中状态
            }

            loan = SalesLoan(**loan_data)
            loan.created_by = request.user
            loan.save()

            # 处理借用明细
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            from decimal import ROUND_HALF_UP, Decimal

            for item_data in items_data:
                product_id = item_data.get("product_id")
                quantity = Decimal(str(item_data.get("quantity", 0)))

                if product_id and quantity > 0:
                    quantity = quantity.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                    loan_item = SalesLoanItem.objects.create(
                        loan=loan,
                        product_id=product_id,
                        quantity=quantity,
                        batch_number=item_data.get("batch_number", ""),
                        serial_numbers=item_data.get("serial_numbers", ""),
                        specifications=item_data.get("specifications", ""),
                        notes=item_data.get("notes", ""),
                        created_by=request.user,
                    )

                    # 创建出库记录，从借用仓出库
                    InventoryTransaction.objects.create(
                        transaction_type="out",
                        product_id=product_id,
                        warehouse=borrow_warehouse,
                        quantity=-quantity,  # 负数表示出库
                        reference_number=loan.loan_number,
                        notes=f"销售借用单 {loan.loan_number} 出库",
                        operator=request.user,
                    )

            # 创建通知
            if loan.salesperson and loan.salesperson != request.user:
                _create_loan_notification(
                    loan, "created", loan.salesperson, f"创建人：{request.user.username}"
                )

            messages.success(request, f"借用单 {loan.loan_number} 创建成功！")
            return redirect("sales:loan_detail", pk=loan.pk)

        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")
            return redirect("sales:loan_list")

    # GET请求
    customers = Customer.objects.filter(is_deleted=False).order_by("name")
    products = Product.objects.filter(is_deleted=False).order_by("name")
    salespersons = User.objects.filter(is_active=True).order_by("username")

    context = {
        "customers": customers,
        "products": products,
        "salespersons": salespersons,
        "today": timezone.now().date(),
    }
    return render(request, "modules/sales/loan_form.html", context)


@login_required
def loan_detail(request, pk):
    """借用单详情"""
    loan = get_object_or_404(
        SalesLoan.objects.filter(is_deleted=False)
        .select_related("customer", "salesperson", "converted_order", "conversion_approved_by")
        .prefetch_related("items__product"),
        pk=pk,
    )

    # 计算权限
    can_edit = loan.status == "draft"
    can_delete = loan.status == "draft"
    can_return = (
        loan.status in ["loaned", "partially_returned"] and loan.total_remaining_quantity > 0
    )
    can_request_conversion = (
        loan.status in ["loaned", "partially_returned"] and loan.total_remaining_quantity > 0
    )
    can_approve_conversion = request.user.is_staff and loan.status == "converting"

    context = {
        "loan": loan,
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_return": can_return,
        "can_request_conversion": can_request_conversion,
        "can_approve_conversion": can_approve_conversion,
    }
    return render(request, "modules/sales/loan_detail.html", context)


@login_required
@transaction.atomic
def loan_update(request, pk):
    """编辑借用单"""
    from customers.models import Customer
    from django.contrib.auth import get_user_model
    from products.models import Product

    User = get_user_model()

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status != "draft":
        messages.error(request, "只有草稿状态的借用单可以编辑")
        return redirect("sales:loan_detail", pk=pk)

    if request.method == "POST":
        try:
            # 更新主单
            loan.customer_id = request.POST.get("customer")
            loan.salesperson_id = request.POST.get("salesperson") or request.user.id
            loan.loan_date = request.POST.get("loan_date")
            loan.expected_return_date = request.POST.get("expected_return_date") or None
            loan.purpose = request.POST.get("purpose", "")
            loan.delivery_address = request.POST.get("delivery_address", "")
            loan.contact_person = request.POST.get("contact_person", "")
            loan.contact_phone = request.POST.get("contact_phone", "")
            loan.notes = request.POST.get("notes", "")
            loan.updated_by = request.user
            loan.save()

            # 删除旧明细
            loan.items.all().delete()

            # 添加新明细
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            from decimal import ROUND_HALF_UP, Decimal

            for item_data in items_data:
                product_id = item_data.get("product_id")
                quantity = Decimal(str(item_data.get("quantity", 0)))

                if product_id and quantity > 0:
                    quantity = quantity.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                    SalesLoanItem.objects.create(
                        loan=loan,
                        product_id=product_id,
                        quantity=quantity,
                        batch_number=item_data.get("batch_number", ""),
                        serial_numbers=item_data.get("serial_numbers", ""),
                        specifications=item_data.get("specifications", ""),
                        notes=item_data.get("notes", ""),
                        created_by=request.user,
                    )

            messages.success(request, "借用单更新成功！")
            return redirect("sales:loan_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET请求
    customers = Customer.objects.filter(is_deleted=False).order_by("name")
    products = Product.objects.filter(is_deleted=False).order_by("name")
    salespersons = User.objects.filter(is_active=True).order_by("username")

    context = {
        "loan": loan,
        "customers": customers,
        "products": products,
        "salespersons": salespersons,
        "is_edit": True,
    }
    return render(request, "modules/sales/loan_form.html", context)


@login_required
def loan_delete(request, pk):
    """删除借用单（软删除）"""
    from django.views.decorators.http import require_POST

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("sales:loan_detail", pk=pk)

    if loan.status != "draft":
        messages.error(request, "只有草稿状态的借用单可以删除")
        return redirect("sales:loan_detail", pk=pk)

    loan.delete()  # 软删除
    messages.success(request, f"借用单 {loan.loan_number} 已删除")
    return redirect("sales:loan_list")


@login_required
@transaction.atomic
def loan_return(request, pk):
    """处理归还（支持部分归还）"""
    from inventory.models import InventoryTransaction, Warehouse

    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status not in ["loaned", "partially_returned"]:
        messages.error(request, "当前状态不允许归还")
        return redirect("sales:loan_detail", pk=pk)

    if request.method == "POST":
        try:
            # 获取借用仓
            try:
                borrow_warehouse = Warehouse.get_borrow_warehouse()
            except Warehouse.DoesNotExist:
                raise ValueError("借用仓不存在，请先创建借用仓")

            # 处理归还明细
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            from decimal import Decimal

            has_returned = False
            for item_data in items_data:
                item_id = item_data.get("item_id")
                return_qty = Decimal(str(item_data.get("return_quantity", 0)))

                if item_id and return_qty > 0:
                    item = SalesLoanItem.objects.get(pk=item_id, loan=loan)

                    # 验证归还数量
                    if return_qty > item.remaining_quantity:
                        raise ValueError(
                            f"产品 {item.product.name} 的归还数量 ({return_qty}) "
                            f"不能超过剩余数量 ({item.remaining_quantity})"
                        )

                    # 更新已归还数量
                    item.returned_quantity += return_qty
                    item.updated_by = request.user
                    item.save()
                    has_returned = True

                    # 创建入库记录，入库到借用仓
                    InventoryTransaction.objects.create(
                        transaction_type="in",
                        product=item.product,
                        warehouse=borrow_warehouse,
                        quantity=return_qty,  # 正数表示入库
                        reference_number=loan.loan_number,
                        notes=f"销售借用单 {loan.loan_number} 归还入库",
                        operator=request.user,
                    )

            if not has_returned:
                raise ValueError("请至少归还一个产品")

            # 更新借用单状态
            if loan.is_fully_returned:
                loan.status = "fully_returned"
            else:
                loan.status = "partially_returned"
            loan.updated_by = request.user
            loan.save()

            # 创建通知
            if loan.salesperson:
                _create_loan_notification(
                    loan, "returned", loan.salesperson, f"归还处理人：{request.user.username}"
                )

            messages.success(request, "归还处理成功！")
            return redirect("sales:loan_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"归还处理失败：{str(e)}")

    # GET请求
    context = {
        "loan": loan,
    }
    return render(request, "modules/sales/loan_return.html", context)


@login_required
@transaction.atomic
def loan_request_conversion(request, pk):
    """发起转销售订单请求（需要审核）"""
    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if loan.status not in ["loaned", "partially_returned"]:
        messages.error(request, "当前状态不允许转销售")
        return redirect("sales:loan_detail", pk=pk)

    if loan.total_remaining_quantity <= 0:
        messages.error(request, "没有可转销售的数量")
        return redirect("sales:loan_detail", pk=pk)

    if request.method == "POST":
        try:
            # 获取转换数量和手动输入的价格
            items_json = request.POST.get("items_json", "[]")
            items_data = json.loads(items_json)

            from decimal import Decimal

            has_conversion = False
            for item_data in items_data:
                item_id = item_data.get("item_id")
                convert_qty = Decimal(str(item_data.get("convert_quantity", 0)))
                unit_price = Decimal(str(item_data.get("unit_price", 0)))

                if item_id and convert_qty > 0:
                    item = SalesLoanItem.objects.get(pk=item_id, loan=loan)

                    # 验证转换数量
                    if convert_qty > item.remaining_quantity:
                        raise ValueError(
                            f"产品 {item.product.name} 的转换数量 ({convert_qty}) "
                            f"不能超过剩余数量 ({item.remaining_quantity})"
                        )

                    # 验证单价
                    if unit_price <= 0:
                        raise ValueError(f"产品 {item.product.name} 的单价必须大于0")

                    # 保存转换数量和价格
                    item.conversion_quantity = convert_qty
                    item.conversion_unit_price = unit_price
                    item.updated_by = request.user
                    item.save()
                    has_conversion = True

            if not has_conversion:
                raise ValueError("请至少选择一个产品进行转换")

            # 更新状态为待审核
            loan.status = "converting"
            loan.conversion_notes = request.POST.get("conversion_notes", "")
            loan.updated_by = request.user
            loan.save()

            # 创建通知给管理员
            from django.contrib.auth import get_user_model

            User = get_user_model()
            managers = User.objects.filter(is_staff=True, is_active=True)
            for manager in managers[:5]:  # 通知前5个管理员
                _create_loan_notification(
                    loan, "converting", manager, f"申请人：{request.user.username}"
                )

            messages.success(request, "转销售请求已提交，等待审核")
            return redirect("sales:loan_detail", pk=pk)

        except Exception as e:
            messages.error(request, f"提交失败：{str(e)}")

    # GET请求
    context = {
        "loan": loan,
    }
    return render(request, "modules/sales/loan_request_conversion.html", context)


@login_required
@transaction.atomic
def loan_approve_conversion(request, pk):
    """审核通过转销售请求，生成销售订单"""
    loan = get_object_or_404(SalesLoan, pk=pk, is_deleted=False)

    if request.method != "POST":
        messages.error(request, "无效的请求方法")
        return redirect("sales:loan_detail", pk=pk)

    if not request.user.is_staff:
        messages.error(request, "您没有审核权限")
        return redirect("sales:loan_detail", pk=pk)

    if loan.status != "converting":
        messages.error(request, "当前状态不允许审核")
        return redirect("sales:loan_detail", pk=pk)

    try:
        # 创建销售订单
        order_data = {
            "order_number": DocumentNumberGenerator.generate("sales_order"),
            "customer": loan.customer,
            "status": "draft",
            "payment_status": "unpaid",
            "order_date": timezone.now().date(),
            "sales_rep": loan.salesperson,
            "notes": f"由借用单 {loan.loan_number} 转换而来\n{loan.conversion_notes}",
        }

        order = SalesOrder(**order_data)
        order.created_by = request.user
        order.save()

        # 创建订单明细
        from decimal import Decimal

        subtotal = Decimal("0.00")

        for item in loan.items.filter(is_deleted=False):
            if item.conversion_quantity > 0 and item.conversion_unit_price:
                order_item = SalesOrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.conversion_quantity,
                    unit_price=item.conversion_unit_price,
                    notes=f"来自借用单 {loan.loan_number}",
                    created_by=request.user,
                )
                subtotal += order_item.line_total

        # 更新订单金额
        order.subtotal = subtotal
        order.total_amount = subtotal  # 简化处理，暂不考虑税费
        order.save()

        # 更新借用单
        loan.status = "converted"
        loan.converted_order = order
        loan.conversion_approved_by = request.user
        loan.conversion_approved_at = timezone.now()
        loan.updated_by = request.user
        loan.save()

        # 创建通知
        if loan.salesperson:
            _create_loan_notification(
                loan,
                "converted",
                loan.salesperson,
                f"审核人：{request.user.username}\n" f"订单号：{order.order_number}",
            )

        messages.success(request, f"转销售已审核通过，生成销售订单 {order.order_number}")
        return redirect("sales:order_detail", pk=order.pk)

    except Exception as e:
        messages.error(request, f"审核失败：{str(e)}")
        return redirect("sales:loan_detail", pk=pk)
