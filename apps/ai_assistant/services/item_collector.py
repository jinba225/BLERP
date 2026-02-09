"""
明细收集器服务

用于在多轮对话中收集业务对象的明细列表，如订单明细、调拨明细等
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CollectionStatus(Enum):
    """收集状态"""

    COLLECTING = "collecting"  # 收集中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


@dataclass
class ItemLine:
    """明细行"""

    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    # 可扩展其他字段
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """验证明细行是否完整"""
        return self.product_id is not None and self.quantity is not None and self.quantity > 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
        }
        if self.unit_price is not None:
            result["unit_price"] = self.unit_price
        result.update(self.extra_data)
        return result


class ItemCollector:
    """
    明细收集器

    用于在多轮对话中收集业务对象的明细列表
    """

    def __init__(self, context_key: str = "item_collection"):
        """
        初始化收集器

        Args:
            context_key: 在对话上下文中存储的键名
        """
        self.context_key = context_key
        self.items: List[ItemLine] = []
        self.status = CollectionStatus.COLLECTING
        self.current_item: Optional[ItemLine] = None

    def start_collection(self):
        """开始收集"""
        self.items = []
        self.status = CollectionStatus.COLLECTING
        self.current_item = None

    def add_item(self, item: ItemLine) -> bool:
        """
        添加明细行

        Args:
            item: 明细行

        Returns:
            是否添加成功
        """
        if not item.is_valid():
            return False

        self.items.append(item)
        return True

    def add_item_from_dict(self, item_dict: Dict[str, Any]) -> bool:
        """
        从字典添加明细行

        Args:
            item_dict: 明细行字典

        Returns:
            是否添加成功
        """
        item = ItemLine(
            product_id=item_dict.get("product_id"),
            product_name=item_dict.get("product_name"),
            quantity=item_dict.get("quantity"),
            unit_price=item_dict.get("unit_price"),
            extra_data={
                k: v
                for k, v in item_dict.items()
                if k not in ["product_id", "product_name", "quantity", "unit_price"]
            },
        )
        return self.add_item(item)

    def update_current_item(self, field_name: str, value: Any):
        """
        更新当前正在编辑的明细行

        Args:
            field_name: 字段名
            value: 字段值
        """
        if self.current_item is None:
            self.current_item = ItemLine()

        if field_name == "product_id":
            self.current_item.product_id = value
        elif field_name == "product_name":
            self.current_item.product_name = value
        elif field_name == "quantity":
            self.current_item.quantity = value
        elif field_name == "unit_price":
            self.current_item.unit_price = value
        else:
            self.current_item.extra_data[field_name] = value

    def confirm_current_item(self) -> bool:
        """
        确认当前明细行

        Returns:
            是否确认成功
        """
        if self.current_item and self.current_item.is_valid():
            self.items.append(self.current_item)
            self.current_item = None
            return True
        return False

    def get_items(self) -> List[Dict[str, Any]]:
        """
        获取所有明细行

        Returns:
            明细行字典列表
        """
        return [item.to_dict() for item in self.items]

    def get_summary(self) -> str:
        """
        获取收集摘要

        Returns:
            摘要文本
        """
        if not self.items:
            return "暂无明细"

        summary = f"已收集 {len(self.items)} 条明细:\n"
        for i, item in enumerate(self.items, 1):
            line = f"{i}. {item.product_name or '产品ID:' + str(item.product_id)} "
            line += f"数量: {item.quantity}"
            if item.unit_price:
                line += f", 单价: {item.unit_price}"
            summary += line + "\n"

        return summary

    def is_complete(self) -> bool:
        """
        是否收集完成

        Returns:
            是否完成
        """
        return self.status == CollectionStatus.COMPLETED and len(self.items) > 0

    def complete_collection(self):
        """完成收集"""
        if len(self.items) > 0:
            self.status = CollectionStatus.COMPLETED

    def cancel_collection(self):
        """取消收集"""
        self.status = CollectionStatus.CANCELLED
        self.items = []
        self.current_item = None

    def to_context(self) -> Dict[str, Any]:
        """
        转换为上下文字典，用于保存到对话上下文

        Returns:
            上下文字典
        """
        return {
            "status": self.status.value,
            "items": [item.to_dict() for item in self.items],
            "current_item": self.current_item.to_dict() if self.current_item else None,
        }

    @classmethod
    def from_context(
        cls, context_data: Dict[str, Any], context_key: str = "item_collection"
    ) -> "ItemCollector":
        """
        从上下文字典恢复收集器

        Args:
            context_data: 上下文字典
            context_key: 上下文键名

        Returns:
            收集器实例
        """
        collector = cls(context_key=context_key)

        if context_data:
            collector.status = CollectionStatus(context_data.get("status", "collecting"))
            collector.items = [
                ItemLine(
                    product_id=item.get("product_id"),
                    product_name=item.get("product_name"),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    extra_data={
                        k: v
                        for k, v in item.items()
                        if k not in ["product_id", "product_name", "quantity", "unit_price"]
                    },
                )
                for item in context_data.get("items", [])
            ]

            current_item_data = context_data.get("current_item")
            if current_item_data:
                collector.current_item = ItemLine(
                    product_id=current_item_data.get("product_id"),
                    product_name=current_item_data.get("product_name"),
                    quantity=current_item_data.get("quantity"),
                    unit_price=current_item_data.get("unit_price"),
                    extra_data={
                        k: v
                        for k, v in current_item_data.items()
                        if k not in ["product_id", "product_name", "quantity", "unit_price"]
                    },
                )

        return collector


class ItemCollectionHelper:
    """
    明细收集辅助类

    提供便捷的静态方法用于处理明细收集
    """

    @staticmethod
    def parse_product_input(user_input: str) -> Dict[str, Any]:
        """
        解析用户输入的产品信息

        Args:
            user_input: 用户输入，如 "10个笔记本电脑 @ 5000元"

        Returns:
            解析后的产品信息字典
        """
        import re

        result = {}

        # 提取数量
        quantity_pattern = r"(\d+(?:\.\d+)?)\s*(个|台|件|套|箱|kg|千克)"
        quantity_match = re.search(quantity_pattern, user_input)
        if quantity_match:
            result["quantity"] = float(quantity_match.group(1))

        # 提取单价
        price_pattern = r"(?:@|单价|价格)\s*:?(\d+(?:\.\d+)?)\s*(元|块|USD)?"
        price_match = re.search(price_pattern, user_input)
        if price_match:
            result["unit_price"] = float(price_match.group(1))

        # 提取产品名称（简化处理，实际应该从产品库搜索）
        # 这里假设产品名称在数量之前
        parts = user_input.split(quantity_pattern)[0] if quantity_match else user_input
        product_name = parts.strip()
        if product_name:
            result["product_name"] = product_name

        return result

    @staticmethod
    def validate_items(
        items: List[Dict[str, Any]], required_fields: List[str] = None
    ) -> tuple[bool, str]:
        """
        验证明细列表

        Args:
            items: 明细列表
            required_fields: 必填字段列表

        Returns:
            (是否有效, 错误信息)
        """
        if not items:
            return False, "明细列表不能为空"

        if required_fields is None:
            required_fields = ["product_id", "quantity"]

        for i, item in enumerate(items, 1):
            for field_name in required_fields:
                if field_name not in item or item[field_name] is None:
                    return False, f"第{i}行缺少必填字段: {field_name}"

            if "quantity" in item and item["quantity"] <= 0:
                return False, f"第{i}行数量必须大于0"

        return True, ""

    @staticmethod
    def calculate_total(items: List[Dict[str, Any]]) -> float:
        """
        计算明细总额

        Args:
            items: 明细列表

        Returns:
            总额
        """
        total = 0.0
        for item in items:
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            total += quantity * unit_price
        return total
