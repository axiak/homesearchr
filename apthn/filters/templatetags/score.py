from django import template

register = template.Library()

@register.filter
def scorize(value):
    return '%d%%' % (100 * value)

