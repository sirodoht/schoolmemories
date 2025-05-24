from django import template

from main import country, models

register = template.Library()


@register.filter
def country_name(country_code):
    return country.COUNTRIES.get(country_code, country_code)


@register.filter
def gender_name(gender_code):
    gender_choices = dict(models.Memory.GENDER_CHOICES)
    return gender_choices.get(gender_code, gender_code)


@register.filter
def school_type_name(school_type_code):
    school_type_choices = dict(models.Memory.SCHOOL_TYPE_CHOICES)
    return school_type_choices.get(school_type_code, school_type_code)
