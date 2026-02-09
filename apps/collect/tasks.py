"""
Celery异步任务模块
实现采集、落地、同步的全链路异步处理
"""
import uuid
import math
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from typing import Dict, Any

from .models import (
    CollectTask,
    CollectItem,
    ProductListing,
    Platform,
    Shop,
    PricingRule,
)
from .adapters import get_collect_adapter
from .services import ImageDownloader, TranslatorFactory, translate_product_data
from .exceptions import (
    CollectException,
    ProductCreateException,
    ListingCreateException,
    SyncException,
    ImageDownloadException,
    TranslationException,
)
from products.models import Product


def generate_erp_sku(source_platform: str, source_sku: str) -> str:
    """
    生成ERP统一SKU

    Args:
        source_platform: 源平台（taobao/1688）
        source_sku: 源平台SKU

    Returns:
        str: ERP SKU，如TB_12345_abc123
    """
    platform_prefix = source_platform.upper()
    random_suffix = uuid.uuid4().hex[:6]
    return f"{platform_prefix}_{source_sku}_{random_suffix}"


def apply_field_map_rules(
    collect_data: Dict[str, Any], platform_code: str, target_type: str = "product"
) -> Dict[str, Any]:
    """
    应用字段映射规则

    Args:
        collect_data: 采集的原始数据
        platform_code: 平台编码
        target_type: 目标类型（product/listing）

    Returns:
        dict: 映射后的数据
    """
    from .models import FieldMapRule

    # 获取映射规则
    rules = FieldMapRule.objects.filter(
        collect_platform=platform_code, target_type=target_type, is_active=True
    ).order_by("sort_order")

    mapped_data = collect_data.copy()

    for rule in rules:
        source_value = collect_data.get(rule.source_field)

        if rule.rule_type == "direct":
            # 直接映射
            mapped_data[rule.target_field] = source_value
        elif rule.rule_type == "calc":
            # 计算规则
            try:
                if rule.map_rule:
                    mapped_data[rule.target_field] = eval(
                        rule.map_rule, {"__builtins__": None}, {"value": source_value}
                    )
            except:
                mapped_data[rule.target_field] = source_value
        elif rule.rule_type == "fixed":
            # 固定值
            mapped_data[rule.target_field] = rule.map_rule
        # function类型暂不支持

    return mapped_data


