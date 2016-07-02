'''
Created on Nov 3, 2015

@author: theo
'''
from django.core.management.base import BaseCommand

from optparse import make_option
import pytz,datetime
import logging

from iom.akvo import FlowAPI
from iom.models import AkvoFlow, CartoDb, Phone

logger = logging.getLogger(__name__)

def importPhones(api,akvo):
    devices = api.get_devices()
    num = 0
    for device in devices:
        identifier=device['deviceIdentifier']
        number = device['phoneNumber']
        date = device['lastPositionDate']
        lat = device['lastKnownLat']
        lon = device['lastKnownLon']
        acc = device['lastKnownAccuracy']
        esn = device['esn']
        date=datetime.datetime.utcfromtimestamp(date/1000.0).replace(tzinfo=pytz.utc)
        try:
            lon = float(lon)
            lat = float(lat)
        except:
            logger.error('Probleem met coordinaten ({lon},{lat})'.format(lon=lon,lat=lat))
            continue
        try:
            phone = Phone.objects.get(imei=esn)
        except Phone.DoesNotExist:
            phone = Phone(imei=esn)
        phone.device_id = identifier
        phone.phone_number = number
        phone.last_contact = date
        phone.latitude = lat
        phone.longitude = lon
        phone.accuracy = acc
        phone.save()
        num += 1
    return num

class Command(BaseCommand):
    args = ''
    help = 'Importeer telefoons'
    option_list = BaseCommand.option_list + (
            make_option('--akvo',
                action='store',
                dest = 'akvo',
                default = 1,
                help = 'id van Akvoflow configuratie'),
            make_option('--cartodb',
                action='store',
                dest = 'cartodb',
                default = 1,
                help = 'id van Cartodb configuratie'),
        )

    def handle(self, *args, **options):
        
        akvo = AkvoFlow.objects.get(pk=options.get('akvo'))
        api = FlowAPI(instance=akvo.instance, key=akvo.key, secret=akvo.secret)
        #cartodb = CartoDb.objects.get(pk=options.get('cartodb'))
    
        try:
            logger.info('Telefoons ophalen')
            num = importPhones(api, akvo)
            logger.info('{num} telefoons gevonden'.format(num=num))
        
#             logger.info('Cartodb actialiseren')
#             updateCartodb(cartodb, mp)        
        except Exception as e:
            logger.exception('Probleem met importeren telefoons: %s',e)
        finally:
            pass
