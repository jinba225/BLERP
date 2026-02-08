"""
Django自定义模板过滤器
"""
from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """从字典中获取值"""
    if d is None:
        return None
    return d.get(key)


@register.filter
def dict_key(d, key):
    """从字典中获取值（用于链式调用）"""
    if d is None:
        return None
    return d.get(key)
