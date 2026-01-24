"""
Customer views for the ERP system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Customer, CustomerCategory, CustomerContact, CustomerAddress
from apps.core.utils.code_generator import CodeGenerator
from apps.core.choice_helpers import get_customer_context


@login_required
def customer_list(request):
    """
    List all customers with search and filter capabilities.
    """
    customers = Customer.objects.filter(is_deleted=False).select_related('category', 'sales_rep')

    # Search
    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(contact_person__icontains=search) |
            Q(phone__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        customers = customers.filter(status=status)

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        customers = customers.filter(category_id=category)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    customers = customers.order_by(sort)

    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter
    categories = CustomerCategory.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'category': category,
        'categories': categories,
        'total_count': paginator.count,
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_detail(request, pk):
    """
    Display customer details.
    """
    customer = get_object_or_404(
        Customer.objects.filter(is_deleted=False).select_related(
            'category', 'sales_rep'
        ).prefetch_related('contacts', 'addresses'),
        pk=pk
    )

    context = {
        'customer': customer,
        'contacts': customer.contacts.filter(is_deleted=False),
        'addresses': customer.addresses.filter(is_deleted=False),
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
@transaction.atomic
def customer_create(request):
    """
    Create a new customer.
    """
    if request.method == 'POST':
        try:
            # Debug: Print all POST data
            print("=" * 80)
            print("DEBUG: POST data received:")
            for key, value in request.POST.items():
                print(f"  {key}: {value}")
            print("=" * 80)
            
            # Generate customer code automatically
            customer_code = CodeGenerator.generate_customer_code()
            
            # Extract form data
            data = {
                'name': request.POST.get('name'),
                'code': customer_code,  # Use auto-generated code
                'customer_level': request.POST.get('customer_level', 'C'),
                'status': request.POST.get('status', 'active'),
                'category_id': request.POST.get('category') or None,
                'website': request.POST.get('website', ''),
                'address': request.POST.get('address', ''),
                'city': request.POST.get('city', ''),
                'province': request.POST.get('province', ''),
                'country': request.POST.get('country', '中国'),
                'postal_code': request.POST.get('postal_code', ''),
                'industry': request.POST.get('industry', ''),
                'business_license': request.POST.get('business_license', ''),
                'tax_number': request.POST.get('tax_number', ''),
                'bank_name': request.POST.get('bank_name', ''),
                'bank_account': request.POST.get('bank_account', ''),
                'sales_rep_id': request.POST.get('sales_rep') or None,
                'credit_limit': request.POST.get('credit_limit', 0),
                'payment_terms': request.POST.get('payment_terms', ''),
                'discount_rate': request.POST.get('discount_rate', 0),
                'source': request.POST.get('source', ''),
                'tags': request.POST.get('tags', ''),
                'notes': request.POST.get('notes', ''),
            }

            customer = Customer(**data)
            customer.created_by = request.user
            customer.save()

            # Process multiple contacts
            contacts_data = []
            for key in request.POST:
                if key.startswith('contacts[') and '[name]' in key:
                    # Extract index from key like 'contacts[0][name]'
                    import re
                    match = re.match(r'contacts\[(\d+)\]', key)
                    if match:
                        index = match.group(1)
                        name = request.POST.get(f'contacts[{index}][name]', '').strip()
                        if name:  # Only add if name is provided
                            contacts_data.append({
                                'name': name,
                                'position': request.POST.get(f'contacts[{index}][position]', ''),
                                'department': request.POST.get(f'contacts[{index}][department]', ''),
                                'phone': request.POST.get(f'contacts[{index}][phone]', ''),
                                'mobile': request.POST.get(f'contacts[{index}][mobile]', ''),
                                'email': request.POST.get(f'contacts[{index}][email]', ''),
                                'notes': request.POST.get(f'contacts[{index}][notes]', ''),
                            })

            print(f"DEBUG: Found {len(contacts_data)} contacts to create")

            # Create contacts
            for i, contact_data in enumerate(contacts_data):
                print(f"DEBUG: Creating contact {i+1}: {contact_data['name']}")
                CustomerContact.objects.create(
                    customer=customer,
                    name=contact_data['name'],
                    position=contact_data['position'],
                    department=contact_data['department'],
                    phone=contact_data['phone'],
                    mobile=contact_data['mobile'],
                    email=contact_data['email'],
                    notes=contact_data['notes'],
                    created_by=request.user
                )
                print(f"DEBUG: Contact {i+1} created successfully")

            messages.success(request, f'客户 {customer.name} 创建成功！客户编码：{customer_code}')
            return redirect('customers:customer_detail', pk=customer.pk)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error creating customer: {error_details}")  # Print to console for debugging
            messages.error(request, f'创建失败：{str(e)}')
            messages.error(request, f'错误详情：{error_details[:500]}...')  # Show first 500 chars in UI

    # GET request
    from django.contrib.auth import get_user_model
    User = get_user_model()

    categories = CustomerCategory.objects.filter(is_active=True)
    sales_reps = User.objects.filter(is_active=True)

    # 获取动态选项
    choice_context = get_customer_context()

    context = {
        'categories': categories,
        'sales_reps': sales_reps,
        'action': 'create',
    }
    # 合并动态选项到context
    context.update(choice_context)

    return render(request, 'customers/customer_form.html', context)


@login_required
@transaction.atomic
def customer_update(request, pk):
    """
    Update an existing customer.
    """
    customer = get_object_or_404(Customer, pk=pk, is_deleted=False)

    if request.method == 'POST':
        # Update fields
        customer.name = request.POST.get('name')
        customer.customer_level = request.POST.get('customer_level', 'C')
        customer.status = request.POST.get('status', 'active')
        customer.category_id = request.POST.get('category') or None
        customer.website = request.POST.get('website', '')
        customer.address = request.POST.get('address', '')
        customer.city = request.POST.get('city', '')
        customer.province = request.POST.get('province', '')
        customer.country = request.POST.get('country', '中国')
        customer.postal_code = request.POST.get('postal_code', '')
        customer.industry = request.POST.get('industry', '')
        customer.business_license = request.POST.get('business_license', '')
        customer.tax_number = request.POST.get('tax_number', '')
        customer.bank_name = request.POST.get('bank_name', '')
        customer.bank_account = request.POST.get('bank_account', '')
        customer.sales_rep_id = request.POST.get('sales_rep') or None
        customer.credit_limit = request.POST.get('credit_limit', 0)
        customer.payment_terms = request.POST.get('payment_terms', '')
        customer.discount_rate = request.POST.get('discount_rate', 0)
        customer.source = request.POST.get('source', '')
        customer.tags = request.POST.get('tags', '')
        customer.notes = request.POST.get('notes', '')
        customer.updated_by = request.user

        try:
            customer.save()

            contacts_data = []
            import re
            for key in request.POST:
                if key.startswith('contacts[') and '[name]' in key:
                    m = re.match(r'contacts\[(\d+)\]', key)
                    if m:
                        index = m.group(1)
                        name = request.POST.get(f'contacts[{index}][name]', '').strip()
                        if name:
                            contacts_data.append({
                                'name': name,
                                'position': request.POST.get(f'contacts[{index}][position]', ''),
                                'department': request.POST.get(f'contacts[{index}][department]', ''),
                                'phone': request.POST.get(f'contacts[{index}][phone]', ''),
                                'mobile': request.POST.get(f'contacts[{index}][mobile]', ''),
                                'email': request.POST.get(f'contacts[{index}][email]', ''),
                                'notes': request.POST.get(f'contacts[{index}][notes]', ''),
                            })

            for contact_data in contacts_data:
                CustomerContact.objects.create(
                    customer=customer,
                    name=contact_data['name'],
                    position=contact_data['position'],
                    department=contact_data['department'],
                    phone=contact_data['phone'],
                    mobile=contact_data['mobile'],
                    email=contact_data['email'],
                    notes=contact_data['notes'],
                    created_by=request.user
                )

            messages.success(request, f'客户 {customer.name} 更新成功！')
            return redirect('customers:customer_detail', pk=customer.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request
    from django.contrib.auth import get_user_model
    User = get_user_model()

    categories = CustomerCategory.objects.filter(is_active=True)
    sales_reps = User.objects.filter(is_active=True)
    contacts = CustomerContact.objects.filter(customer=customer, is_deleted=False).order_by('created_at')

    # 获取动态选项
    choice_context = get_customer_context()

    context = {
        'customer': customer,
        'categories': categories,
        'sales_reps': sales_reps,
        'contacts': contacts,
        'action': 'update',
    }
    # 合并动态选项到context
    context.update(choice_context)

    return render(request, 'customers/customer_form.html', context)


@login_required
def customer_delete(request, pk):
    """
    Delete (soft delete) a customer.
    Also soft deletes all related quotes and sales orders.
    """
    customer = get_object_or_404(Customer, pk=pk, is_deleted=False)

    if request.method == 'POST':
        from django.utils import timezone
        from django.db import transaction

        with transaction.atomic():
            # Soft delete the customer
            customer.is_deleted = True
            customer.deleted_at = timezone.now()
            customer.deleted_by = request.user
            customer.save()

            # Soft delete all related quotes
            quotes = customer.quotes.filter(is_deleted=False)
            quotes_count = quotes.count()
            for quote in quotes:
                quote.is_deleted = True
                quote.deleted_at = timezone.now()
                quote.deleted_by = request.user
                quote.save()

            # Soft delete all related sales orders
            orders = customer.sales_orders.filter(is_deleted=False)
            orders_count = orders.count()
            for order in orders:
                order.is_deleted = True
                order.deleted_at = timezone.now()
                order.deleted_by = request.user
                order.save()

        # Build success message
        msg = f'客户 {customer.name} 已删除'
        if quotes_count > 0 or orders_count > 0:
            related_items = []
            if quotes_count > 0:
                related_items.append(f'{quotes_count}个报价单')
            if orders_count > 0:
                related_items.append(f'{orders_count}个销售订单')
            msg += f'，同时删除了相关的{" 和 ".join(related_items)}'

        messages.success(request, msg)
        return redirect('customers:customer_list')

    # Count related records for confirmation page
    quotes_count = customer.quotes.filter(is_deleted=False).count()
    orders_count = customer.sales_orders.filter(is_deleted=False).count()

    context = {
        'customer': customer,
        'quotes_count': quotes_count,
        'orders_count': orders_count,
    }
    return render(request, 'customers/customer_confirm_delete.html', context)


# ==================== Contact Management Views ====================

@login_required
def contact_list(request):
    """
    List all customer contacts with search and filter capabilities.
    """
    contacts = CustomerContact.objects.filter(is_deleted=False).select_related('customer')

    # Search
    search = request.GET.get('search', '')
    if search:
        contacts = contacts.filter(
            Q(name__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(phone__icontains=search) |
            Q(mobile__icontains=search) |
            Q(email__icontains=search)
        )

    # Filter by customer
    customer_id = request.GET.get('customer', '')
    if customer_id:
        contacts = contacts.filter(customer_id=customer_id)

    # Filter by primary contact
    is_primary = request.GET.get('is_primary', '')
    if is_primary:
        contacts = contacts.filter(is_primary=(is_primary == 'true'))

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    contacts = contacts.order_by(sort)

    # Pagination
    paginator = Paginator(contacts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all customers for filter
    customers = Customer.objects.filter(is_deleted=False, status='active').order_by('name')

    context = {
        'page_obj': page_obj,
        'search': search,
        'customer_id': customer_id,
        'is_primary': is_primary,
        'customers': customers,
        'total_count': paginator.count,
    }
    return render(request, 'customers/contact_list.html', context)


@login_required
@transaction.atomic
def contact_create(request):
    """
    Create a new customer contact.
    """
    if request.method == 'POST':
        print(f"[DEBUG] POST data: {request.POST}")  # Debug log

        customer_id = request.POST.get('customer')
        if not customer_id:
            messages.error(request, '请选择客户')
            customers = Customer.objects.filter(is_deleted=False, status='active').order_by('name')
            context = {
                'customers': customers,
                'action': 'create',
            }
            return render(request, 'customers/contact_form.html', context)

        try:
            customer = get_object_or_404(Customer, pk=customer_id, is_deleted=False)
        except Exception as e:
            messages.error(request, f'客户不存在：{str(e)}')
            customers = Customer.objects.filter(is_deleted=False, status='active').order_by('name')
            context = {
                'customers': customers,
                'action': 'create',
            }
            return render(request, 'customers/contact_form.html', context)

        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '联系人姓名不能为空')
            customers = Customer.objects.filter(is_deleted=False, status='active').order_by('name')
            context = {
                'customers': customers,
                'action': 'create',
            }
            return render(request, 'customers/contact_form.html', context)

        try:
            # If this is set as primary, unset other primary contacts for this customer
            is_primary = request.POST.get('is_primary') == 'on'
            if is_primary:
                CustomerContact.objects.filter(
                    customer=customer,
                    is_primary=True,
                    is_deleted=False
                ).update(is_primary=False)

            # Create contact - only use fields that exist in the model
            contact = CustomerContact(
                customer=customer,
                name=name,
                position=request.POST.get('position', ''),
                department=request.POST.get('department', ''),
                phone=request.POST.get('phone', ''),
                mobile=request.POST.get('mobile', ''),
                email=request.POST.get('email', ''),
                is_primary=is_primary,
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            contact.save()

            print(f"[DEBUG] Contact created: {contact.id} - {contact.name}")  # Debug log

            messages.success(request, f'联系人 {contact.name} 创建成功！')
            # Return to customer detail page if from_customer_detail parameter is present
            if request.POST.get('from_customer_detail') or request.META.get('HTTP_REFERER', '').endswith(f'/customers/{customer.pk}/'):
                return redirect('customers:customer_detail', pk=customer.pk)
            return redirect('customers:contact_list')
        except Exception as e:
            print(f"[ERROR] Failed to create contact: {str(e)}")  # Debug log
            import traceback
            traceback.print_exc()
            messages.error(request, f'创建失败：{str(e)}')

    # GET request
    customers = Customer.objects.filter(is_deleted=False, status='active').order_by('name')

    context = {
        'customers': customers,
        'action': 'create',
    }
    return render(request, 'customers/contact_form.html', context)


@login_required
@transaction.atomic
def contact_update(request, pk):
    """
    Update an existing customer contact.
    """
    contact = get_object_or_404(CustomerContact, pk=pk, is_deleted=False)

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = get_object_or_404(Customer, pk=customer_id, is_deleted=False)

        # Update fields - only use fields that exist in the model
        contact.customer = customer
        contact.name = request.POST.get('name')
        contact.position = request.POST.get('position', '')
        contact.department = request.POST.get('department', '')
        contact.phone = request.POST.get('phone', '')
        contact.mobile = request.POST.get('mobile', '')
        contact.email = request.POST.get('email', '')
        is_primary = request.POST.get('is_primary') == 'on'
        contact.notes = request.POST.get('notes', '')
        contact.updated_by = request.user

        try:
            # If this is set as primary, unset other primary contacts for this customer
            if is_primary and not contact.is_primary:
                CustomerContact.objects.filter(
                    customer=customer,
                    is_primary=True,
                    is_deleted=False
                ).exclude(pk=contact.pk).update(is_primary=False)

            contact.is_primary = is_primary
            contact.save()

            messages.success(request, f'联系人 {contact.name} 更新成功！')
            return redirect('customers:contact_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request
    customers = Customer.objects.filter(is_deleted=False).order_by('name')

    context = {
        'contact': contact,
        'customers': customers,
        'action': 'update',
    }
    return render(request, 'customers/contact_form.html', context)


@login_required
def contact_delete(request, pk):
    """
    Delete (soft delete) a customer contact.
    """
    contact = get_object_or_404(CustomerContact, pk=pk, is_deleted=False)

    if request.method == 'POST':
        from django.utils import timezone
        contact.is_deleted = True
        contact.deleted_at = timezone.now()
        contact.deleted_by = request.user
        contact.save()

        messages.success(request, f'联系人 {contact.name} 已删除')
        return redirect('customers:contact_list')

    context = {
        'contact': contact,
    }
    return render(request, 'customers/contact_confirm_delete.html', context)


@login_required
def api_get_customer_contacts(request, customer_id):
    """
    API endpoint to get contacts for a customer.
    Returns JSON response with contacts data.
    """
    from django.http import JsonResponse
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, is_deleted=False)
        contacts = customer.contacts.filter(is_deleted=False).values(
            'id', 'name', 'position', 'department', 'phone', 'mobile', 'email', 'notes'
        ).order_by('name')
        
        return JsonResponse({
            'success': True,
            'contacts': list(contacts)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

