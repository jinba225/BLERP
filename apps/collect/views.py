"""
视图模块
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

# ---------------------- 页面视图 ----------------------


@login_required
def collect_manage(request):
    """采集任务管理主页面"""
    from core.models import Platform, Shop

    from .models import CollectTask

    # 采集任务列表（带分页）
    tasks = CollectTask.objects.filter(is_deleted=False).order_by("-created_at")

    # 筛选
    status = request.GET.get("status")
    platform = request.GET.get("platform")
    search = request.GET.get("search")

    if status:
        tasks = tasks.filter(collect_status=status)
    if platform:
        tasks = tasks.filter(platform_id=platform)
    if search:
        tasks = tasks.filter(Q(task_name__icontains=search) | Q(collect_urls__icontains=search))

    paginator = Paginator(tasks, 20)
    page = request.GET.get("page", 1)
    tasks = paginator.get_page(page)

    # 获取平台和店铺列表
    platforms = Platform.objects.filter(is_deleted=False, is_active=True).order_by("platform_name")
    shops = Shop.objects.filter(is_deleted=False, is_active=True).select_related("platform")

    return render(
        request,
        "modules/collect/collect_manage.html",
        {
            "tasks": tasks,
            "platforms": platforms,
            "shops": shops,
        },
    )


@login_required
def platform_list(request):
    """平台配置列表"""
    from core.models import Platform

    platforms = Platform.objects.filter(is_deleted=False).order_by("platform_name")

    # 筛选
    platform_type = request.GET.get("type")
    if platform_type:
        platforms = platforms.filter(platform_type=platform_type)

    return render(
        request,
        "modules/collect/platform_list.html",
        {
            "platforms": platforms,
        },
    )


@login_required
def shop_list(request):
    """店铺配置列表"""
    from core.models import Platform, Shop

    shops = Shop.objects.filter(is_deleted=False).select_related("platform").order_by("-created_at")

    # 筛选
    platform_id = request.GET.get("platform")
    if platform_id:
        shops = shops.filter(platform_id=platform_id)

    return render(
        request,
        "modules/collect/shop_list.html",
        {
            "shops": shops,
            "platforms": Platform.objects.filter(is_deleted=False, is_active=True),
        },
    )


@login_required
def listing_list(request):
    """Listing管理列表"""
    from core.models import Platform

    from .models import ProductListing

    listings = (
        ProductListing.objects.filter(is_deleted=False)
        .select_related("product", "platform", "shop")
        .order_by("-created_at")
    )

    # 筛选
    status = request.GET.get("status")
    platform = request.GET.get("platform")
    shop = request.GET.get("shop")
    search = request.GET.get("search")

    if status:
        listings = listings.filter(listing_status=status)
    if platform:
        listings = listings.filter(platform_id=platform)
    if shop:
        listings = listings.filter(shop_id=shop)
    if search:
        listings = listings.filter(Q(title__icontains=search) | Q(erp_sku__icontains=search))

    paginator = Paginator(listings, 20)
    page = request.GET.get("page", 1)
    listings = paginator.get_page(page)

    return render(
        request,
        "modules/collect/listing_list.html",
        {
            "listings": listings,
            "platforms": Platform.objects.filter(
                is_deleted=False, is_active=True, platform_type="cross"
            ),
        },
    )


# ---------------------- AJAX视图 ----------------------


@login_required
@require_POST
def collect_task_create_ajax(request):
    """AJAX创建采集任务，触发异步采集"""
    from .forms import CollectTaskForm
    from .models import CollectTask
    from .tasks import collect_and_land_task, collect_land_sync_task

    form = CollectTaskForm(request.POST, request=request)

    if form.is_valid():
        collect_task = form.save(commit=False)
        collect_task.created_by = request.user
        collect_task.updated_by = request.user
        collect_task.save()

        # 获取是否自动同步到跨境平台
        sync_cross = form.cleaned_data.get("sync_cross")
        cross_platform = form.cleaned_data.get("cross_platform")
        cross_shop = form.cleaned_data.get("cross_shop")
        pricing_rule = form.cleaned_data.get("pricing_rule")
        translate = form.cleaned_data.get("translate")
        target_language = form.cleaned_data.get("target_language")

        if sync_cross:
            # 触发「采集+落地+同步」全链路任务
            celery_task = collect_land_sync_task.delay(
                collect_task.id,
                cross_platform.id if cross_platform else None,
                cross_shop.id if cross_shop else None,
                pricing_rule.id if pricing_rule else None,
                translate,
                target_language,
            )
        else:
            # 仅触发「采集+落地」任务
            celery_task = collect_and_land_task.delay(collect_task.id)

        # 更新Celery任务ID
        collect_task.celery_task_id = celery_task.id
        collect_task.save()

        return JsonResponse(
            {
                "code": 200,
                "msg": "采集任务已触发，正在后台处理",
                "data": {"task_id": collect_task.id},
            }
        )
    else:
        return JsonResponse({"code": 400, "msg": "表单验证失败", "data": {"errors": form.errors}})


@login_required
@require_GET
def collect_task_status_ajax(request):
    """AJAX查询采集任务状态，供前端轮询"""
    from .models import CollectItem, CollectTask

    task_id = request.GET.get("task_id")
    collect_task = get_object_or_404(CollectTask, id=task_id, is_deleted=False)

    # 获取失败子项数
    fail_items = CollectItem.objects.filter(
        collect_task=collect_task, collect_status="failed", is_deleted=False
    ).count()

    land_fail_items = CollectItem.objects.filter(
        collect_task=collect_task, land_status="failed", is_deleted=False
    ).count()

    return JsonResponse(
        {
            "code": 200,
            "data": {
                "task_id": collect_task.id,
                "collect_status": collect_task.collect_status,
                "land_status": collect_task.land_status,
                "collect_num": collect_task.collect_num,
                "success_num": collect_task.success_num,
                "fail_num": collect_task.fail_num,
                "error_msg": collect_task.error_msg or "",
                "fail_items": fail_items,
                "land_fail_items": land_fail_items,
                "success_rate": collect_task.success_rate,
                "duration": collect_task.duration,
            },
        }
    )


@login_required
@require_GET
def collect_item_list_ajax(request):
    """AJAX查询采集子项列表"""
    from .models import CollectItem

    task_id = request.GET.get("task_id")
    collect_items = CollectItem.objects.filter(collect_task_id=task_id, is_deleted=False).order_by(
        "-created_at"
    )

    # 构造返回数据
    items = []
    for item in collect_items:
        item_data = {
            "id": item.id,
            "collect_url": item.collect_url,
            "item_name": item.item_name,
            "item_sku": item.item_sku,
            "collect_status": item.collect_status,
            "land_status": item.land_status,
            "land_error": item.land_error or "",
            "collected_at": (item.collected_at.isoformat() if item.collected_at else None),
            "landed_at": item.landed_at.isoformat() if item.landed_at else None,
        }

        if item.product:
            item_data["product_id"] = item.product.id
            item_data["product_name"] = item.product.name
            item_data["product_code"] = item.product.code

        items.append(item_data)

    return JsonResponse({"code": 200, "data": items})


@login_required
@require_POST
def create_listing_ajax(request):
    """AJAX创建Listing"""
    from .models import Product
    from .tasks import create_listing_task

    product_id = request.POST.get("product_id")
    platform_id = request.POST.get("platform_id")
    shop_id = request.POST.get("shop_id")
    pricing_rule_id = request.POST.get("pricing_rule_id")
    translate = request.POST.get("translate") == "true"
    target_language = request.POST.get("target_language", "en")

    if not all([product_id, platform_id, shop_id]):
        return JsonResponse({"code": 400, "msg": "缺少必要参数"})

    # 创建Listing任务
    celery_task = create_listing_task.delay(
        int(product_id),
        int(platform_id),
        int(shop_id),
        int(pricing_rule_id) if pricing_rule_id else None,
        translate,
        target_language,
    )

    return JsonResponse(
        {
            "code": 200,
            "msg": "Listing创建任务已提交",
            "data": {"task_id": celery_task.id},
        }
    )
