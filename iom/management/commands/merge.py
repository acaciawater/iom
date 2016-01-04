'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from iom.models import Meetpunt
import logging
from iom import util

logger = logging.getLogger('akvo')

class Command(BaseCommand):
    args = ''
    help = 'handmetingen samenvoegen'

    def handle(self, *args, **options):
        for target in Meetpunt.objects.exclude(device=''):
            mps = util.zoek_meetpunten(target.location)
            if len(mps)>1:
                for mp in mps:
                    if mp.pk != target.pk and mp.device == '':
                        print unicode(target), '<=', unicode(mp)
                        for w in mp.waarneming_set.all():
                            w.locatie = target
                            try:
                                w.save()
                            except:
                                pass
                        mp.delete()
