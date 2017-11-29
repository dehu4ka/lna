from django import template
import mistune
from net.lib import HighlightRenderer


register = template.Library()


@register.filter
def markdown(value, vendor):
    value = '```pre\n' + value + '\n```'
    renderer = HighlightRenderer(vendor)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(value)
