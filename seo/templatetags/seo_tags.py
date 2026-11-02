from django import template

from seo.structured_data import page_description, structured_data_script

register = template.Library()


@register.simple_tag
def seo_description(page=None):
    return page_description(page)


@register.simple_tag
def json_ld(page=None):
    return structured_data_script(page)
