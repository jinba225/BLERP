"""
Custom template filters for the ERP system.
"""
from decimal import Decimal

from django import template

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