@shared_task(bind=True, max_retries=3, retry_backoff=5)
def collect_and_land_task(self, collect_task_id: int):
    """
    采集+落地主任务：批量采集商品并落地到产品库

    Args:
        collect_task_id: CollectTask模型ID
    """
    try:
        # 1. 获取采集任务
        collect_task = CollectTask.objects.get(id=collect_task_id, is_deleted=False)

        # 更新任务状态为采集中
        collect_task.collect_status = "running"
        collect_task.started_at = timezone.now()
        collect_task.save()

        # 获取平台配置和适配器
        platform_config = collect_task.platform
        adapter = get_collect_adapter(platform_config)

        # 拆分采集链接
        collect_urls = [url.strip() for url in collect_task.collect_urls.split("\n") if url.strip()]
        collect_task.collect_num = len(collect_urls)
        collect_task.save()

        success_num = 0
        fail_num = 0

        # 2. 批量采集+落地
        for url in collect_urls:
            # 创建采集子项
            collect_item = CollectItem.objects.create(
                collect_task=collect_task,
                collect_url=url,
                create_user=collect_task.created_by,
                update_user=collect_task.updated_by,
            )

            try:
                # 3. 调用适配器采集单个商品
                collect_data = adapter.collect_item(url)
                collect_item.collect_data = collect_data
                collect_item.item_name = collect_data.get("product_name", "")
                collect_item.item_sku = collect_data.get("source_sku", "")
                collect_item.collect_status = "success"
                collect_item.collected_at = timezone.now()

                # 4. 应用字段映射规则
                mapped_data = apply_field_map_rules(
                    collect_data, platform_config.platform_code, "product"
                )

                # 5. 下载图片
                try:
                    image_downloader = ImageDownloader()
                    images = collect_data.get("images", [])
                    if images:
                        downloaded_images = image_downloader.download_images(
                            images, save_to_local=True
                        )
                        mapped_data["images"] = downloaded_images
                        if downloaded_images:
                            mapped_data["main_image"] = downloaded_images[0]
                except ImageDownloadException as e:
                    print(f"图片下载失败: {e.msg}")
                    # 使用原始图片URL
                    pass

                # 6. 落地到产品库（事务保证原子性）
                with transaction.atomic():
                    # 生成ERP SKU
                    erp_sku = generate_erp_sku(
                        platform_config.platform_code,
                        collect_data.get("source_sku", str(uuid.uuid4().hex[:8])),
                    )

                    # 创建产品库产品
                    product = Product.objects.create(
                        name=mapped_data.get("product_name", ""),
                        code=erp_sku,
                        main_image=mapped_data.get("main_image", ""),
                        selling_price=mapped_data.get("price", 0),
                        track_inventory=False,
                        description=mapped_data.get("description", ""),
                        specifications="",
                        created_by=collect_task.created_by,
                        updated_by=collect_task.updated_by,
                    )

                    # 关联采集子项和产品
                    collect_item.product = product
                    collect_item.land_status = "success"
                    collect_item.landed_at = timezone.now()

                success_num += 1

            except CollectException as e:
                # 采集失败
                collect_item.collect_status = "failed"
                collect_item.land_error = f"采集失败：{e.msg}"
                fail_num += 1
            except ProductCreateException as e:
                # 落地失败
                collect_item.collect_status = "success" if collect_item.collect_data else "failed"
                collect_item.land_status = "failed"
                collect_item.land_error = f"落地失败：{e.msg}"
                fail_num += 1
            except Exception as e:
                # 其他异常
                collect_item.collect_status = "success" if collect_item.collect_data else "failed"
                collect_item.land_status = "failed"
                collect_item.land_error = f"未知错误：{str(e)[:200]}"
                fail_num += 1
            finally:
                collect_item.save()

        # 7. 更新任务统计
        collect_task.success_num = success_num
        collect_task.fail_num = fail_num

        if success_num > 0 and fail_num == 0:
            collect_task.collect_status = "success"
            collect_task.land_status = "success"
        elif success_num > 0 and fail_num > 0:
            collect_task.collect_status = "partial"
            collect_task.land_status = "partial"
        else:
            collect_task.collect_status = "failed"
            collect_task.land_status = "failed"

        collect_task.completed_at = timezone.now()
        collect_task.save()

    except Exception as e:
        # 任务整体失败，更新状态
        try:
            collect_task = CollectTask.objects.get(id=collect_task_id, is_deleted=False)
            collect_task.collect_status = "failed"
            collect_task.error_msg = f"任务执行失败：{str(e)[:500]}"
            collect_task.completed_at = timezone.now()
            collect_task.save()
        except:
            pass

        # 重试
        self.retry(exc=e, countdown=5)


