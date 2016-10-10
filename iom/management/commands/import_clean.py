'''
Created on Oct 5, 2016

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from optparse import make_option
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings
from dateutil import parser
import os,pytz,datetime
import json,logging
import xlrd
import re

from acacia.data.models import ProjectLocatie
from iom import util
from iom.akvo import FlowAPI, as_timestamp
from iom.models import AkvoFlow, CartoDb, Meetpunt, Waarnemer, Alias
from iom.exif import Exif

logger = logging.getLogger(__name__)

def maak_naam(parameter,diep):
    if diep and not diep.endswith('iep'):
        diep = None
    return parameter + '_' + diep if diep else parameter

def get_or_create_waarnemer(akvoname):
    try:
        # is deze alias al geregistreerd?
        alias = Alias.objects.get(alias=akvoname)
        waarnemer = alias.waarnemer
        logger.debug('Waarnemer {name} gevonden met alias {alias}'.format(name=unicode(waarnemer),alias=alias))
    except Alias.DoesNotExist:
        # Bestaat er al een waarnemer met deze naam?
        words = akvoname.split()
        if len(words) > 1:
            voornaam = words[0]
            initialen = voornaam[0].upper()
            achternaam = words[-1].title()
            if len(words) > 2:
                tussenvoegsel = ' '.join(words[1:-1])
            else:
                tussenvoegsel = ''
            waarnemer, created = Waarnemer.objects.get_or_create(initialen=initialen, voornaam=voornaam, tussenvoegsel=tussenvoegsel, achternaam=achternaam)
        else:
            waarnemer, created = Waarnemer.objects.get_or_create(achternaam=akvoname)
        if created:
            logger.info('Waarnemer {} aangemaakt'.format(unicode(waarnemer)))
        # alias toevoegen aan waarnemer
        alias = waarnemer.alias_set.create(alias=akvoname)
        logger.info('alias {alias} toegevoegd aan waarnemer {name}'.format(alias=unicode(alias),name=unicode(waarnemer)))
    return waarnemer

def download_photo(url):
    # copy photo to local storage and rotate if necessary
    try:
        filename = os.path.basename(url)
        Exif.copyImage(url, os.path.join(settings.PHOTO_DIR,filename))
        return os.path.join(settings.PHOTO_URL,filename)
    except:
        return url
                
def importRegistrationForm(sheet,projectlocatie,user):
    meetpunten=set()
    waarnemingen=set()
    num_meetpunten = 0
    keys = [sheet.cell(0, col).value.split('|')[-1] for col in xrange(sheet.ncols)]
    for row in xrange(1,sheet.nrows):
        cells = {keys[col]: sheet.cell(row, col).value for col in xrange(sheet.ncols)}
        identifier = cells['Identifier']
        displayName = cells['Display Name']
        submitter = cells['Submitter']
        device = cells['Device identifier']
        date = parser.parse(cells['Submission Date'],dayfirst=True)
        akvowaarnemer = cells['Waarnemer']
        meetid = cells['Meetpunt ID']
        foto = cells['Maak een foto van het meetgebied']
        lat = cells['Latitude']
        lon = cells['Longitude']
        omschrijving = cells['Meetpunt omschrijving']
        num_meetpunten += 1
        try:
            location = Point(float(lon),float(lat),srid=4326)
            location.transform(28992)
        except:
            logger.error('Probleem met coordinaten {loc}. waarnemer = {waar}, meetpunt = {mp}'.format(loc=(lat,lon), waar = akvowaarnemer or submitter, mp=meetid))
            continue

        akvoname = akvowaarnemer or submitter
        waarnemer = get_or_create_waarnemer(akvoname)

        # change reference to photo from smartphone storage to amazon storage and download to this server
        if foto:
            foto = download_photo(foto)

        if meetid:
            # Gebuik waarnemer naam + meetid
            meetName = '{name} - {id}'. format(name=akvoname, id=meetid)
        else:
            meetName = displayName

        name = meetName or 'Naamloos'
        meetpunt = None
        for dup in range(10):
            try:
                meetpunt, created = waarnemer.meetpunt_set.get_or_create(identifier=identifier, defaults={
                    'name': name, 
                    'projectlocatie': projectlocatie, 
                    'location': location, 
                    'displayname': displayName, 
                    'device': device,
                    'photo_url': foto,
                    'description': omschrijving})
                break
            except Exception as e:
                logger.error('Dubbel meetpunt {mname} voor waarnemer {wname}'.format(mname=meetName, wname=unicode(waarnemer)))
                name = '{} ({})'.format(meetName, dup+1) 
                continue

        if not meetpunt:
            raise Exception('Te veel dubbele meetopunten met naam {name}'.format(name=meetName))
            
        if created:
            logger.info('Meetpunt {id} aangemaakt voor waarnemer {name}'.format(id=name,name=unicode(waarnemer)))
            meetpunten.add(meetpunt)

        #if device != 'IMPORTER':
        ec = cells['Meet EC waarde - ECOND'] 
        diep = cells['Diep of ondiep gemeten?']
        waarneming_naam = maak_naam('EC',diep)

        try:
            waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                              defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
        except Exception as e:
            logger.exception('Probleem bij toevoegen waarneming {wname} aan meetpunt {mname}'.format(wname=waarneming_naam, mname=unicode(meetpunt)))
            continue

        if created:
            logger.debug('{id}, {date}, EC={ec}'.format(id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)

        elif waarneming.waarde != ec:
            waarneming.waarde = ec
            waarneming.save()
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)
        #endif
        
    logger.info('Aantal meetpunten: {aantal}, nieuwe meetpunten: {new}'.format(aantal=num_meetpunten, new=len(meetpunten)))

    return meetpunten, waarnemingen
   
def importMonitoringForm(sheet):
    meetpunten = set()
    waarnemingen = set()
    num_waarnemingen = 0
    num_replaced = 0

    keys = [sheet.cell(0, col).value.split('|')[-1] for col in xrange(sheet.ncols)]
    for row in xrange(1,sheet.nrows):
        cells = {keys[col]: sheet.cell(row, col).value for col in xrange(sheet.ncols)}
        submitter = cells['Submitter']
        waarnemer = get_or_create_waarnemer(submitter)
        
        #find related registration form (meetpunt)
        identifier = cells['Identifier']
        try:
            meetpunt = Meetpunt.objects.get(identifier=identifier)
        except Meetpunt.DoesNotExist:
            logger.error('Meetpunt {identifier} niet gevonden voor {submitter}'.format(identifier=identifier, submitter=submitter))
            continue
        
        device = cells['Device identifier']
        date = parser.parse(cells['Submission Date'],dayfirst=True) # format: day first
        ec=cells['EC waarde - ECOND']
        foto=cells['Maak een foto van het meetgebied']
        diep=cells['Diep of ondiep']
        waarneming_naam = maak_naam('EC',diep)
        
        if foto:
            foto = download_photo(foto)

        if foto:
            # update meetpunt photo along the way..
            meetpunt.photo_url = foto
            meetpunt.save(update_fields=['photo_url'])
        try:     
        
            waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                      defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
        except Exception as ex:
            logger.exception('Probleem met toevoegen van waarneming {waar} met waarde {waarde} aan meetpunt {meetpunt}'.format(waar=waarneming_naam, waarde=ec, meetpunt=meetpunt))
            continue
        
        if created:
            logger.info('created {identifier}={mp}, {id}({date})={ec}'.format(identifier=identifier, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
            num_waarnemingen += 1
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)
        elif waarneming.waarde != ec:
            waarneming.waarde = ec
            waarneming.save()
            logger.info('updated {identifier}={mp}, {id}({date})={ec}'.format(identifier=identifier, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
            num_replaced += 1
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)
    logger.info('Aantal nieuwe metingen: {meet}, bijgewerkt: {repl}'.format(meet=num_waarnemingen,repl=num_replaced))
    return meetpunten, waarnemingen

class Command(BaseCommand):
    args = ''
    help = 'Importeer cleaned_data spreadsheet'
    option_list = BaseCommand.option_list + (
            make_option('--file',
                action='store',
                dest = 'fname',
                default='/media/sf_C_DRIVE/Users/theo/Downloads/NZG_RAW_DATA-10410916.xlsx',
                help = 'xlsx file'),
            make_option('--user',
                action='store',
                dest = 'user',
                default = 'akvo',
                help = 'user name'),
        )

    def handle(self, *args, **options):
        user = User.objects.get(username=options.get('user'))
        filename = args[0]
        logger.debug('Importing '+filename)
        locatie = None
        match = re.search('RAW_DATA\-(\d+)\.', filename)
        if match:
            surveyId = match.group(1)
            # find surveyid in akvo config
            for candidate in ProjectLocatie.objects.all():
                if surveyId == candidate.akvoflow.regform:
                    locatie = candidate
                    isRegForm = True
                    break
                if surveyId == candidate.akvoflow.monforms: 
                    locatie = candidate
                    isRegForm = False
                    break
        if not locatie:
            logger.error('Geen geregistreerde survey gevonden voor dit bestand')
            return 

        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_name('Raw Data')
        try:
            if isRegForm:
                logger.debug('Meetpuntgegevens ophalen voor {}'.format(locatie))
                mp,wn = importRegistrationForm(sheet,projectlocatie=locatie,user=user)
            else:
                logger.debug('Waarnemingen ophalen voor {}'.format(locatie))
                mp,wn=importMonitoringForm(sheet)
            #if mp:
                #logger.debug('Grafieken aanpassen')
                #util.updateSeries(mp, user)
                #logger.debug('Cartodb actualiseren')
                #cartodb = locatie.cartodb
                #util.exportCartodb(cartodb, mp)
            
            #akvo = locatie.akvoflow
            #akvo.last_update = timezone.now()
            #akvo.save()        
        except Exception as e:
            logger.exception('Probleem met verwerken nieuwe metingen: %s',e)
        finally:
            pass
