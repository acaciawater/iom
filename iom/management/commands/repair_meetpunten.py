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
    help = 'foreign key to chart check'

    def handle(self, *args, **options):
        for mp in Meetpunt.objects.all():
            try:
                chart = mp.chart.name
            except:
                print mp
                mp.chart = None
                mp.save()
        for dp in DataPoint.objects.all():
            try:
                s = dp.series
            except:
                print dp.series_id, dp
                dp.delete()
            