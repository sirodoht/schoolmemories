from django import template

from main import country

register = template.Library()


@register.filter
def country_name(country_code):
    return country.COUNTRIES.get(country_code, country_code)
