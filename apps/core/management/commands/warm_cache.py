"""
缓存预热命令
在系统启动时预加载常用数据到缓存中，提升系统性能
"""

import logging
from datetime import datetime

from core.services.cache_manager import get_cache_manager
from core.services.rate_limiter import get_rate_limiter
from django.core.management.base import BaseCommand
from django.utils import timezone
from ecomm_sync.services.cache_manager import get_cache_manager as get_ecomm_cache_manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """缓存预热命令"""

    help = "预热系统缓存，提升系统启动性能"

    def handle(self, *args, **options):
        """执行缓存预热"""
        start_time = datetime.now()
        logger.info("开始执行缓存预热...")

        try:
            # 1. 预热核心缓存
            self._warm_core_cache()

            # 2. 预热电商同步缓存
            self._warm_ecomm_cache()

            # 3. 预热限流器
            self._warm_rate_limiters()

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"缓存预热完成，耗时: {duration:.2f}秒")
            self.stdout.write(self.style.SUCCESS(f"缓存预热完成，耗时: {duration:.2f}秒"))

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            self.stdout.write(self.style.ERROR(f"缓存预热失败: {e}"))

    def _warm_core_cache(self):
        """预热核心系统缓存"""
        logger.info("预热核心系统缓存...")

        # 获取缓存管理器
        cache_manager = get_cache_manager()

        # 预热系统配置
        try:
            from core.models import SystemConfig

            async def load_system_configs():
                configs = SystemConfig.objects.filter(is_active=True)
                for config in configs:
                    key = f"system_config:{config.key}"
                    await cache_manager.set(
                        key,
                        {
                            "key": config.key,
                            "value": config.value,
                            "config_type": config.config_type,
                            "description": config.description,
                        },
                        "system_config",
                    )

            import asyncio

            asyncio.run(load_system_configs())
            logger.info("系统配置缓存预热完成")

        except Exception as e:
            logger.error(f"系统配置缓存预热失败: {e}")

        # 预热公司信息
        try:
            from core.models import Company

            async def load_company_info():
                companies = Company.objects.filter(is_active=True)
                for company in companies:
                    key = f"company:{company.id}"
                    await cache_manager.set(
                        key,
                        {
                            "id": company.id,
                            "name": company.name,
                            "code": company.code,
                            "address": company.address,
                            "phone": company.phone,
                            "email": company.email,
                        },
                        "company_info",
                    )

            import asyncio

            asyncio.run(load_company_info())
            logger.info("公司信息缓存预热完成")

        except Exception as e:
            logger.error(f"公司信息缓存预热失败: {e}")

        # 预热平台配置
        try:
            from core.models import Platform

            async def load_platforms():
                platforms = Platform.objects.filter(is_active=True)
                for platform in platforms:
                    key = f"platform:{platform.platform_code}"
                    await cache_manager.set(
                        key,
                        {
                            "id": platform.id,
                            "platform_code": platform.platform_code,
                            "platform_name": platform.platform_name,
                            "platform_type": platform.platform_type,
                            "api_url": platform.api_url,
                            "is_active": platform.is_active,
                        },
                        "platform_info",
                    )

            import asyncio

            asyncio.run(load_platforms())
            logger.info("平台配置缓存预热完成")

        except Exception as e:
            logger.error(f"平台配置缓存预热失败: {e}")

    def _warm_ecomm_cache(self):
        """预热电商同步缓存"""
        logger.info("预热电商同步缓存...")

        # 获取电商缓存管理器
        ecomm_cache_manager = get_ecomm_cache_manager()

        # 预热店铺信息
        try:
            from core.models import Shop

            async def load_shops():
                shops = Shop.objects.filter(is_active=True)
                for shop in shops:
                    key = f"shop:{shop.id}"
                    await ecomm_cache_manager.set(
                        key,
                        {
                            "id": shop.id,
                            "shop_name": shop.shop_name,
                            "platform": shop.platform.platform_code,
                            "shop_id": shop.shop_id,
                            "currency": shop.currency,
                            "is_active": shop.is_active,
                        },
                        "shop_info",
                    )

            import asyncio

            asyncio.run(load_shops())
            logger.info("店铺信息缓存预热完成")

        except Exception as e:
            logger.error(f"店铺信息缓存预热失败: {e}")

        # 预热分类信息
        try:
            from products.models import Category

            async def load_categories():
                categories = Category.objects.filter(is_active=True)
                for category in categories:
                    key = f"category:{category.id}"
                    await ecomm_cache_manager.set(
                        key,
                        {
                            "id": category.id,
                            "name": category.name,
                            "code": category.code,
                            "parent_id": category.parent_id,
                            "is_active": category.is_active,
                        },
                        "category_list",
                    )

            import asyncio

            asyncio.run(load_categories())
            logger.info("分类信息缓存预热完成")

        except Exception as e:
            logger.error(f"分类信息缓存预热失败: {e}")

    def _warm_rate_limiters(self):
        """预热限流器"""
        logger.info("预热限流器...")

        # 预加载所有平台的限流器
        from core.config import PLATFORM_RATE_LIMITS

        for platform in PLATFORM_RATE_LIMITS.keys():
            try:
                limiter = get_rate_limiter(platform)
                status = limiter.get_status()
                logger.debug(f"限流器预热: {platform}, status: {status}")
            except Exception as e:
                logger.error(f"限流器预热失败: {platform}, error: {e}")

        logger.info("限流器预热完成")
