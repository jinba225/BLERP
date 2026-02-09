"""
Custom template filters for the ERP system.
"""
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from decimal import Decimal
from datetime import date, datetime
import json

register = template.Library()


@register.filter(name="mul")
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|mul:arg }}
    """
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, ArithmeticError):
        return 0


@register.filter(name="div")
def divide(value, arg):
    """
    Divide the value by the argument.
    Usage: {{ value|div:arg }}
    """
    try:
        if value is None or arg is None or arg == 0:
            return 0
        return Decimal(str(value)) / Decimal(str(arg))
    except (ValueError, TypeError, ArithmeticError):
        return 0


@register.filter(name="percentage")
def percentage(value, decimals=2):
    """
    Format value as percentage.
    Usage: {{ value|percentage }}
    """
    try:
        if value is None:
            return "0%"
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter(name="days_until")
def days_until(target_date):
    """
    Calculate days until target date from today.
    Returns negative value if date is in the past.
    Usage: {{ due_date|days_until }}
    """
    try:
        if not target_date:
            return 0

        # Convert to date if it's datetime
        if isinstance(target_date, datetime):
            target_date = target_date.date()

        today = date.today()
        delta = target_date - today
        return delta.days
    except (ValueError, TypeError, AttributeError):
        return 0


@register.filter(name="days_between")
def days_between(start_date, end_date):
    try:
        if not start_date or not end_date:
            return 0

        # Normalize to date
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        return (end_date - start_date).days
    except Exception:
        return 0


@register.filter(name="abs")
def absolute_value(value):
    """
    Return the absolute value of the number.
    Usage: {{ value|abs }}
    """
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value


@register.filter(name="js")
def to_javascript(value):
    """
    Convert Python value to JavaScript-compatible JSON string.
    Handles Python booleans (True/False) to JavaScript (true/false).
    Usage: {{ python_dict|js }}
    """
    try:
        # 使用DjangoJSONEncoder来正确处理所有Python类型
        # 使用mark_safe防止HTML转义
        return mark_safe(json.dumps(value, cls=DjangoJSONEncoder))
    except (TypeError, ValueError):
        return mark_safe("{}")
