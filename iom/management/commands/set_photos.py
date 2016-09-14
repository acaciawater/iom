'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from iom.models import Meetpunt
from acacia.data.models import DataPoint
import logging
from iom import util

logger = logging.getLogger('akvo')

class Command(BaseCommand):
    args = ''
    help = 'set phot of meetpunt to last photo taken'

    def handle(self, *args, **options):
        for mp in Meetpunt.objects.all():
            waarnemingen = mp.waarneming_set.order_by('-datum')
            for w in waarnemingen:
                if w.foto_url:
                    if mp.photo_url != w.foto_url:
                        mp.photo_url = w.foto_url
                        mp.save()
                        print mp
                    break
            
                