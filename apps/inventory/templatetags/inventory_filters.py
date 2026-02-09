"""
Custom template filters for inventory app.
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name="mul")
def multiply(value, arg):
    """
    Multiply two values.
    Usage: {{ value|mul:arg }}
    """
    try:
        if value is None or arg is None:
            return Decimal("0")
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return Decimal("0")


@register.filter(name="sub")
def subtract(value, arg):
    """
    Subtract arg from value.
    Usage: {{ value|sub:arg }}
    """
    try:
        if value is None or arg is None:
            return 0
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name="percentage")
def percentage(value, total):
    """
    Calculate percentage.
    Usage: {{ value|percentage:total }}
    """
    try:
        if total is None or float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
