"""
查询优化工具模块

提供常见的数据库查询优化工具函数，减少N+1查询问题和内存占用。
"""
from django.db.models import QuerySet


def get_optimized_choices(queryset, value_field="id", label_field="name", filter_kwargs=None):
    """
    优化的下拉框数据查询 - 只查询必要字段

    Args:
        queryset: Django QuerySet
        value_field: 选项值的字段名，默认为'id'
        label_field: 选项显示文本的字段名，默认为'name'
        filter_kwargs: 额外的过滤条件字典

    Returns:
        list: 元组列表 [(value, label), ...]

    Example:
        >>> customers = get_optimized_choices(Customer.objects.all())
        >>> warehouses = get_optimized_choices(
        ...     Warehouse.objects.filter(is_active=True),
        ...     value_field='id',
        ...     label_field='name'
        ... )
    """
    if filter_kwargs:
        queryset = queryset.filter(**filter_kwargs)

    return list(
        queryset.filter(is_deleted=False)
        .only(value_field, label_field)
        .values_list(value_field, label_field)
    )


def get_optimized_choices_with_order(
    queryset, value_field="id", label_field="name", order_by=None, filter_kwargs=None
):
    """
    优化的下拉框数据查询 - 支持自定义排序

    Args:
        queryset: Django QuerySet
        value_field: 选项值的字段名
        label_field: 选项显示文本的字段名
        order_by: 排序字段列表，如 ['name', 'code']
        filter_kwargs: 额外的过滤条件字典

    Returns:
        list: 元组列表 [(value, label), ...]

    Example:
        >>> products = get_optimized_choices_with_order(
        ...     Product.objects.all(),
        ...     value_field='id',
        ...     label_field='name',
        ...     order_by=['category__name', 'name']
        ... )
    """
    if filter_kwargs:
        queryset = queryset.filter(**filter_kwargs)

    queryset = queryset.filter(is_deleted=False).only(value_field, label_field)

    if order_by:
        queryset = queryset.order_by(*order_by)

    return list(queryset.values_list(value_field, label_field))


def batch_fetch_related(queryset, *relations):
    """
    批量预加载关联对象 - 减少N+1查询

    Args:
        queryset: Django QuerySet
        *relations: 需要预加载的关联字段名称

    Returns:
        QuerySet: 添加了select_related的QuerySet

    Example:
        >>> orders = batch_fetch_related(
        ...     SalesOrder.objects.all(),
        ...     'customer',
        ...     'customer__default_payment_term',
        ...     'sales_rep'
        ... )
    """
    return queryset.select_related(*relations)


def optimize_queryset_for_list(
    queryset, select_related_fields=None, prefetch_related_fields=None, only_fields=None
):
    """
    综合优化QuerySet用于列表展示

    Args:
        queryset: Django QuerySet
        select_related_fields: select_related字段列表（ForeignKey/OneToOne）
        prefetch_related_fields: prefetch_related字段列表（ManyToOne/ManyToMany）
        only_fields: only()限制查询的字段列表

    Returns:
        QuerySet: 优化后的QuerySet

    Example:
        >>> orders = optimize_queryset_for_list(
        ...     SalesOrder.objects.all(),
        ...     select_related_fields=['customer', 'sales_rep'],
        ...     prefetch_related_fields=['items'],
        ...     only_fields=['id', 'order_number', 'customer__name', 'total_amount']
        ... )
    """
    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)

    if prefetch_related_fields:
        queryset = queryset.prefetch_related(*prefetch_related_fields)

    if only_fields:
        queryset = queryset.only(*only_fields)

    return queryset
