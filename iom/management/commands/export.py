'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from optparse import make_option
from iom.models import Meetpunt, CartoDb 
from iom.util import exportCartodb
from acacia.data.models import ProjectLocatie

class Command(BaseCommand):
    args = ''
    help = 'Exports all data to cartodb'

    def handle(self, *args, **options):
        for p in ProjectLocatie.objects.all():
            mps = [m.meetpunt for m in p.meetlocatie_set.all()]
            exportCartodb(p.cartodb, mps)

        