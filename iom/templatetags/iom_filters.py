'''
Created on Jul 8, 2015

@author: theo
'''
from django import template
#from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(is_safe=True)
def defaultif0(value,arg):
    return arg if value == 0 else value
