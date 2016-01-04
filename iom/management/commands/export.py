'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from optparse import make_option
from iom.models import Meetpunt, CartoDb 
from iom.util import exportCartodb

class Command(BaseCommand):
    args = ''
    help = 'Exports all data to cartodb'

    def handle(self, *args, **options):
        cdb = CartoDb.objects.get(pk=1)
        exportCartodb(cdb, Meetpunt.objects.all(),'allemetingen')

        