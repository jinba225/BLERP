# Sales app


# ============================================
# 兼容性导入：打印模板已移至 core 模块
# ============================================
def __getattr__(name):
    """延迟导入以避免循环依赖"""
    if name == "PrintTemplate":
        from core.models import PrintTemplate

        return PrintTemplate
    elif name == "DefaultTemplateMapping":
        from core.models import DefaultTemplateMapping

        return DefaultTemplateMapping
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
