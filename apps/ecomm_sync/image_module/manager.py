import logging
import os
from typing import List

import requests

logger = logging.getLogger(__name__)


class ImageDownloader:
    """图片下载器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )

    def download_product_images(self, image_urls: List[str], product_code: str) -> dict:
        if not image_urls:
            return {"total": 0, "success": 0, "failed": 0, "paths": []}

        logger.info(f"开始下载 {product_code} 的 {len(image_urls)} 张图片")

        downloaded_paths = []
        success_count = 0
        failed_count = 0

        for i, url in enumerate(image_urls, 1):
            try:
                logger.info(f"下载 {i}/{len(image_urls)}: {url[:80]}...")
                filename = f"{product_code}_{i:04d}.jpg"
                local_path = os.path.join("media/products/imported", filename)

                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)

                    downloaded_paths.append(local_path)
                    success_count += 1
                    logger.info(f"下载成功: {local_path}")
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"下载失败: {url}, 错误: {e}")

        logger.info(
            f"下载完成: 成功 {success_count}/{len(image_urls)}, 失败 {failed_count}/{len(image_urls)}"
        )

        return {
            "total": len(image_urls),
            "success": success_count,
            "failed": failed_count,
            "paths": downloaded_paths,
        }


class ImageManager:
    """图片管理器"""

    def __init__(self, downloader: ImageDownloader = None):
        self.downloader = downloader or ImageDownloader()

    def download_images_for_product(self, image_urls, product_code: str) -> dict:
        return self.downloader.download_product_images(image_urls, product_code)

    def get_image_path(self, product_code: str, image_index: int = 0) -> str:
        return f"media/products/imported/{product_code}_{image_index:04d}.jpg"

    def test_connection(self) -> bool:
        return self.downloader.test_connection()


def get_image_downloader() -> ImageDownloader:
    """获取图片下载器实例"""
    return ImageDownloader()
