from typing import Dict, List, Optional
from django.utils.text import slugify
from django.conf import settings


class WooCommerceMapper:
    """WooCommerce字段映射器"""

    @staticmethod
    def map_to_woo(ecomm_product, raw_data: dict = None) -> dict:
        """
        将电商产品映射为WooCommerce产品

        Args:
            ecomm_product: EcommProduct实例
            raw_data: 原始采集数据（可选）

        Returns:
            WooCommerce产品数据字典
        """
        product = ecomm_product.product
        if not product:
            raise ValueError("未关联ERP产品")

        data = {
            "name": product.name,
            "slug": slugify(product.name),
            "type": "simple",
            "status": WooCommerceMapper._map_status(product.status),
            "catalog_visibility": "visible",
            "description": WooCommerceMapper._map_description(product, raw_data),
            "short_description": product.description or "",
            "sku": product.code,
            "regular_price": str(product.selling_price),
            "manage_stock": product.track_inventory,
            "stock_quantity": str(product.min_stock),
            "backorders": "notify" if product.track_inventory else "no",
            "sold_individually": True,
            "categories": WooCommerceMapper._map_categories(product),
            "images": WooCommerceMapper._map_images(product),
            "attributes": WooCommerceMapper._map_attributes(product),
            "meta_data": WooCommerceMapper._map_metadata(ecomm_product),
        }

        return data

    @staticmethod
    def _map_status(status: str) -> str:
        """映射产品状态"""
        status_map = {
            "active": "publish",
            "inactive": "draft",
            "discontinued": "private",
            "development": "draft",
        }
        return status_map.get(status, "draft")

    @staticmethod
    def _map_description(product, raw_data: dict = None) -> str:
        """映射产品描述"""
        if raw_data and "description" in raw_data:
            return raw_data["description"]

        desc_parts = []
        if product.description:
            desc_parts.append(product.description)
        if product.specifications:
            desc_parts.append(f"## 规格\n{product.specifications}")

        return "\n\n".join(desc_parts)

    @staticmethod
    def _map_categories(product) -> List[dict]:
        """映射产品分类"""
        categories = []

        if product.category:
            categories.append(
                {
                    "id": product.category.woo_category_id
                    if hasattr(product.category, "woo_category_id")
                    else None
                }
            )

        return categories

    @staticmethod
    def _map_images(product) -> List[dict]:
        """映射产品图片"""
        images = []

        if product.main_image:
            images.append(
                {
                    "src": product.main_image.url if product.main_image else "",
                    "alt": f"{product.name} - 主图",
                    "name": f"{product.name} - 主图",
                }
            )

        for product_image in product.images.filter(is_main=False).order_by("sort_order")[:5]:
            if product_image.image:
                images.append(
                    {
                        "src": product_image.image.url,
                        "alt": product_image.title or f"{product.name} - 图片",
                        "name": product_image.title or f"{product.name} - 图片",
                    }
                )

        return images

    @staticmethod
    def _map_attributes(product) -> List[dict]:
        """映射产品属性"""
        attributes = []

        for attr_value in product.attribute_values.all():
            attr = attr_value.attribute
            attributes.append(
                {
                    "id": None,
                    "name": attr.name,
                    "position": 0,
                    "visible": attr.is_filterable,
                    "variation": False,
                    "options": [attr_value.value],
                }
            )

        return attributes

    @staticmethod
    def _map_metadata(ecomm_product) -> List[dict]:
        """映射元数据"""
        metadata = [
            {"key": "external_url", "value": ecomm_product.external_url},
            {"key": "platform", "value": ecomm_product.platform.platform_type},
            {"key": "external_id", "value": ecomm_product.external_id},
            {"key": "ecomm_product_id", "value": str(ecomm_product.id)},
        ]

        if ecomm_product.raw_data:
            if "brand" in ecomm_product.raw_data:
                metadata.append({"key": "brand", "value": ecomm_product.raw_data.get("brand")})
            if "model" in ecomm_product.raw_data:
                metadata.append({"key": "model", "value": ecomm_product.raw_data.get("model")})

        return metadata

    @staticmethod
    def map_to_woo_category(product_category, parent_id: int = None) -> dict:
        """
        将ERP分类映射为WooCommerce分类

        Args:
            product_category: ProductCategory实例
            parent_id: 父分类ID

        Returns:
            WooCommerce分类数据字典
        """
        return {
            "name": product_category.name,
            "slug": slugify(product_category.name),
            "parent": parent_id,
            "description": product_category.description or "",
            "display": "default",
            "menu_order": product_category.sort_order,
        }

    @staticmethod
    def extract_price_update(ecomm_product) -> dict:
        """
        提取价格更新数据

        Args:
            ecomm_product: EcommProduct实例

        Returns:
            价格更新数据
        """
        product = ecomm_product.product
        if not product:
            raise ValueError("未关联ERP产品")

        return {
            "regular_price": str(product.selling_price),
        }

    @staticmethod
    def extract_stock_update(ecomm_product) -> dict:
        """
        提取库存更新数据

        Args:
            ecomm_product: EcommProduct实例

        Returns:
            库存更新数据
        """
        product = ecomm_product.product
        if not product:
            raise ValueError("未关联ERP产品")

        return {
            "manage_stock": product.track_inventory,
            "stock_quantity": str(product.min_stock),
            "stock_status": "instock" if product.min_stock > 0 else "outofstock",
        }

    @staticmethod
    def extract_status_update(ecomm_product) -> dict:
        """
        提取状态更新数据

        Args:
            ecomm_product: EcommProduct实例

        Returns:
            状态更新数据
        """
        product = ecomm_product.product
        if not product:
            raise ValueError("未关联ERP产品")

        status = WooCommerceMapper._map_status(product.status)

        return {
            "status": status,
        }

    @staticmethod
    def create_batch_updates(ecomm_products, update_type: str = "full") -> List[dict]:
        """
        创建批量更新数据

        Args:
            ecomm_products: EcommProduct查询集
            update_type: 更新类型 (full, price, stock, status)

        Returns:
            批量更新数据列表
        """
        updates = []

        for ecomm_product in ecomm_products:
            if not ecomm_product.woo_product_id:
                continue

            update = {"id": ecomm_product.woo_product_id}

            if update_type == "full":
                update.update(WooCommerceMapper.map_to_woo(ecomm_product))
            elif update_type == "price":
                update.update(WooCommerceMapper.extract_price_update(ecomm_product))
            elif update_type == "stock":
                update.update(WooCommerceMapper.extract_stock_update(ecomm_product))
            elif update_type == "status":
                update.update(WooCommerceMapper.extract_status_update(ecomm_product))

            updates.append(update)

        return updates
