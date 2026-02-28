"""
上下文处理器

为模板提供全局上下文变量
"""
from django.conf import settings


def company_info(request):
    """
    公司信息上下文处理器
    """
    return {
        'company_name': getattr(settings, 'COMPANY_NAME', 'BetterLaser'),
        'company_logo': getattr(settings, 'COMPANY_LOGO', '/static/images/logo.png'),
    }


def csp_nonce(request):
    """
    CSP nonce 上下文处理器
    
    将 csp_nonce 添加到模板上下文中，用于内联脚本和样式
    """
    nonce = getattr(request, 'csp_nonce', '')
    return {
        'csp_nonce': nonce,
    }