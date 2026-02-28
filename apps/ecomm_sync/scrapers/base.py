import abc
import asyncio
import logging
import random
from typing import Dict, List

from ecomm_sync.models import EcommPlatform

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """爬虫基础类"""

    def __init__(self, platform: EcommPlatform):
        """
        初始化爬虫

        Args:
            platform: 电商平台
        """
        self.platform = platform
        self.failure_count = 0
        self.max_retries = 3

    @abc.abstractmethod
    async def scrape_product(self, external_id: str) -> Dict:
        """
        采集单个产品

        Args:
            external_id: 平台商品ID

        Returns:
            产品数据字典
        """
        pass

    @abc.abstractmethod
    async def scrape_product_list(self, limit: int = 100) -> List[Dict]:
        """
        采集产品列表

        Args:
            limit: 限制数量

        Returns:
            产品数据列表
        """
        pass

    async def scrape_with_retry(self, external_id: str) -> Dict:
        """
        带重试的采集

        Args:
            external_id: 平台商品ID

        Returns:
            产品数据字典
        """
        for attempt in range(self.max_retries):
            try:
                delay = random.uniform(2, 5) * (attempt + 1)
                await asyncio.sleep(delay)

                data = await self.scrape_product(external_id)
                self.failure_count = 0
                return data

            except Exception as e:
                self.failure_count += 1
                logger.warning(
                    f"采集失败 (尝试 {attempt + 1}/{self.max_retries}): {external_id}, 错误: {e}"
                )

                if attempt == self.max_retries - 1:
                    raise Exception(f"采集失败，已达最大重试次数: {str(e)}")

    def _extract_price(self, price_str: str) -> float:
        """
        提取价格

        Args:
            price_str: 价格字符串

        Returns:
            价格数值
        """
        if not price_str:
            return 0.0

        price_str = str(price_str).replace("¥", "").replace(",", "").replace("元", "").strip()

        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def _extract_stock(self, stock_str: str) -> int:
        """
        提取库存

        Args:
            stock_str: 库存字符串

        Returns:
            库存数量
        """
        if not stock_str:
            return 0

        stock_str = str(stock_str).strip().lower()

        if "有货" in stock_str or "库存" in stock_str:
            return 999
        elif "无货" in stock_str or "缺货" in stock_str:
            return 0
        elif "件" in stock_str:
            try:
                return int("".join(filter(str.isdigit, stock_str)))
            except ValueError:
                return 0
        else:
            return 0

    def _map_status(self, status_str: str) -> str:
        """
        映射状态

        Args:
            status_str: 平台状态字符串

        Returns:
            ERP状态
        """
        if not status_str:
            return "inactive"

        status_str = str(status_str).strip().lower()

        status_map = {
            "onsale": ["在售", "销售中", "有货", "active"],
            "offshelf": ["下架", "已下架", "offshelf", "inactive", "discontinued"],
        }

        for erp_status, keywords in status_map.items():
            for keyword in keywords:
                if keyword in status_str:
                    return erp_status

        return "inactive"

    def _format_description(self, title: str, description: str = "") -> str:
        """
        格式化描述

        Args:
            title: 产品标题
            description: 产品描述

        Returns:
            格式化后的描述
        """
        if description:
            return description

        return title or ""

    def _normalize_images(self, images: List[str]) -> List[str]:
        """
        标准化图片URL

        Args:
            images: 图片URL列表

        Returns:
            标准化后的图片列表
        """
        normalized = []
        seen = set()

        for img in images:
            if not img:
                continue

            img_url = str(img).strip()

            if img_url in seen:
                continue
            seen.add(img_url)

            if not img_url.startswith("http"):
                continue

            normalized.append(img_url)

        return normalized[:6]

    def _create_mock_data(self, external_id: str) -> Dict:
        """
        创建模拟数据（用于测试）

        Args:
            external_id: 平台商品ID

        Returns:
            模拟产品数据
        """
        return {
            "id": external_id,
            "title": f"测试产品 {external_id}",
            "price": f"{random.uniform(50, 500):.2f}",
            "stock": random.randint(0, 100),
            "description": "这是一个测试产品描述",
            "images": [
                "https://via.placeholder.com/400x400.png",
                "https://via.placeholder.com/400x400.png",
            ],
            "category": "测试分类",
            "brand": "测试品牌",
            "model": f"TEST-{external_id}",
            "specifications": "测试规格",
            "status": "onsale",
        }

    @staticmethod
    def get_scraper(platform: EcommPlatform):
        """
        获取对应平台的爬虫实例

        Args:
            platform: 电商平台

        Returns:
            爬虫实例
        """
        from .hybrid import HybridScraper

        if not platform:
            raise ValueError("平台不能为空")

        return HybridScraper(platform)

    def is_rate_limited(self, response_status: int = None, error_msg: str = "") -> bool:
        """
        判断是否被限流

        Args:
            response_status: 响应状态码
            error_msg: 错误消息

        Returns:
            是否被限流
        """
        if response_status == 429:
            return True

        rate_limit_keywords = [
            "rate limit",
            "频率限制",
            "访问频率",
            "too many requests",
            "请求过多",
            "限流",
            "访问过快",
        ]

        if error_msg:
            return any(keyword in error_msg.lower() for keyword in rate_limit_keywords)

        return False
