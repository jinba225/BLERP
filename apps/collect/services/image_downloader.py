"""
图片下载服务
支持图片下载、转换、上传到本地或云存储
"""

import hashlib
import os
from typing import Dict, List, Optional

import requests
from django.core.files.base import ContentFile
from django.utils import timezone

from .exceptions import ImageDownloadException


class ImageDownloader:
    """图片下载器"""

    def __init__(self, upload_to="collect/images/"):
        """
        初始化图片下载器

        Args:
            upload_to: 上传路径
        """
        self.upload_to = upload_to
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

    def download_image(self, image_url: str, save_to_local: bool = True) -> Optional[str]:
        """
        下载单张图片

        Args:
            image_url: 图片URL
            save_to_local: 是否保存到本地

        Returns:
            str: 本地路径或CDN URL

        Raises:
            ImageDownloadException: 下载失败
        """
        if not image_url:
            return None

        try:
            # 下载图片
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()

            # 生成文件名
            file_hash = hashlib.sha256(image_url.encode()).hexdigest()[:8]
            ext = self._get_extension(response.headers.get("content-type", ""))
            filename = f"{file_hash}{ext}"

            if save_to_local:
                # 保存到本地
                file_path = self._save_to_local(filename, response.content)
                return file_path
            else:
                # 返回原始URL
                return image_url

        except requests.exceptions.Timeout:
            raise ImageDownloadException(image_url, "下载超时")
        except requests.exceptions.RequestException as e:
            raise ImageDownloadException(image_url, f"下载失败: {str(e)}")
        except Exception as e:
            raise ImageDownloadException(image_url, f"处理失败: {str(e)}")

    def download_images(self, image_urls: List[str], save_to_local: bool = True) -> List[str]:
        """
        批量下载图片

        Args:
            image_urls: 图片URL列表
            save_to_local: 是否保存到本地

        Returns:
            list: 成功下载的图片路径列表
        """
        results = []

        for url in image_urls:
            try:
                image_path = self.download_image(url, save_to_local)
                if image_path:
                    results.append(image_path)
            except ImageDownloadException as e:
                # 记录错误但继续下载其他图片
                print(f"图片下载失败: {e.msg}")
                continue

        return results

    def _save_to_local(self, filename: str, content: bytes) -> str:
        """
        保存图片到本地

        Args:
            filename: 文件名
            content: 图片内容

        Returns:
            str: 相对路径
        """
        from django.core.files.storage import default_storage

        # 构造完整路径
        date_path = timezone.now().strftime("%Y/%m/%d")
        file_path = os.path.join(self.upload_to, date_path, filename)

        # 保存文件
        default_storage.save(file_path, ContentFile(content))

        # 返回URL
        return default_storage.url(file_path)

    def _get_extension(self, content_type: str) -> str:
        """
        根据Content-Type获取文件扩展名

        Args:
            content_type: Content-Type

        Returns:
            str: 文件扩展名
        """
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }

        return ext_map.get(content_type.lower(), ".jpg")

    def optimize_image(self, image_path: str, max_width: int = 1200, quality: int = 85) -> str:
        """
        优化图片（缩放、压缩）

        Args:
            image_path: 图片路径
            max_width: 最大宽度
            quality: 图片质量（1-100）

        Returns:
            str: 优化后的图片路径
        """
        try:
            from PIL import Image

            # 打开图片
            img = Image.open(image_path)

            # 缩放图片
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # 保存优化后的图片
            img.save(image_path, optimize=True, quality=quality)

            return image_path

        except ImportError:
            # 未安装Pillow库，跳过优化
            print("警告: 未安装Pillow库，跳过图片优化")
            return image_path
        except Exception as e:
            print(f"图片优化失败: {str(e)}")
            return image_path


class ImageConverter:
    """图片格式转换器"""

    @staticmethod
    def convert_to_webp(image_path: str, quality: int = 80) -> str:
        """
        转换为WebP格式

        Args:
            image_path: 图片路径
            quality: 图片质量

        Returns:
            str: WebP格式图片路径
        """
        try:
            from PIL import Image

            img = Image.open(image_path)
            webp_path = image_path.rsplit(".", 1)[0] + ".webp"
            img.save(webp_path, "WEBP", quality=quality)

            return webp_path

        except ImportError:
            raise ImageDownloadException(image_path, "未安装Pillow库")
        except Exception as e:
            raise ImageDownloadException(image_path, f"格式转换失败: {str(e)}")

    @staticmethod
    def resize_image(image_path: str, width: int, height: int = None) -> str:
        """
        调整图片大小

        Args:
            image_path: 图片路径
            width: 目标宽度
            height: 目标高度（可选，保持比例）

        Returns:
            str: 调整后的图片路径
        """
        try:
            from PIL import Image

            img = Image.open(image_path)

            if height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            img.save(image_path)

            return image_path

        except ImportError:
            raise ImageDownloadException(image_path, "未安装Pillow库")
        except Exception as e:
            raise ImageDownloadException(image_path, f"图片缩放失败: {str(e)}")


def download_product_images(
    image_urls: List[str], save_to_local: bool = True
) -> Dict[str, List[str]]:
    """
    下载产品所有图片的便捷函数

    Args:
        image_urls: 图片URL列表
        save_to_local: 是否保存到本地

    Returns:
        dict: {
            'success': ['path1', 'path2'],
            'failed': ['url1', 'url2']
        }
    """
    downloader = ImageDownloader()
    results = {"success": [], "failed": []}

    for url in image_urls:
        try:
            path = downloader.download_image(url, save_to_local)
            if path:
                results["success"].append(path)
        except ImageDownloadException:
            results["failed"].append(url)

    return results
