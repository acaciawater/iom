'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option
from iom.models import Waarnemer, Meetpunt 
from django.contrib.gis.geos import Point
from acacia.data.models import ProjectLocatie
import csv
from dateutil import parser
from iom import util

class Command(BaseCommand):
    args = ''
    help = 'Importeer csv file met metingen'
    option_list = BaseCommand.option_list + (
            make_option('--file',
                action='store',
                dest = 'file',
                default = '/media/sf_F_DRIVE/projdirs/iom/metingen.csv',
                help = 'naam van csv bestand'),
        )
    
    def handle(self, *args, **options):
        fname = options.get('file', None)
        if not fname:
            print 'filenaam ontbreekt'
            return
        project = ProjectLocatie.objects.get(pk=1) # Texel
        user = User.objects.get(pk=1) # admin
        allseries = set()
        meetpunten = set()
        with open(fname) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                waarnemer_id = row['wnid']
                sample_id= row['locatie']
                lon = float(row['lon'])
                lat = float(row['lat'])
                oms = row['omschrijving']
                bo = row['boven/onder']
                location = Point(lon,lat,srid=4326)
                location.transform(28992)
                name = 'MP%s.%s' % (waarnemer_id, sample_id)
                if bo is not None and len(bo) > 0:
                    name += bo
                try:
                    waarnemer = Waarnemer.objects.get(pk=waarnemer_id)
                    meetpunt = waarnemer.meetpunt_set.get(name=name)
                    meetpunt.location = location
                    meetpunt.description = oms
                    meetpunt.save()
                except Waarnemer.DoesNotExist:
                    print 'Waarnemer niet gevonden: %d' % waarnemer_id
                    continue
                except Meetpunt.DoesNotExist:
                    meetpunt=waarnemer.meetpunt_set.create(name=name,projectlocatie=project,nummer=sample_id,location=location,description=oms)
                    print 'Meetpunt', meetpunt, 'aangemaakt.'
                    
                # Geleidbaarheid
                series, created = meetpunt.manualseries_set.get_or_create(name='EC_'+name,defaults={'user': user, 'type': 'scatter', 'unit': 'uS/cm'})
                if created:
                    print 'Tijdreeks EC aangemaakt voor meetpunt', meetpunt  

                date = parser.parse(row['datetime'])
                
                try:
                    value = float(row['EC'])
                except:
                    continue
                unit = row['eenheid mS of uS']
                if unit in [ 'mS', 'SAL']:
                    value *= 1000
                dp, created = series.datapoints.get_or_create(date=date, defaults={'value': value})
                if not created:
                    if dp.value != value:
                        dp.value=value
                        dp.save(update_fields=['value'])
                print meetpunt, date, 'EC', value
                allseries.add(series)
                meetpunten.add(meetpunt)
                
                # Temperatuur
                series, created = meetpunt.manualseries_set.get_or_create(name='Temp_'+name,defaults={'user': user, 'type': 'scatter', 'unit': 'oC'})
                if created:
                    print 'Tijdreeks Temp aangemaakt voor meetpunt', meetpunt  

                try:
                    value = float(row['temperatuur'])
                except:
                    continue
                
                dp, created = series.datapoints.get_or_create(date=date, defaults={'value': value})
                if not created:
                    if dp.value != value:
                        dp.value=value
                        dp.save(update_fields=['value'])
                print meetpunt, date, 'Temp', value
                allseries.add(series)
        
        print 'Updating thumbnails'
        for series in allseries:
            print series.name
            series.getproperties().update()
            series.make_thumbnail()

        for meetpunt in meetpunten:
            print meetpunt.name
            util.maak_meetpunt_thumbnail(meetpunt)
                    
