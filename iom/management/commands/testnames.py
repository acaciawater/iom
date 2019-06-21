# -*- coding: utf-8 -*-
import os
import re
import json
import logging
import string

from django.conf import settings
from django.core.management.base import BaseCommand
import requests
from requests.exceptions import HTTPError

from acacia.data.models import Project
from iom.models import Waarnemer, Meetpunt, Waarneming

logger = logging.getLogger(__name__)

def genstring(charset, length):
    ''' generate a string of length characters selected randomly from charset '''
    import random
    return ''.join([random.choice(charset) for _ in range(length)])

def genpasswd(length=8):
    ''' generate a password of length characters '''
    charset = string.ascii_letters + string.digits + '!@#$%&*+=-?.:'
    return genstring(charset,length)

def truncate(string, maxlength, ellipsis='...', position='end'):
    ''' truncate a string to maxlength characters and insert placeholder in truncated string. 
    position can be begin, end or middle '''
    
    length = len(string)
    if length <= maxlength:
        return string

    # remove trailing whitespace
    string = string.strip()
    length = len(string)
    if length <= maxlength:
        return string

    # remove all other whitespace    
    string = re.sub(r'\s','',string)
    length = len(string)
    if length <= maxlength:
        return string
    
    length2 = maxlength - len(ellipsis)
    if position == 'end':
        return string[:length2] + ellipsis
    if position == 'begin':
        return ellipsis + string[-length2:]
    left = length2/2
    right = length2-left
    return string[:left] + ellipsis + string[-right:]
    
class Command(BaseCommand):
    args = ''

    def makeSeriesName(self, meetpunt, category, maxlength=30):
        name = meetpunt.name.strip()
        if len(name) > maxlength:
            # remove everything up to 'achternaam - ' 
            tag = '{} - '.format(meetpunt.waarnemer.achternaam).lower()
            #tag = ' - '
            pos = name.lower().find(tag)
            if pos >= 0:
                name = name[pos+len(tag):]

        if category:
            length = maxlength - (len(category)+3)
            name = '{} ({})'.format(truncate(name, length, '..', position='begin'), category)
        else:
            name = truncate(name, maxlength, '..', position='begin')
        return name

    def test_series_names(self):
        for meetpunt in Meetpunt.objects.all():
            name = self.makeSeriesName(meetpunt, 'Shallow')
            if name != meetpunt.name:
                print meetpunt.name, '=>', name
                
    def handle(self, *args, **options):

        self.test_series_names()
