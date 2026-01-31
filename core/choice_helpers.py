"""
Choice Options Helper Functions
视图辅助函数 - 用于在视图中轻松获取动态选项
"""
from core.models_choice import ChoiceOption


def get_choice_context():
    """
    获取所有常用选项的上下文字典。
    在视图中一次性获取所有需要的选项，传递给模板使用。

    返回包含所有选项的字典，可直接传递给template context。

    用法:
        context = get_choice_context()
        context.update({'customer': customer, ...})
        return render(request, 'template.html', context)
    """
    return {
        # 客户相关
        'customer_levels': ChoiceOption.get_choices('customer_level'),
        'customer_statuses': ChoiceOption.get_choices('customer_status'),
        'address_types': ChoiceOption.get_choices('address_type'),
        'visit_types': ChoiceOption.get_choices('visit_type'),
        'visit_purposes': ChoiceOption.get_choices('visit_purpose'),
        'credit_types': ChoiceOption.get_choices('credit_type'),

        # 供应商相关
        'supplier_levels': ChoiceOption.get_choices('supplier_level'),
        'contact_types': ChoiceOption.get_choices('contact_type'),
        'evaluation_periods': ChoiceOption.get_choices('evaluation_period'),

        # 产品相关
        'product_types': ChoiceOption.get_choices('product_type'),
        'product_statuses': ChoiceOption.get_choices('product_status'),
        'unit_types': ChoiceOption.get_choices('unit_type'),
        'attribute_types': ChoiceOption.get_choices('attribute_type'),
        'price_types': ChoiceOption.get_choices('price_type'),

        # 库存相关
        'warehouse_types': ChoiceOption.get_choices('warehouse_type'),
        'adjustment_types': ChoiceOption.get_choices('adjustment_type'),
        'adjustment_reasons': ChoiceOption.get_choices('adjustment_reason'),
        'count_types': ChoiceOption.get_choices('count_type'),
        'transaction_types': ChoiceOption.get_choices('transaction_type'),

        # 财务相关
        'payment_terms': ChoiceOption.get_choices('payment_terms'),
    }


def get_customer_context():
    """
    获取客户管理相关的选项。
    针对客户模块优化的上下文获取函数。
    """
    return {
        'customer_levels': ChoiceOption.get_choices('customer_level'),
        'customer_statuses': ChoiceOption.get_choices('customer_status'),
        'address_types': ChoiceOption.get_choices('address_type'),
        'visit_types': ChoiceOption.get_choices('visit_type'),
        'visit_purposes': ChoiceOption.get_choices('visit_purpose'),
        'credit_types': ChoiceOption.get_choices('credit_type'),
        'payment_terms': ChoiceOption.get_choices('payment_terms'),
    }


def get_supplier_context():
    """获取供应商管理相关的选项"""
    return {
        'supplier_levels': ChoiceOption.get_choices('supplier_level'),
        'contact_types': ChoiceOption.get_choices('contact_type'),
        'evaluation_periods': ChoiceOption.get_choices('evaluation_period'),
        'payment_terms': ChoiceOption.get_choices('payment_terms'),
    }


def get_product_context():
    """获取产品管理相关的选项"""
    return {
        'product_types': ChoiceOption.get_choices('product_type'),
        'product_statuses': ChoiceOption.get_choices('product_status'),
        'unit_types': ChoiceOption.get_choices('unit_type'),
        'attribute_types': ChoiceOption.get_choices('attribute_type'),
        'price_types': ChoiceOption.get_choices('price_type'),
    }


def get_inventory_context():
    """获取库存管理相关的选项"""
    return {
        'warehouse_types': ChoiceOption.get_choices('warehouse_type'),
        'adjustment_types': ChoiceOption.get_choices('adjustment_type'),
        'adjustment_reasons': ChoiceOption.get_choices('adjustment_reason'),
        'count_types': ChoiceOption.get_choices('count_type'),
        'transaction_types': ChoiceOption.get_choices('transaction_type'),
    }


# 便捷函数 - 单个分类快速获取
def get_customer_levels():
    """获取客户等级选项"""
    return ChoiceOption.get_choices('customer_level')


def get_supplier_levels():
    """获取供应商等级选项"""
    return ChoiceOption.get_choices('supplier_level')


def get_payment_terms():
    """获取付款方式选项"""
    return ChoiceOption.get_choices('payment_terms')


def get_choice_label(category, code):
    """
    获取选项的显示标签。

    Args:
        category: 选项分类，如 'customer_level'
        code: 选项代码，如 'A'

    Returns:
        显示标签，如 'A级客户'，如果未找到则返回代码本身

    用法:
        label = get_choice_label('customer_level', 'A')  # 返回 'A级客户'
    """
    return ChoiceOption.get_label(category, code)
