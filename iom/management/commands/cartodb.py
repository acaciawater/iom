'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option
from iom.models import Waarnemer, Meetpunt 
import urllib,urllib2
import json
from django.contrib.gis.geos import Point
from acacia.data.models import ProjectLocatie

class Command(BaseCommand):
    args = ''
    help = 'Downloads data from cartodb and updates time series'
    option_list = BaseCommand.option_list + (
            make_option('--pk',
                action='store',
                type = 'int',
                dest = 'pk',
                default = None,
                help = 'update single datasource'),
        )
    url = 'https://tkleinen.cartodb.com/api/v2/sql'
    sql = 'SELECT * FROM waarnemers_1'
    
    def handle(self, *args, **options):
        data = urllib.urlencode({'format': 'GeoJSON','q': self.sql})
        resp = urllib2.urlopen(url=self.url, data=data)
        data = resp.read()
        data=json.loads(data)
        project = ProjectLocatie.objects.get(pk=1) # Texel
        user = User.objects.get(pk=1) # admin
        for feature in data['features']:

            geom = feature['geometry']
            assert(geom['type'] == 'Point')
            location = Point(geom['coordinates'], srid=4326)
            location.transform(28992)
            
            props = feature['properties']
            waarnemer_id = props['waarnemer']
            sample_id = props['sampleid']
            name = 'MP%s.%d' % (waarnemer_id, sample_id)
            try:
                waarnemer = Waarnemer.objects.get(pk=waarnemer_id)
                meetpunt = waarnemer.meetpunt_set.get(name=name)
                meetpunt.location = location
                meetpunt.save()
            except Waarnemer.DoesNotExist:
                print 'Waarnemer niet gevonden: %d' % waarnemer_id
                continue
            except Meetpunt.DoesNotExist:
                meetpunt=waarnemer.meetpunt_set.create(name=name,projectlocatie=project,nummer=sample_id,location=location)
            
            series, created = meetpunt.manualseries_set.get_or_create(name='EC',defaults={'user': user})
            date = props['datum']
            value = props['ec']

            dp, created = series.datapoints.get_or_create(date=date, defaults={'value': value})
            if not created:
                if dp.value != value:
                    dp.value=value
                    dp.save(update_fields=['value'])
            print meetpunt, date, value
            