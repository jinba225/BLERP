"""
Signals for the core app.
"""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save)
@receiver(post_delete)
def clear_company_cache(sender, **kwargs):
    """
    当Company模型被保存或删除时，清除公司信息缓存

    Args:
        sender: 发送信号的模型类
        kwargs: 信号参数
    """
    from .models import Company

    # 只处理Company模型的信号
    if sender == Company:
        # 清除所有语言的公司缓存（使用keys方法）
        try:
            # 获取所有以active_company_开头的缓存键
            company_cache_keys = cache.keys("active_company_*")
            if company_cache_keys:
                cache.delete_many(company_cache_keys)
        except AttributeError:
            # 如果缓存后端不支持keys方法，则删除已知语言的缓存
            for lang in ["zh-hans", "zh-cn", "en"]:
                cache_key = f"active_company_{lang}"
                cache.delete(cache_key)
