'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from optparse import make_option
from iom.models import Meetpunt, CartoDb 
import urllib,urllib2
import time
from iom.util import updateCartodb

class Command(BaseCommand):
    args = ''
    help = 'Updates data in cartodb'
    option_list = BaseCommand.option_list + (
            make_option('--pk',
                action='store',
                type = 'int',
                dest = 'pk',
                default = None,
                help = 'update single meetpunt'),
        )
        
    def handle(self, *args, **options):
        cdb = CartoDb.objects.get(pk=1)
        #cdb.runsql('DELETE FROM waarnemingen')
        updateCartodb(cdb, Meetpunt.objects.all())

        