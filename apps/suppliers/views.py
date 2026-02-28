"""
Supplier views for the ERP system.
"""

from core.utils.code_generator import CodeGenerator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Supplier, SupplierCategory, SupplierContact


@login_required
def supplier_list(request):
    """
    List all suppliers with search and filter capabilities.
    """
    suppliers = (
        Supplier.objects.filter(is_deleted=False)
        .select_related("category", "buyer")
        .prefetch_related("contacts")
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(contact_person__icontains=search)
            | Q(phone__icontains=search)
        )

    # Filter by level
    level = request.GET.get("level", "")
    if level:
        suppliers = suppliers.filter(level=level)

    # Filter by category
    category = request.GET.get("category", "")
    if category:
        suppliers = suppliers.filter(category_id=category)

    # Filter by approval status
    is_approved = request.GET.get("is_approved", "")
    if is_approved == "true":
        suppliers = suppliers.filter(is_approved=True)
    elif is_approved == "false":
        suppliers = suppliers.filter(is_approved=False)

    # Sorting
    sort = request.GET.get("sort", "-created_at")
    suppliers = suppliers.order_by(sort)

    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter
    categories = SupplierCategory.objects.filter(is_active=True)

    context = {
        "page_obj": page_obj,
        "search": search,
        "level": level,
        "category": category,
        "is_approved": is_approved,
        "categories": categories,
        "total_count": paginator.count,
    }
    return render(request, "modules/suppliers/supplier_list.html", context)


@login_required
def supplier_detail(request, pk):
    """
    Display supplier details.
    """
    supplier = get_object_or_404(
        Supplier.objects.filter(is_deleted=False)
        .select_related("category", "buyer")
        .prefetch_related("contacts"),
        pk=pk,
    )

    context = {
        "supplier": supplier,
        "contacts": supplier.contacts.filter(is_deleted=False),
    }
    return render(request, "modules/suppliers/supplier_detail.html", context)


