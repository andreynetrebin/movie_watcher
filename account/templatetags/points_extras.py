# your_app/templatetags/points_extras.py
from django import template

register = template.Library()

@register.filter
def sum_points(entries):
    """Суммирует points из списка записей"""
    try:
        return sum(entry.points for entry in entries)
    except (AttributeError, TypeError):
        return 0

@register.filter
def calc_day_total(entries):
    """Альтернативное название для sum_points"""
    return sum_points(entries)

# Дополнительные полезные фильтры для points
@register.filter
def positive_points(entries):
    """Возвращает только положительные операции"""
    return [entry for entry in entries if entry.points > 0]

@register.filter
def negative_points(entries):
    """Возвращает только отрицательные операции"""
    return [entry for entry in entries if entry.points < 0]