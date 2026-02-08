"""
Context processors for injecting global template variables.
"""
from django.core.cache import cache
from django.utils.translation import get_language
from .models import Company


def company_info(request):
    """
    向所有模板注入公司信息（带缓存）

    Returns:
        dict: 包含公司信息的字典（支持国际化）
    """
    # 使用缓存键包含语言代码，支持国际化
    lang_code = get_language()
    cache_key = f'active_company_{lang_code}'

    # 尝试从缓存获取
    company_data = cache.get(cache_key)

    if company_data is None:
        try:
            company = Company.objects.filter(is_active=True).select_related('created_by', 'updated_by').first()

            if company:
                # 根据语言选择描述
                if lang_code == 'en':
                    description = company.description_en or company.description
                else:
                    description = company.description

                company_data = {
                    'company': company,
                    'company_name': company.name,
                    'company_code': company.code,
                    'company_address': company.address,
                    'company_phone': company.phone,
                    'company_email': company.email,
                    'company_website': company.website,
                    'company_logo': company.logo.url if company.logo else None,
                    'company_tax_number': company.tax_number,
                    'company_legal_representative': company.legal_representative,
                    'company_description': description,
                }

                # 缓存1小时
                cache.set(cache_key, company_data, 3600)
            else:
                # 返回默认值（根据语言）
                if lang_code == 'en':
                    default_name = 'BetterLaser ERP'
                    default_description = 'Enterprise Resource Planning System'
                else:
                    default_name = 'BetterLaser ERP'
                    default_description = '企业资源规划管理系统'

                company_data = {
                    'company': None,
                    'company_name': default_name,
                    'company_code': 'BLERP',
                    'company_address': '',
                    'company_phone': '',
                    'company_email': '',
                    'company_website': '',
                    'company_logo': None,
                    'company_tax_number': '',
                    'company_legal_representative': '',
                    'company_description': default_description,
                }
        except Exception:
            # 出错时返回默认值
            if lang_code == 'en':
                default_name = 'BetterLaser ERP'
                default_description = 'Enterprise Resource Planning System'
            else:
                default_name = 'BetterLaser ERP'
                default_description = '企业资源规划管理系统'

            company_data = {
                'company': None,
                'company_name': default_name,
                'company_code': 'BLERP',
                'company_address': '',
                'company_phone': '',
                'company_email': '',
                'company_website': '',
                'company_logo': None,
                'company_tax_number': '',
                'company_legal_representative': '',
                'company_description': default_description,
            }

    return company_data


def page_refresh_config(request):
    """
    向所有模板注入页面刷新配置

    配置优先级（从高到低）：
    1. 视图级别配置（在view中设置context['page_refresh_config']）
    2. 全局配置（settings.PAGE_REFRESH_CONFIG）
    3. 默认配置

    Args:
        request: HttpRequest对象

    Returns:
        dict: 页面刷新配置字典
    """
    from django.conf import settings

    # 获取全局配置
    global_config = getattr(settings, 'PAGE_REFRESH_CONFIG', {
        'enabled': False,
        'default_interval': 30,
    })

    # 尝试从视图获取覆盖配置（通过request属性）
    view_config = getattr(request, 'page_refresh_config', {})

    # 合并配置（视图配置优先）
    config = {
        'enabled': view_config.get('enabled', global_config.get('enabled', True)),
        'interval': view_config.get('interval', global_config.get('default_interval', 30)),
        'mode': view_config.get('mode', 'auto'),  # auto, manual, smart
        'preserve_state': view_config.get('preserve_state', True),
        'show_notifications': view_config.get('show_notifications', False),
        'smart_features': global_config.get('smart_features', {
            'visibility_detection': True,
            'user_activity_detection': True,
            'preserve_scroll_position': True,
        }),
    }

    return {
        'page_refresh_config': config
    }
