from django import template
import mistune
from net.lib import HighlightRenderer
from django.utils.safestring import mark_safe
import re


register = template.Library()


@register.filter
def markdown(value, vendor):
    value = '```pre\n' + value + '\n```'
    renderer = HighlightRenderer(vendor)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(value)


def ireplace(old, repl, text):
    return re.sub('(?i)'+re.escape(old), lambda m: repl, text)


@register.filter(is_safe=False)
def config_search(config, search):
    result = ''
    config_list = config.splitlines(keepends=True)  # List with config lines
    lines_num = len(config_list)

    for i in range(0, lines_num - 1):
        if config_list[i].upper().find(search.upper()) != -1:
            result += '...\n'
            if i >= 2:
                result += config_list[i-2]
            if i >= 1:
                result += config_list[i-1]
            # highlighting search
            # result += config_list[i].replace(search, '<strong>' + search + '</strong>')
            # result += ireplace(search, '<strong>' + search + '</strong>', config_list[i])
            result += config_list[i]
            if i <= lines_num - 2:
                result += config_list[i+1]
            if i <= lines_num - 1:
                result += config_list[i+2]
            result += '...\n'
    # result = mark_safe('<pre><code>' + result + '</code></pre>')

    result = markdown(result, 'Cisco')
    result = ireplace(search, '<span class="cp">' + search + '</span>', result)
    # return result
    return mark_safe(result)