@login_required
@transaction.atomic
def supplier_create(request):
    """
    Create a new supplier.
    """
    if request.method == "POST":
        try:
            # Generate supplier code automatically
            supplier_code = CodeGenerator.generate_supplier_code()

            data = {
                "name": request.POST.get("name"),
                "code": supplier_code,  # Use auto-generated code
                "category_id": request.POST.get("category") or None,
                "level": request.POST.get("level", "C"),
                "website": request.POST.get("website", ""),
                "address": request.POST.get("address", ""),
                "city": request.POST.get("city", ""),
                "province": request.POST.get("province", ""),
                "country": request.POST.get("country", "中国"),
                "postal_code": request.POST.get("postal_code", ""),
                "tax_number": request.POST.get("tax_number", ""),
                "registration_number": request.POST.get("registration_number", ""),
                "legal_representative": request.POST.get("legal_representative", ""),
                "payment_terms": request.POST.get("payment_terms", ""),
                "currency": request.POST.get("currency", "CNY"),
                "bank_name": request.POST.get("bank_name", ""),
                "bank_account": request.POST.get("bank_account", ""),
                "buyer_id": request.POST.get("buyer") or None,
                "lead_time": request.POST.get("lead_time", 0),
                "min_order_amount": request.POST.get("min_order_amount", 0),
                "quality_rating": request.POST.get("quality_rating", 0),
                "delivery_rating": request.POST.get("delivery_rating", 0),
                "service_rating": request.POST.get("service_rating", 0),
                "certifications": request.POST.get("certifications", ""),
                "is_active": request.POST.get("is_active") == "on",
                "is_approved": request.POST.get("is_approved") == "on",
                "notes": request.POST.get("notes", ""),
            }

            supplier = Supplier(**data)
            supplier.created_by = request.user
            supplier.save()

            contacts_data = []
            import re

            for key in request.POST:
                if key.startswith("contacts[") and "[name]" in key:
                    m = re.match(r"contacts\[(\d+)\]", key)
                    if m:
                        i = m.group(1)
                        name = request.POST.get(f"contacts[{i}][name]", "").strip()
                        if name:
                            contacts_data.append(
                                {
                                    "name": name,
                                    "position": request.POST.get(f"contacts[{i}][position]", ""),
                                    "phone": request.POST.get(f"contacts[{i}][phone]", ""),
                                    "email": request.POST.get(f"contacts[{i}][email]", ""),
                                    "notes": request.POST.get(f"contacts[{i}][notes]", ""),
                                    "is_primary": request.POST.get(f"contacts[{i}][is_primary]")
                                    == "on",
                                }
                            )

            primary_set = False
            for c in contacts_data:
                is_primary = c["is_primary"] and not primary_set
                if is_primary:
                    primary_set = True
                SupplierContact.objects.create(
                    supplier=supplier,
                    name=c["name"],
                    position=c["position"],
                    phone=c["phone"],
                    email=c["email"],
                    notes=c["notes"],
                    is_primary=is_primary,
                    created_by=request.user,
                )

            messages.success(request, f"供应商 {supplier.name} 创建成功！供应商编码：{supplier_code}")
            return redirect("suppliers:supplier_detail", pk=supplier.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    from django.contrib.auth import get_user_model

    User = get_user_model()

    categories = SupplierCategory.objects.filter(is_active=True)
    buyers = User.objects.filter(is_active=True)

    context = {
        "categories": categories,
        "buyers": buyers,
        "action": "create",
    }
    return render(request, "modules/suppliers/supplier_form.html", context)


@login_required
@transaction.atomic
def supplier_update(request, pk):
    """
    Update an existing supplier.
    """
    supplier = get_object_or_404(Supplier, pk=pk, is_deleted=False)

    if request.method == "POST":
        supplier.name = request.POST.get("name")
        supplier.category_id = request.POST.get("category") or None
        supplier.level = request.POST.get("level", "C")
        supplier.website = request.POST.get("website", "")
        supplier.address = request.POST.get("address", "")
        supplier.city = request.POST.get("city", "")
        supplier.province = request.POST.get("province", "")
        supplier.country = request.POST.get("country", "中国")
        supplier.postal_code = request.POST.get("postal_code", "")
        supplier.tax_number = request.POST.get("tax_number", "")
        supplier.registration_number = request.POST.get("registration_number", "")
        supplier.legal_representative = request.POST.get("legal_representative", "")
        supplier.payment_terms = request.POST.get("payment_terms", "")
        supplier.currency = request.POST.get("currency", "CNY")
        supplier.bank_name = request.POST.get("bank_name", "")
        supplier.bank_account = request.POST.get("bank_account", "")
        supplier.buyer_id = request.POST.get("buyer") or None
        supplier.lead_time = request.POST.get("lead_time", 0)
        supplier.min_order_amount = request.POST.get("min_order_amount", 0)
        supplier.quality_rating = request.POST.get("quality_rating", 0)
        supplier.delivery_rating = request.POST.get("delivery_rating", 0)
        supplier.service_rating = request.POST.get("service_rating", 0)
        supplier.certifications = request.POST.get("certifications", "")
        supplier.is_active = request.POST.get("is_active") == "on"
        supplier.is_approved = request.POST.get("is_approved") == "on"
        supplier.notes = request.POST.get("notes", "")
        supplier.updated_by = request.user

        try:
            supplier.save()
            messages.success(request, f"供应商 {supplier.name} 更新成功！")
            return redirect("suppliers:supplier_detail", pk=supplier.pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET request
    from django.contrib.auth import get_user_model

    User = get_user_model()

    categories = SupplierCategory.objects.filter(is_active=True)
    buyers = User.objects.filter(is_active=True)

    context = {
        "supplier": supplier,
        "categories": categories,
        "buyers": buyers,
        "action": "update",
    }
    return render(request, "modules/suppliers/supplier_form.html", context)


@login_required
def supplier_delete(request, pk):
    """
    Delete (soft delete) a supplier.
    Also soft deletes all related purchase orders.
    """
    supplier = get_object_or_404(Supplier, pk=pk, is_deleted=False)

    if request.method == "POST":
        from django.db import transaction
        from django.utils import timezone

        with transaction.atomic():
            # Soft delete the supplier
            supplier.is_deleted = True
            supplier.deleted_at = timezone.now()
            supplier.deleted_by = request.user
            supplier.save()

            # Soft delete all related purchase orders
            orders = supplier.purchase_orders.filter(is_deleted=False)
            orders_count = orders.count()
            for order in orders:
                order.is_deleted = True
                order.deleted_at = timezone.now()
                order.deleted_by = request.user
                order.save()

        # Build success message
        msg = f"供应商 {supplier.name} 已删除"
        if orders_count > 0:
            msg += f"，同时删除了相关的{orders_count}个采购订单"

        messages.success(request, msg)
        return redirect("suppliers:supplier_list")

    # Count related records for confirmation page
    orders_count = supplier.purchase_orders.filter(is_deleted=False).count()

    context = {
        "supplier": supplier,
        "orders_count": orders_count,
    }
    return render(request, "modules/suppliers/supplier_confirm_delete.html", context)


# ============================================================================
# Supplier Contact Views
# ============================================================================


@login_required
@transaction.atomic
def contact_create(request):
    """
    Create a new supplier contact.
    """
    if request.method == "POST":
        supplier_id = request.POST.get("supplier")
        supplier = get_object_or_404(Supplier, pk=supplier_id, is_deleted=False)

        # Check if setting as primary contact
        is_primary = request.POST.get("is_primary") == "on"

        # If setting as primary, unset other primary contacts
        if is_primary:
            SupplierContact.objects.filter(
                supplier=supplier, is_deleted=False, is_primary=True
            ).update(is_primary=False)

        # Create new contact
        contact = SupplierContact.objects.create(
            supplier=supplier,
            name=request.POST.get("name"),
            position=request.POST.get("position", ""),
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
            is_primary=is_primary,
            is_active=True,
            created_by=request.user,
            updated_by=request.user,
        )

        messages.success(request, f"联系人 {contact.name} 已创建")

        # Check if should return to supplier detail page
        if request.POST.get("from_supplier_detail"):
            return redirect("suppliers:supplier_detail", pk=supplier_id)

        return redirect("suppliers:contact_list")

    # GET request - show create form
    suppliers = Supplier.objects.filter(is_deleted=False, is_approved=True)
    context = {
        "suppliers": suppliers,
    }
    return render(request, "modules/suppliers/contact_form.html", context)


@login_required
def contact_update(request, pk):
    """
    Update an existing supplier contact.
    """
    contact = get_object_or_404(SupplierContact, pk=pk, is_deleted=False)

    if request.method == "POST":
        # Check if setting as primary contact
        is_primary = request.POST.get("is_primary") == "on"

        # If setting as primary and not already primary, unset other primary contacts
        if is_primary and not contact.is_primary:
            SupplierContact.objects.filter(
                supplier=contact.supplier, is_deleted=False, is_primary=True
            ).update(is_primary=False)

        # Update contact
        contact.name = request.POST.get("name")
        contact.position = request.POST.get("position", "")
        contact.phone = request.POST.get("phone", "")
        contact.email = request.POST.get("email", "")
        contact.is_primary = is_primary
        contact.is_active = request.POST.get("is_active") == "on"
        contact.updated_by = request.user
        contact.save()

        messages.success(request, f"联系人 {contact.name} 已更新")
        return redirect("suppliers:supplier_detail", pk=contact.supplier.pk)

    # GET request - show update form
    context = {
        "contact": contact,
    }
    return render(request, "modules/suppliers/contact_form.html", context)


@login_required
def contact_delete(request, pk):
    """
    Delete (soft delete) a supplier contact.
    """
    contact = get_object_or_404(SupplierContact, pk=pk, is_deleted=False)

    if request.method == "POST":
        supplier_id = contact.supplier.pk
        contact_name = contact.name

        contact.is_deleted = True
        contact.deleted_by = request.user
        contact.deleted_at = timezone.now()
        contact.save()

        messages.success(request, f"联系人 {contact_name} 已删除")
        return redirect("suppliers:supplier_detail", pk=supplier_id)

    context = {
        "contact": contact,
    }
    return render(request, "modules/suppliers/contact_confirm_delete.html", context)


@login_required
def contact_list(request):
    """
    List all supplier contacts.
    """
    contacts = (
        SupplierContact.objects.filter(is_deleted=False)
        .select_related("supplier")
        .order_by("supplier__name", "-is_primary", "name")
    )

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query)
            | Q(supplier__name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(contacts, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
    }
    return render(request, "modules/suppliers/contact_list.html", context)
