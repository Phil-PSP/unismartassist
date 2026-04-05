"""Custom template tags for students app"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dict by key in templates"""
    return dictionary.get(key, [])
