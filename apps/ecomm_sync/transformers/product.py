import logging
from typing import Dict, Optional
from django.utils.text import slugify
from ecomm_sync.models import EcommProduct
from products.models import Product, ProductCategory, Brand, Unit


logger = logging.getLogger(__name__)


class ProductTransformer:
    """产品数据转换器"""

    @staticmethod
    def transform(raw_data: Dict, ecomm_product: EcommProduct) -> Product:
        """
        将原始采集数据转换为Product

        Args:
            raw_data: 原始采集数据
            ecomm_product: 电商产品实例

        Returns:
            产品实例
        """
        logger.info(f'开始转换产品: {raw_data.get("title", "未知")}')

        try:
            product = Product(
                name=raw_data.get("title", "")[:200],
                code=ProductTransformer._generate_code(raw_data),
                description=raw_data.get("description", ""),
                specifications=raw_data.get("specifications", ""),
                model=raw_data.get("model", ""),
                product_type="finished",
                status="active",
                selling_price=float(str(raw_data.get("price", 0))),
                cost_price=float(str(raw_data.get("price", 0))) * 0.7,
                track_inventory=True,
                min_stock=int(str(raw_data.get("stock", 0))),
            )

            product.save()

            logger.info(f"产品创建成功: {product.code} - {product.name}")
            return product

        except Exception as e:
            logger.error(f"产品转换失败: {e}")
            raise

    @staticmethod
    def _generate_code(raw_data: Dict) -> str:
        """
        生成产品编码

        Args:
            raw_data: 原始数据

        Returns:
            产品编码
        """
        external_id = str(raw_data.get("id", ""))
        brand = str(raw_data.get("brand", ""))
        model = str(raw_data.get("model", ""))

        if external_id:
            return f"ECOMM-{external_id}"
        elif brand and model:
            return f"{brand.upper()}-{model.upper()}"
        else:
            return f"ECOMM-{external_id}"

    @staticmethod
    def sync_category(
        raw_data: Dict, parent_category: Optional[ProductCategory] = None
    ) -> ProductCategory:
        """
        同步或创建分类

        Args:
            raw_data: 原始数据
            parent_category: 父分类

        Returns:
            分类实例
        """
        from products.models import ProductCategory

        category_name = raw_data.get("category", "默认分类")

        category, created = ProductCategory.objects.get_or_create(
            name=category_name,
            defaults={
                "code": slugify(category_name).upper()[:50],
                "parent": parent_category,
                "description": f"自动创建的分类: {category_name}",
            },
        )

        if created:
            logger.info(f"创建新分类: {category_name}")

        return category

    @staticmethod
    def sync_brand(raw_data: Dict) -> Brand:
        """
        同步或创建品牌

        Args:
            raw_data: 原始数据

        Returns:
            品牌实例
        """
        from products.models import Brand

        brand_name = raw_data.get("brand", "默认品牌")

        brand, created = Brand.objects.get_or_create(
            name=brand_name,
            defaults={
                "code": slugify(brand_name).upper()[:50],
                "description": f"自动创建的品牌: {brand_name}",
            },
        )

        if created:
            logger.info(f"创建新品牌: {brand_name}")

        return brand

    @staticmethod
    def get_default_unit() -> Unit:
        """
        获取或创建默认单位

        Returns:
            单位实例
        """
        from products.models import Unit

        unit, created = Unit.objects.get_or_create(
            name="件",
            defaults={
                "symbol": "PC",
                "unit_type": "count",
                "description": "默认计数单位",
            },
        )

        if created:
            unit.is_default = True
            unit.save()

        return unit

    @staticmethod
    def update_existing_product(product: Product, raw_data: Dict):
        """
        更新现有产品

        Args:
            product: 产品实例
            raw_data: 原始数据
        """
        logger.info(f"更新产品: {product.code}")

        old_price = float(product.selling_price)
        new_price = float(str(raw_data.get("price", 0)))

        if old_price != new_price:
            product.selling_price = new_price
            logger.info(f"价格更新: ¥{old_price} -> ¥{new_price}")

        old_stock = product.min_stock
        new_stock = int(str(raw_data.get("stock", 0)))

        if old_stock != new_stock:
            product.min_stock = new_stock
            logger.info(f"库存更新: {old_stock} -> {new_stock}")

        new_desc = raw_data.get("description", "")
        if new_desc and new_desc != product.description:
            product.description = new_desc
            logger.info(f"描述更新")

        new_specs = raw_data.get("specifications", "")
        if new_specs and new_specs != product.specifications:
            product.specifications = new_specs
            logger.info(f"规格更新")

        product.save()
