import asyncio
import logging
from typing import Dict, List, Optional
from .base import BaseScraper
from core.models import Platform


logger = logging.getLogger(__name__)


class HybridScraper(BaseScraper):
    """混合采集器：API优先，失败降级到爬虫"""

    def __init__(self, platform: EcommPlatform):
        """
        初始化混合采集器

        Args:
            platform: 电商平台
        """
        super().__init__(platform)
        self.api_client = None
        self.browser_scraper = None

        self._init_components()

    def _init_components(self):
        """初始化API和爬虫组件"""
        try:
            self.api_client = self._create_api_client()
            logger.info(f"初始化API客户端: {self.platform.platform_type}")
        except Exception as e:
            logger.warning(f"API客户端初始化失败: {e}")

        try:
            self.browser_scraper = self._create_browser_scraper()
            logger.info(f"初始化浏览器爬虫: {self.platform.platform_type}")
        except Exception as e:
            logger.warning(f"浏览器爬虫初始化失败: {e}")

    def _create_api_client(self) -> Optional[object]:
        """创建API客户端"""
        if self.platform.platform_type == "taobao":
            try:
                from .taobao_api import TaobaoAPIClient

                return TaobaoAPIClient()
            except ImportError:
                logger.warning("淘宝API客户端未实现")
                return None
        elif self.platform.platform_type == "alibaba":
            try:
                from .alibaba_api import AlibabaAPIClient

                return AlibabaAPIClient()
            except ImportError:
                logger.warning("阿里API客户端未实现")
                return None
        return None

    def _create_browser_scraper(self) -> Optional["BaseScraper"]:
        """创建浏览器爬虫"""
        if self.platform.platform_type == "taobao":
            try:
                from .taobao import TaobaoBrowserScraper

                return TaobaoBrowserScraper(self.platform)
            except ImportError:
                logger.warning("淘宝浏览器爬虫未实现")
                return None
        elif self.platform.platform_type == "alibaba":
            try:
                from .alibaba import AlibabaBrowserScraper

                return AlibabaBrowserScraper(self.platform)
            except ImportError:
                logger.warning("阿里浏览器爬虫未实现")
                return None
        return None

    async def scrape_product(self, external_id: str) -> Dict:
        """
        采集单个产品

        Args:
            external_id: 平台商品ID

        Returns:
            产品数据字典
        """
        logger.info(f"开始采集产品: {external_id}")

        if self.api_client:
            try:
                logger.info(f"使用API采集: {external_id}")
                data = await self.api_client.get_product(external_id)
                self.failure_count = 0
                return data
            except Exception as e:
                logger.warning(f"API采集失败: {e}, 降级到浏览器爬虫")

        if self.browser_scraper:
            try:
                logger.info(f"使用浏览器采集: {external_id}")
                return await self.browser_scraper.scrape_with_retry(external_id)
            except Exception as e:
                logger.error(f"浏览器采集也失败: {e}")
                raise

        raise Exception("无可用的采集方法")

    async def scrape_product_list(self, limit: int = 100) -> List[Dict]:
        """
        采集产品列表

        Args:
            limit: 限制数量

        Returns:
            产品数据列表
        """
        logger.info(f"开始采集产品列表，限制: {limit}")

        if self.api_client:
            try:
                logger.info(f"使用API采集列表")
                return await self.api_client.get_products(limit)
            except Exception as e:
                logger.warning(f"API采集列表失败: {e}")

        if self.browser_scraper:
            try:
                logger.info(f"使用浏览器采集列表")
                return await self.browser_scraper.scrape_product_list(limit)
            except Exception as e:
                logger.error(f"浏览器采集列表也失败: {e}")
                raise

        raise Exception("无可用的采集方法")

    async def scrape_product_urls(self, urls: List[str]) -> List[Dict]:
        """
        批量采集产品URL

        Args:
            urls: 商品URL列表

        Returns:
            产品数据列表
        """
        results = []

        for url in urls:
            external_id = self._extract_external_id(url)
            try:
                data = await self.scrape_product(external_id)
                results.append(data)
            except Exception as e:
                logger.error(f"采集失败: {url}, 错误: {e}")
                continue

        return results

    def _extract_external_id(self, url: str) -> str:
        """
        从URL提取商品ID

        Args:
            url: 商品URL

        Returns:
            商品ID
        """
        if not url:
            return ""

        if "item.taobao.com" in url:
            parts = url.split("id=")
            if len(parts) > 1:
                return parts[1].split("&")[0]
        elif "detail.1688.com" in url:
            parts = url.split("offer/")
            if len(parts) > 1:
                offer_id = parts[1].split(".html")[0]
                return offer_id

        return url.split("/")[-1]

    async def scrape_with_timeout(self, external_id: str, timeout: float = 30.0) -> Dict:
        """
        带超时的采集

        Args:
            external_id: 平台商品ID
            timeout: 超时时间(秒)

        Returns:
            产品数据字典
        """
        try:
            return await asyncio.wait_for(self.scrape_product(external_id), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"采集超时: {external_id}")
            raise Exception(f"采集超时: {timeout}秒")

    def test_api_connection(self) -> bool:
        """
        测试API连接

        Returns:
            API是否可用
        """
        if not self.api_client:
            return False

        try:
            if hasattr(self.api_client, "test_connection"):
                return asyncio.run(self.api_client.test_connection())
            return True
        except Exception:
            return False

    def get_api_status(self) -> Dict[str, bool]:
        """
        获取组件状态

        Returns:
            状态字典
        """
        return {
            "api_available": self.api_client is not None,
            "browser_available": self.browser_scraper is not None,
            "api_tested": self.test_api_connection(),
        }
