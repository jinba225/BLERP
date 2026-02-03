"""
Product views for the ERP system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Product, ProductCategory, Brand, Unit


@login_required
def product_list(request):
    """
    List all products with search and filter capabilities.
    """
    products = Product.objects.filter(is_deleted=False).select_related('category', 'brand', 'unit').prefetch_related('listings')

    # Search
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(barcode__icontains=search) |
            Q(model__icontains=search)
        )

    # Filter by type
    product_type = request.GET.get('product_type', '')
    if product_type:
        products = products.filter(product_type=product_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        products = products.filter(status=status)

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category_id=category)

    # Filter by brand
    brand = request.GET.get('brand', '')
    if brand:
        products = products.filter(brand_id=brand)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    products = products.order_by(sort)

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all categories and brands for filter
    categories = ProductCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'product_type': product_type,
        'status': status,
        'category': category,
        'brand': brand,
        'categories': categories,
        'brands': brands,
        'total_count': paginator.count,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    """
    Display product details.
    """
    product = get_object_or_404(
        Product.objects.filter(is_deleted=False).select_related(
            'category', 'brand', 'unit'
        ).prefetch_related('images'),
        pk=pk
    )

    context = {
        'product': product,
        'images': product.images.all(),
    }
    return render(request, 'products/product_detail.html', context)


@login_required
@transaction.atomic
def product_create(request):
    """
    Create a new product.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'code': request.POST.get('code'),
            'barcode': request.POST.get('barcode') or None,
            'category_id': request.POST.get('category') or None,
            'brand_id': request.POST.get('brand') or None,
            'product_type': request.POST.get('product_type', 'finished'),
            'status': request.POST.get('status', 'active'),
            'description': request.POST.get('description', ''),
            'specifications': request.POST.get('specifications', ''),
            'model': request.POST.get('model', ''),
            'unit_id': request.POST.get('unit') or None,
            'weight': request.POST.get('weight') or None,
            'length': request.POST.get('length') or None,
            'width': request.POST.get('width') or None,
            'height': request.POST.get('height') or None,
            'cost_price': request.POST.get('cost_price', 0),
            'selling_price': request.POST.get('selling_price', 0),
            'track_inventory': request.POST.get('track_inventory') == 'on',
            'min_stock': request.POST.get('min_stock', 0),
            'max_stock': request.POST.get('max_stock', 0),
            'reorder_point': request.POST.get('reorder_point', 0),
            'warranty_period': request.POST.get('warranty_period', 0),
            'shelf_life': request.POST.get('shelf_life') or None,
            'notes': request.POST.get('notes', ''),
        }

        try:
            product = Product(**data)
            product.created_by = request.user
            product.save()

            messages.success(request, f'产品 {product.name} 创建成功！')
            return redirect('products:product_detail', pk=product.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request
    categories = ProductCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    units = Unit.objects.filter(is_active=True)

    context = {
        'categories': categories,
        'brands': brands,
        'units': units,
        'action': 'create',
    }
    return render(request, 'products/product_form.html', context)


@login_required
@transaction.atomic
def product_update(request, pk):
    """
    Update an existing product.
    """
    product = get_object_or_404(Product, pk=pk, is_deleted=False)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.barcode = request.POST.get('barcode') or None
        product.category_id = request.POST.get('category') or None
        product.brand_id = request.POST.get('brand') or None
        product.product_type = request.POST.get('product_type', 'finished')
        product.status = request.POST.get('status', 'active')
        product.description = request.POST.get('description', '')
        product.specifications = request.POST.get('specifications', '')
        product.model = request.POST.get('model', '')
        product.unit_id = request.POST.get('unit') or None
        product.weight = request.POST.get('weight') or None
        product.length = request.POST.get('length') or None
        product.width = request.POST.get('width') or None
        product.height = request.POST.get('height') or None
        product.cost_price = request.POST.get('cost_price', 0)
        product.selling_price = request.POST.get('selling_price', 0)
        product.track_inventory = request.POST.get('track_inventory') == 'on'
        product.min_stock = request.POST.get('min_stock', 0)
        product.max_stock = request.POST.get('max_stock', 0)
        product.reorder_point = request.POST.get('reorder_point', 0)
        product.warranty_period = request.POST.get('warranty_period', 0)
        product.shelf_life = request.POST.get('shelf_life') or None
        product.notes = request.POST.get('notes', '')
        product.updated_by = request.user

        try:
            product.save()
            messages.success(request, f'产品 {product.name} 更新成功！')
            return redirect('products:product_detail', pk=product.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request
    categories = ProductCategory.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    units = Unit.objects.filter(is_active=True)

    context = {
        'product': product,
        'categories': categories,
        'brands': brands,
        'units': units,
        'action': 'update',
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """
    Delete (soft delete) a product.
    """
    product = get_object_or_404(Product, pk=pk, is_deleted=False)

    if request.method == 'POST':
        from django.utils import timezone
        product.is_deleted = True
        product.deleted_at = timezone.now()
        product.deleted_by = request.user
        product.save()

        messages.success(request, f'产品 {product.name} 已删除')
        return redirect('products:product_list')

    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)


# ============================================
# Unit Management Views (计量单位管理)
# ============================================

@login_required
def unit_list(request):
    """
    List all units with search and filter capabilities.
    """
    units = Unit.objects.filter(is_deleted=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        units = units.filter(
            Q(name__icontains=search) |
            Q(symbol__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by type
    unit_type = request.GET.get('unit_type', '')
    if unit_type:
        units = units.filter(unit_type=unit_type)

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        units = units.filter(is_active=is_active == 'true')

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    units = units.order_by(sort)

    # Pagination
    paginator = Paginator(units, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'unit_type': unit_type,
        'is_active': is_active,
        'total_count': paginator.count,
        'unit_types': Unit.UNIT_TYPES,
    }
    return render(request, 'products/unit_list.html', context)


@login_required
def unit_detail(request, pk):
    """
    Display unit details.
    """
    unit = get_object_or_404(Unit, pk=pk, is_deleted=False)

    # Get products using this unit
    products = Product.objects.filter(unit=unit, is_deleted=False)[:10]

    context = {
        'unit': unit,
        'products': products,
        'product_count': Product.objects.filter(unit=unit, is_deleted=False).count(),
    }
    return render(request, 'products/unit_detail.html', context)


@login_required
@transaction.atomic
def unit_create(request):
    """
    Create a new unit.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'symbol': request.POST.get('symbol'),
            'unit_type': request.POST.get('unit_type', 'basic'),
            'description': request.POST.get('description', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }

        try:
            unit = Unit(**data)
            unit.created_by = request.user
            unit.save()

            messages.success(request, f'计量单位 {unit.name} 创建成功！')
            return redirect('products:unit_detail', pk=unit.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    context = {
        'action': 'create',
        'unit_types': Unit.UNIT_TYPES,
    }
    return render(request, 'products/unit_form.html', context)


@login_required
@transaction.atomic
def unit_update(request, pk):
    """
    Update an existing unit.
    """
    unit = get_object_or_404(Unit, pk=pk, is_deleted=False)

    if request.method == 'POST':
        unit.name = request.POST.get('name')
        unit.symbol = request.POST.get('symbol')
        unit.unit_type = request.POST.get('unit_type', 'basic')
        unit.description = request.POST.get('description', '')
        unit.is_active = request.POST.get('is_active') == 'on'
        unit.updated_by = request.user

        try:
            unit.save()
            messages.success(request, f'计量单位 {unit.name} 更新成功！')
            return redirect('products:unit_detail', pk=unit.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    context = {
        'unit': unit,
        'action': 'update',
        'unit_types': Unit.UNIT_TYPES,
    }
    return render(request, 'products/unit_form.html', context)


@login_required
def unit_delete(request, pk):
    """
    Delete (soft delete) a unit.
    """
    unit = get_object_or_404(Unit, pk=pk, is_deleted=False)

    # Check if unit is being used
    product_count = Product.objects.filter(unit=unit, is_deleted=False).count()
    if product_count > 0:
        messages.error(request, f'无法删除：该单位正在被 {product_count} 个产品使用')
        return redirect('products:unit_detail', pk=unit.pk)

    if request.method == 'POST':
        unit.is_deleted = True
        unit.deleted_at = timezone.now()
        unit.deleted_by = request.user
        unit.save()

        messages.success(request, f'计量单位 {unit.name} 已删除')
        return redirect('products:unit_list')

    context = {
        'unit': unit,
    }
    return render(request, 'products/unit_confirm_delete.html', context)


@login_required
def unit_set_default(request, pk):
    """
    Set a unit as the default unit.
    Only one unit can be default at a time.
    """
    unit = get_object_or_404(Unit, pk=pk, is_deleted=False)

    # 取消其他单位的默认状态
    Unit.objects.filter(is_default=True).update(is_default=False)

    # 设置当前单位为默认
    unit.is_default = True
    unit.save(update_fields=['is_default'])

    messages.success(request, f'已将 {unit.name}({unit.symbol}) 设为默认单位')
    return redirect('products:unit_list')


# ============================================
# Brand Management Views (品牌管理)
# ============================================

@login_required
def brand_list(request):
    """
    List all brands with search and filter capabilities.
    """
    brands = Brand.objects.filter(is_deleted=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        brands = brands.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search) |
            Q(country__icontains=search)
        )

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        brands = brands.filter(is_active=is_active == 'true')

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    brands = brands.order_by(sort)

    # Pagination
    paginator = Paginator(brands, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'is_active': is_active,
        'total_count': paginator.count,
    }
    return render(request, 'products/brand_list.html', context)


@login_required
def brand_detail(request, pk):
    """
    Display brand details.
    """
    brand = get_object_or_404(Brand, pk=pk, is_deleted=False)

    # Get products of this brand
    products = Product.objects.filter(brand=brand, is_deleted=False)[:10]

    context = {
        'brand': brand,
        'products': products,
        'product_count': Product.objects.filter(brand=brand, is_deleted=False).count(),
    }
    return render(request, 'products/brand_detail.html', context)


@login_required
@transaction.atomic
def brand_create(request):
    """
    Create a new brand.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'code': request.POST.get('code'),
            'description': request.POST.get('description', ''),
            'website': request.POST.get('website', ''),
            'country': request.POST.get('country', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }

        try:
            brand = Brand(**data)
            brand.created_by = request.user
            brand.save()

            messages.success(request, f'品牌 {brand.name} 创建成功！')
            return redirect('products:brand_detail', pk=brand.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    context = {
        'action': 'create',
    }
    return render(request, 'products/brand_form.html', context)


@login_required
@transaction.atomic
def brand_update(request, pk):
    """
    Update an existing brand.
    """
    brand = get_object_or_404(Brand, pk=pk, is_deleted=False)

    if request.method == 'POST':
        brand.name = request.POST.get('name')
        brand.code = request.POST.get('code')
        brand.description = request.POST.get('description', '')
        brand.website = request.POST.get('website', '')
        brand.country = request.POST.get('country', '')
        brand.is_active = request.POST.get('is_active') == 'on'
        brand.updated_by = request.user

        try:
            brand.save()
            messages.success(request, f'品牌 {brand.name} 更新成功！')
            return redirect('products:brand_detail', pk=brand.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    context = {
        'brand': brand,
        'action': 'update',
    }
    return render(request, 'products/brand_form.html', context)


@login_required
def brand_delete(request, pk):
    """
    Delete (soft delete) a brand.
    """
    brand = get_object_or_404(Brand, pk=pk, is_deleted=False)

    # Check if brand is being used
    product_count = Product.objects.filter(brand=brand, is_deleted=False).count()
    if product_count > 0:
        messages.error(request, f'无法删除：该品牌正在被 {product_count} 个产品使用')
        return redirect('products:brand_detail', pk=brand.pk)

    if request.method == 'POST':
        brand.is_deleted = True
        brand.deleted_at = timezone.now()
        brand.deleted_by = request.user
        brand.save()

        messages.success(request, f'品牌 {brand.name} 已删除')
        return redirect('products:brand_list')

    context = {
        'brand': brand,
    }
    return render(request, 'products/brand_confirm_delete.html', context)


# ============================================
# ProductCategory Management Views (产品分类管理)
# ============================================

@login_required
def category_list(request):
    """
    List all categories in a tree structure.
    """
    categories = ProductCategory.objects.filter(is_deleted=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        categories = categories.filter(is_active=is_active == 'true')

    context = {
        'categories': categories,
        'search': search,
        'is_active': is_active,
    }
    return render(request, 'products/category_list.html', context)


@login_required
def category_detail(request, pk):
    """
    Display category details.
    """
    category = get_object_or_404(ProductCategory, pk=pk, is_deleted=False)

    # Get products in this category
    products = Product.objects.filter(category=category, is_deleted=False)[:10]

    # Get child categories
    children = category.get_children().filter(is_deleted=False)

    context = {
        'category': category,
        'products': products,
        'product_count': Product.objects.filter(category=category, is_deleted=False).count(),
        'children': children,
    }
    return render(request, 'products/category_detail.html', context)


@login_required
@transaction.atomic
def category_create(request):
    """
    Create a new category.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'code': request.POST.get('code'),
            'description': request.POST.get('description', ''),
            'sort_order': request.POST.get('sort_order', 0),
            'is_active': request.POST.get('is_active') == 'on',
        }

        parent_id = request.POST.get('parent')
        if parent_id:
            data['parent_id'] = parent_id

        try:
            category = ProductCategory(**data)
            category.created_by = request.user
            category.save()

            messages.success(request, f'产品分类 {category.name} 创建成功！')
            return redirect('products:category_detail', pk=category.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request
    all_categories = ProductCategory.objects.filter(is_active=True, is_deleted=False)

    context = {
        'action': 'create',
        'all_categories': all_categories,
    }
    return render(request, 'products/category_form.html', context)


@login_required
@transaction.atomic
def category_update(request, pk):
    """
    Update an existing category.
    """
    category = get_object_or_404(ProductCategory, pk=pk, is_deleted=False)

    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.code = request.POST.get('code')
        category.description = request.POST.get('description', '')
        category.sort_order = request.POST.get('sort_order', 0)
        category.is_active = request.POST.get('is_active') == 'on'

        parent_id = request.POST.get('parent')
        if parent_id and int(parent_id) != category.pk:
            category.parent_id = parent_id
        else:
            category.parent = None

        category.updated_by = request.user

        try:
            category.save()
            messages.success(request, f'产品分类 {category.name} 更新成功！')
            return redirect('products:category_detail', pk=category.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request
    all_categories = ProductCategory.objects.filter(
        is_active=True,
        is_deleted=False
    ).exclude(pk=category.pk)

    context = {
        'category': category,
        'action': 'update',
        'all_categories': all_categories,
    }
    return render(request, 'products/category_form.html', context)


@login_required
def category_delete(request, pk):
    """
    Delete (soft delete) a category.
    """
    category = get_object_or_404(ProductCategory, pk=pk, is_deleted=False)

    # Get children and product count
    children = category.get_children().filter(is_deleted=False)
    has_children = children.exists()
    children_count = children.count()
    product_count = Product.objects.filter(category=category, is_deleted=False).count()

    if request.method == 'POST':
        # Check if category has children
        if has_children:
            messages.error(request, '无法删除：该分类下还有子分类')
            return redirect('products:category_detail', pk=category.pk)

        # Check if category is being used
        if product_count > 0:
            messages.error(request, f'无法删除：该分类正在被 {product_count} 个产品使用')
            return redirect('products:category_detail', pk=category.pk)

        category.is_deleted = True
        category.deleted_at = timezone.now()
        category.deleted_by = request.user
        category.save()

        messages.success(request, f'产品分类 {category.name} 已删除')
        return redirect('products:category_list')

    context = {
        'category': category,
        'has_children': has_children,
        'children_count': children_count,
        'product_count': product_count,
    }
    return render(request, 'products/category_confirm_delete.html', context)
