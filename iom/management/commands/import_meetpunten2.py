'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option
from iom.models import Waarnemer, Meetpunt, CartoDb
from django.contrib.gis.geos import Point
from acacia.data.models import ProjectLocatie
import csv, logging, uuid
from dateutil import parser
from iom.util import updateSeries, updateCartodb 

logger = logging.getLogger('akvo')

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

        meetpunten = set()
        with open(fname) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                waarnemer_id = row['wnid']
                submitter = row['waarnemer']
                sample_id= row['locatie']
                lon = float(row['lon'])
                lat = float(row['lat'])
                oms = row['omschrijving']
                diep = row['boven/onder']
                ec = float(row['EC'])

                if diep == 'b': # boven
                    diep = 'Ondiep'
                elif diep in ('d', 'o'): # onder of diep
                    diep = 'Diep'
                date = parser.parse(row['datetime'])

                location = Point(lon,lat,srid=4326)
                location.transform(28992)
                name = 'MP%s.%s' % (waarnemer_id, sample_id)
                try:
                    waarnemer = Waarnemer.objects.get(pk=waarnemer_id)
                    waarnemer.akvoname = submitter.lower()
                    waarnemer.save()
                    meetpunt = waarnemer.meetpunt_set.get(name=name)
                    meetpunt.identifier = uuid.uuid4()
                    meetpunt.location = location
                    meetpunt.description = oms
                    meetpunt.save()
                except Waarnemer.DoesNotExist:
                    logging.error('Waarnemer niet gevonden: %d' % waarnemer_id)
                    continue
                except Meetpunt.DoesNotExist:
                    meetpunt=waarnemer.meetpunt_set.create(name=name,projectlocatie=project,location=location,description=oms)
                    logger.info('Meetpunt {mp} aangemaakt.'.format(mp=meetpunt))
                    
                waarnemingen = meetpunt.waarneming_set.filter(naam='EC_'+diep,datum=date)
                if waarnemingen.exists():
                    logger.warn('EC waarnemingen worden vervangen voor {locatie}, datum={date}'.format(locatie=meetpunt.name,date=date)) 
                    waarnemingen.delete()
                meetpunt.waarneming_set.create(naam='EC_'+diep if diep else 'EC', waarnemer=waarnemer, datum=date, device='acacia', waarde=ec, opmerking='', eenheid='uS/cm' )
                logger.debug('EC_{diep}, {date}, EC={ec}'.format(diep=diep, date=date, ec=ec))

                meetpunten.add(meetpunt)
                
        updateSeries(meetpunten, user)                
        
        #cartodb = CartoDb.objects.get(name='Texel Meet')
        #cartodb.runsql('DELETE FROM waarnemingen')
        #updateCartodb(cartodb, meetpunten)        