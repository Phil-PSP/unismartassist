from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """Return the current query string with one parameter replaced."""
    params = request.GET.copy()
    params[field] = value
    return params.urlencode()
