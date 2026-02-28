"""
图片下载器（简化版，无外部依赖，避免LSP错误）
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)


def download_product_images(image_urls, product_code):
    """下载产品图片"""
    if not image_urls:
        logger.warning(f"产品 {product_code} 无图片URL")
        return []

    logger.info(f"开始下载 {product_code} 的 {len(image_urls)} 张图片")

    downloaded_paths = []
    success_count = 0
    failed_count = 0

    for idx, url in enumerate(image_urls):
        try:
            filename = f"{product_code}_{idx+1:04d}.jpg"
            local_path = os.path.join("media/products/imported", filename)
            os.makedirs("media/products/imported", exist_ok=True)

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

            downloaded_paths.append(local_path)
            success_count += 1
            logger.info(f"下载成功: {filename}")

        except Exception as e:
            failed_count += 1
            logger.error(f"下载失败: {url}, 错误: {e}")

    logger.info(
        f"产品 {product_code} 下载完成: 成功 {success_count}/{len(image_urls)}, 失败 {failed_count}/{len(image_urls)}"
    )

    return downloaded_paths


def test_connection(test_url="https://www.baidu.com"):
    """测试网络连接"""
    try:
        response = requests.head(test_url, timeout=10)
        response.raise_for_status()
        logger.info(f"网络测试成功")
        return True
    except Exception as e:
        logger.error(f"网络测试失败: {e}")
        return False


def get_image_hash(image_path):
    """获取图片哈希值（8位）"""
    if not os.path.exists(image_path):
        return ""

    with open(image_path, "rb") as f:
        import hashlib

        return hashlib.sha256(f.read()).hexdigest()[:8]


def get_image_size(image_path):
    """获取图片尺寸"""
    if not os.path.exists(image_path):
        return 0, 0

    try:
        from PIL import Image as PILImage

        img = PILImage.open(image_path)
        return img.size
    except ImportError:
        logger.warning("PIL未安装")
        return 0, 0


def compress_image(image_path, quality=85):
    """压缩图片（可选）"""
    if not os.path.exists(image_path):
        return image_path

    try:
        from PIL import Image as PILImage

        img = PILImage.open(image_path)
        width, height = img.size

        if width > 1200 or height > 1200:
            max_dim = max(width, height)
            ratio = 1200.0 / max_dim
            if ratio > 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                img.save(image_path, quality=quality, optimize=True)
                logger.info(f"图片已压缩: {image_path}")

        return image_path
    except ImportError:
        logger.warning("PIL未安装，跳过压缩")
        return image_path


def delete_duplicate_images(image_paths):
    """删除重复图片"""
    seen = {}
    deleted_count = 0

    for path in image_paths:
        if not os.path.exists(path):
            continue

        file_hash = get_image_hash(path)

        if file_hash in seen_hashes:
            os.remove(path)
            deleted_count += 1
            logger.info(f"删除重复: {path}")
        else:
            seen_hashes[file_hash] = path

    logger.info(f"删除了 {deleted_count} 张重复图片")
    return deleted_count


if __name__ == "__main__":
    # 简单测试
    test_urls = [
        "https://via.placeholder.com/150x150.jpg",
        "https://via.placeholder.com/150x150.jpg",
    ]
    result = download_product_images(test_urls, "TEST001")
    print("测试结果:", result)
