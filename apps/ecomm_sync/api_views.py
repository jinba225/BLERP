"""
Listing同步AJAX视图（轻量级实现）
不使用DRF，直接使用Django原生能力
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json

from .models import ProductListing, PlatformAccount, EcommProduct, SyncLog
from core.models import Platform
from .services.listing_sync import ListingService


@login_required
@require_http_methods(["GET"])
def product_listings_fragment(request, product_id):
    """
    获取产品的所有Listing（JSON）
    用于前端刷新Listing列表
    """
    try:
        listings = ProductListing.objects.filter(product_id=product_id).select_related(
            "platform", "account"
        )

        data = [
            {
                "id": l.id,
                "platform_name": l.platform.name,
                "listing_title": l.listing_title,
                "listing_status": l.listing_status,
                "listing_status_display": l.get_listing_status_display(),
                "price": str(l.price),
                "quantity": l.quantity,
                "platform_sku": l.platform_sku,
                "product_name": l.product.name if l.product else "",
                "last_synced_at": l.last_synced_at.strftime("%Y-%m-%d %H:%M:%S")
                if l.last_synced_at
                else None,
                "sync_enabled": l.sync_enabled,
                "sync_error": l.sync_error,
            }
            for l in listings
        ]

        return JsonResponse({"listings": data}, safe=False)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def platforms_list(request):
    """
    获取可用的平台列表（JSON）
    """
    try:
        platforms = Platform.objects.filter(is_active=True)
        data = [
            {
                "id": p.id,
                "name": p.name,
                "platform_type": p.platform_type,
                "platform_type_display": p.get_platform_type_display(),
            }
            for p in platforms
        ]

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def publish_listing(request):
    """
    发布Listing（创建Listing记录）
    """
    try:
        from products.models import Product

        product_id = request.POST.get("product_id")
        platform_id = request.POST.get("platform_id")

        if not product_id or not platform_id:
            return JsonResponse({"success": False, "message": "参数不完整"})

        product = Product.objects.get(id=product_id)
        platform = Platform.objects.get(id=platform_id)

        # 查找该平台的启用账号
        account = PlatformAccount.objects.filter(platform=platform, is_active=True).first()

        if not account:
            return JsonResponse({"success": False, "message": "该平台未配置启用账号"})

        # 调用ListingService发布Listing（创建到平台）
        service = ListingService()
        result = service.publish_listing(product, [platform_id])

        if result["success"] > 0:
            return JsonResponse({"success": True, "message": f'成功发布{result["success"]}个Listing'})
        else:
            return JsonResponse({"success": False, "message": "发布失败：" + str(result["errors"])})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def sync_listing(request, listing_id):
    """
    同步单个Listing（价格+库存）
    """
    try:
        service = ListingService()

        # 获取Listing
        listing = ProductListing.objects.get(id=listing_id)
        product = listing.product

        # 同步价格
        if listing.auto_update_price:
            service.update_listing_price(listing_id, product.selling_price)

        # 同步库存
        if listing.auto_update_stock:
            from inventory.models import ProductStock

            stock = ProductStock.objects.filter(product=product).first()
            if stock:
                service.update_listing_stock(listing_id, stock.qty_in_stock)

        return JsonResponse({"success": True, "message": "同步成功"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def batch_sync_listings(request):
    """
    批量同步Listings
    """
    try:
        listing_ids = json.loads(request.body).get("listing_ids", [])

        if not listing_ids:
            return JsonResponse({"success": False, "message": "请选择要同步的Listing"})

        service = ListingService()
        results = {"total": len(listing_ids), "success": 0, "failed": 0, "errors": []}

        for listing_id in listing_ids:
            try:
                listing = ProductListing.objects.get(id=listing_id)

                # 同步价格
                if listing.auto_update_price:
                    service.update_listing_price(listing_id, listing.product.selling_price)

                # 同步库存
                if listing.auto_update_stock:
                    from inventory.models import ProductStock

                    stock = ProductStock.objects.filter(product=listing.product).first()
                    if stock:
                        service.update_listing_stock(listing_id, stock.qty_in_stock)

                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"listing_id": listing_id, "error": str(e)})

        return JsonResponse(results)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def listings_list(request):
    """
    Listing列表API（支持筛选和搜索）
    """
    try:
        listings = ProductListing.objects.select_related("product", "platform", "account")

        # 筛选
        platform_id = request.GET.get("platform")
        if platform_id:
            listings = listings.filter(platform_id=platform_id)

        account_id = request.GET.get("account")
        if account_id:
            listings = listings.filter(account_id=account_id)

        listing_status = request.GET.get("listing_status")
        if listing_status:
            listings = listings.filter(listing_status=listing_status)

        # 搜索
        search = request.GET.get("search", "")
        if search:
            from django.db.models import Q

            listings = listings.filter(
                Q(product__code__icontains=search)
                | Q(product__name__icontains=search)
                | Q(platform_sku__icontains=search)
            )

        # 分页
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        paginator = Paginator(listings, page_size)
        page_obj = paginator.get_page(page)

        data = [
            {
                "id": l.id,
                "product_id": l.product.id,
                "product_code": l.product.code,
                "product_name": l.product.name,
                "platform_id": l.platform.id,
                "platform_name": l.platform.name,
                "account_id": l.account.id if l.account else None,
                "account_name": l.account.account_name if l.account else "",
                "listing_title": l.listing_title,
                "listing_status": l.listing_status,
                "listing_status_display": l.get_listing_status_display(),
                "platform_sku": l.platform_sku,
                "platform_product_id": l.platform_product_id,
                "price": str(l.price),
                "quantity": l.quantity,
                "sync_enabled": l.sync_enabled,
                "last_synced_at": l.last_synced_at.strftime("%Y-%m-%d %H:%M:%S")
                if l.last_synced_at
                else None,
            }
            for l in page_obj
        ]

        return JsonResponse(
            {
                "listings": data,
                "total": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