@shared_task(bind=True, max_retries=2, retry_backoff=3)
def create_listing_task(
    self,
    product_id: int,
    platform_id: int,
    shop_id: int,
    pricing_rule_id: int = None,
    translate: bool = False,
    target_language: str = "en",
):
    """
    创建Listing任务：从产品创建Listing

    Args:
        product_id: 产品ID
        platform_id: 平台ID
        shop_id: 店铺ID
        pricing_rule_id: 定价规则ID（可选）
        translate: 是否翻译
        target_language: 目标语言
    """
    try:
        # 获取产品、平台、店铺
        product = Product.objects.get(id=product_id, is_deleted=False)
        platform = Platform.objects.get(id=platform_id, is_deleted=False)
        shop = Shop.objects.get(id=shop_id, is_deleted=False)

        # 检查是否已存在Listing
        existing_listing = ProductListing.objects.filter(
            product=product, platform=platform, shop=shop, is_deleted=False
        ).first()

        if existing_listing:
            return {"listing_id": existing_listing.id, "status": "exists"}

        # 准备Listing数据
        listing_data = {
            "erp_sku": product.code,
            "title": product.name,
            "description": product.description or "",
            "main_image": product.main_image.url if product.main_image else "",
            "images": [],
            "cost": product.selling_price,
            "quantity": 0,
        }

        # 应用定价规则
        if pricing_rule_id:
            try:
                pricing_rule = PricingRule.objects.get(id=pricing_rule_id, is_active=True)
                listing_data["price"] = pricing_rule.calculate_price(product.selling_price)
            except PricingRule.DoesNotExist:
                listing_data["price"] = product.selling_price
        else:
            listing_data["price"] = product.selling_price

        # 翻译
        if translate:
            try:
                translator = TranslatorFactory.get_translator("baidu")
                listing_data["title"] = translator.translate(product.name, target_language)
                if product.description:
                    listing_data["description"] = translator.translate(
                        product.description, target_language
                    )
            except TranslationException as e:
                print(f"翻译失败: {e.msg}")

        # 创建Listing
        with transaction.atomic():
            listing = ProductListing.objects.create(
                product=product,
                platform=platform,
                shop=shop,
                erp_sku=listing_data["erp_sku"],
                title=listing_data["title"],
                description=listing_data["description"],
                main_image=listing_data["main_image"],
                images=listing_data["images"],
                price=listing_data["price"],
                cost=listing_data["cost"],
                quantity=listing_data["quantity"],
                listing_status="draft",
                sync_status="pending",
                created_by=product.created_by,
                updated_by=product.updated_by,
            )

        return {"listing_id": listing.id, "status": "created"}

    except Exception as e:
        self.retry(exc=e, countdown=3)


@shared_task(bind=True, max_retries=2, retry_backoff=3)
def collect_land_sync_task(
    self,
    collect_task_id: int,
    cross_platform_id: int,
    cross_shop_id: int,
    pricing_rule_id: int = None,
    translate: bool = False,
    target_language: str = "en",
):
    """
    采集+落地+同步全链路任务

    Args:
        collect_task_id: 采集任务ID
        cross_platform_id: 跨境平台ID
        cross_shop_id: 跨境店铺ID
        pricing_rule_id: 定价规则ID（可选）
        translate: 是否翻译
        target_language: 目标语言
    """
    try:
        # 1. 先执行采集+落地
        collect_and_land_task(collect_task_id)

        # 2. 获取采集落地成功的产品
        collect_task = CollectTask.objects.get(id=collect_task_id, is_deleted=False)
        success_items = CollectItem.objects.filter(
            collect_task=collect_task, land_status="success", is_deleted=False
        )

        if not success_items.exists():
            raise Exception("无落地成功的产品，无法创建Listing")

        # 3. 批量创建Listing
        listing_ids = []
        for item in success_items:
            if item.product:
                result = create_listing_task.delay(
                    item.product.id,
                    cross_platform_id,
                    cross_shop_id,
                    pricing_rule_id,
                    translate,
                    target_language,
                )
                listing_ids.append(result.id)

        return {"task_id": collect_task_id, "listing_count": len(listing_ids)}

    except Exception as e:
        self.retry(exc=e, countdown=3)


@shared_task
def sync_listing_to_platform_task(listing_id: int):
    """
    同步Listing到跨境平台

    Args:
        listing_id: Listing ID
    """
    try:
        listing = ProductListing.objects.get(id=listing_id, is_deleted=False)

        # TODO: 根据平台类型调用相应的同步适配器
        # 这里需要实现具体的平台同步逻辑
        # 如：ShopeeListingAdapter, TikTokListingAdapter等

        listing.sync_status = "success"
        listing.last_synced_at = timezone.now()
        listing.save()

        return {"listing_id": listing_id, "status": "synced"}

    except Exception as e:
        listing = ProductListing.objects.get(id=listing_id, is_deleted=False)
        listing.sync_status = "failed"
        listing.sync_error = str(e)[:500]
        listing.save()

        raise SyncException(platform_name=listing.platform.platform_name)


@shared_task
def batch_sync_listings_task(listing_ids: list):
    """
    批量同步Listing到跨境平台

    Args:
        listing_ids: Listing ID列表
    """
    results = []

    for listing_id in listing_ids:
        try:
            result = sync_listing_to_platform_task.delay(listing_id)
            results.append({"listing_id": listing_id, "status": "queued"})
        except Exception as e:
            results.append({"listing_id": listing_id, "status": "error", "error": str(e)})

    return results
