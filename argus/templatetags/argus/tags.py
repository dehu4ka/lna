import re

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from net.models import OnlineStatus
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.simple_tag(takes_context=True)
def active_url(context, url):
    try:
        pattern = '^%s$' % reverse(url)
    except NoReverseMatch:
        pattern = url

    path = context['request'].path
#    return "class='active'" if re.search(pattern, path) else ''
    return "active" if re.search(pattern, path) else ''


@register.filter(name='status_badge')
def status_badge(status):
    begin = '<span class="badge badge-pill '
    middle = '">'
    end = '</span>'
    if status == 'выведено из эксплуатации':
        return mark_safe(begin + "badge-danger" + middle + "выведено" + end)
    if status == 'ЗИП':
        return mark_safe(begin + "badge-info" + middle + status + end)
    if status == 'монтаж':
        return mark_safe(begin + "badge-primary" + middle + status + end)
    if status == 'проект':
        return mark_safe(begin + "badge-info" + middle + status + end)
    if status == 'ремонт':
        return mark_safe(begin + "badge-warning" + middle + status + end)
    if status == 'тест':
        return mark_safe(begin + "badge-default" + middle + status + end)
    if status == 'эксплуатация':
        return mark_safe(begin + "badge-success" + middle + "экспл" +  end)

    return begin + "badge-default" + middle + status + end

# Very ineffective way to show online status
@register.filter(name='online_status')
def online_status(id):
    try:
        OnlineStatus.objects.get(pk=id)
        return mark_safe('<i class="fa fa-check text-success"></i>')
    except ObjectDoesNotExist:
        return mark_safe('<i class="fa fa-times text-danger"></i>')
