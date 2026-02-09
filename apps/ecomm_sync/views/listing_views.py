"""
Listing管理视图
"""
from core.models import Platform
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from ..models import PlatformAccount, ProductListing


@login_required
def listing_list(request):
    """Listing列表页面"""
    listings = ProductListing.objects.select_related("product", "platform", "account").all()

    # 筛选逻辑
    platform_id = request.GET.get("platform")
    if platform_id:
        listings = listings.filter(platform_id=platform_id)

    account_id = request.GET.get("account")
    if account_id:
        listings = listings.filter(account_id=account_id)

    listing_status = request.GET.get("listing_status")
    if listing_status:
        listings = listings.filter(listing_status=listing_status)

    # 搜索逻辑
    search = request.GET.get("search", "")
    if search:
        listings = listings.filter(
            Q(product__code__icontains=search)
            | Q(product__name__icontains=search)
            | Q(platform_sku__icontains=search)
        )

    # 排序
    listings = listings.order_by("-last_synced_at")

    # 分页
    paginator = Paginator(listings, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "platforms": Platform.objects.filter(is_active=True),
        "accounts": PlatformAccount.objects.filter(is_active=True),
        "listing_status_choices": ProductListing.LISTING_STATUS_CHOICES,
    }
    return render(request, "modules/ecomm_sync/listing_list.html", context)
