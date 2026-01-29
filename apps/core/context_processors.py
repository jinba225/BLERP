"""
Admin Context Processor
"""
from django.conf import settings


def jazzmin_config(request):
    """Jazzmin 配置上下文"""
    from apps.core.models import SystemConfig
    from apps.core.utils.theme_config import THEME_COLORS, DEFAULT_THEME
    
    try:
        # 获取当前主题
        theme_config = SystemConfig.objects.filter(
            key='ui.theme',
            is_active=True
        ).first()
        
        if theme_config:
            current_theme = theme_config.value
        else:
            current_theme = DEFAULT_THEME
        
        # 获取 Logo
        logo_config = SystemConfig.objects.filter(
            key='ui.logo',
            is_active=True
        ).first()
        
        logo_url = logo_config.value if logo_config else ''
        
        # 构建颜色配置
        colors = THEME_COLORS.get(current_theme, THEME_COLORS[DEFAULT_THEME])
        
        return {
            'JAZZMIN_UI_THEME': {
                'theme': current_theme,
                'colors': colors,
                'logo': logo_url,
            }
        }
    except Exception as e:
        # 返回默认配置
        return {
            'JAZZMIN_UI_THEME': {
                'theme': DEFAULT_THEME,
                'colors': THEME_COLORS[DEFAULT_THEME],
                'logo': '',
            }
        }
