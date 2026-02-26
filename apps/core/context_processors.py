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
    cache_key = f"active_company_{lang_code}"

    # 尝试从缓存获取
    company_data = cache.get(cache_key)

    if company_data is None:
        try:
            company = (
                Company.objects.filter(is_active=True)
                .select_related("created_by", "updated_by")
                .first()
            )

            if company:
                # 根据语言选择描述
                if lang_code == "en":
                    description = company.description_en or company.description
                else:
                    description = company.description

                company_data = {
                    "company": company,
                    "company_name": company.name,
                    "company_code": company.code,
                    "company_address": company.address,
                    "company_phone": company.phone,
                    "company_email": company.email,
                    "company_website": company.website,
                    "company_logo": company.logo.url if company.logo else None,
                    "company_tax_number": company.tax_number,
                    "company_legal_representative": company.legal_representative,
                    "company_description": description,
                }

                # 缓存1小时
                cache.set(cache_key, company_data, 3600)
            else:
                # 返回默认值（根据语言）
                if lang_code == "en":
                    default_name = "BetterLaser ERP"
                    default_description = "Enterprise Resource Planning System"
                else:
                    default_name = "BetterLaser ERP"
                    default_description = "企业资源规划管理系统"

                company_data = {
                    "company": None,
                    "company_name": default_name,
                    "company_code": "BLERP",
                    "company_address": "",
                    "company_phone": "",
                    "company_email": "",
                    "company_website": "",
                    "company_logo": None,
                    "company_tax_number": "",
                    "company_legal_representative": "",
                    "company_description": default_description,
                }
        except Exception:
            # 出错时返回默认值
            if lang_code == "en":
                default_name = "BetterLaser ERP"
                default_description = "Enterprise Resource Planning System"
            else:
                default_name = "BetterLaser ERP"
                default_description = "企业资源规划管理系统"

            company_data = {
                "company": None,
                "company_name": default_name,
                "company_code": "BLERP",
                "company_address": "",
                "company_phone": "",
                "company_email": "",
                "company_website": "",
                "company_logo": None,
                "company_tax_number": "",
                "company_legal_representative": "",
                "company_description": default_description,
            }

    return company_data
