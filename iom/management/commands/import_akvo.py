'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from optparse import make_option
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings
import os,pytz,datetime
import logging

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
        # Bestaat er al een waarnemer met deze achternaam?
        words = akvoname.split(r'\s+')
        if len(words) > 1:
            achternaam = words[-1]
            tussenvoegsel = ' '.join(words[:-1])
            waarnemer, created = Waarnemer.objects.get_or_create(tussenvoegsel=tussenvoegsel, achternaam=achternaam)
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
            
def importAkvoRegistration(api,akvo,projectlocatie,user):
    surveyId = akvo.regform
    meetpunten=set()
    num_meetpunten = 0
    
    beginDate=as_timestamp(akvo.last_update)
    instances = api.get_registration_instances(surveyId,beginDate=beginDate).items()
    for key,instance in instances:
        identifier=instance['surveyedLocaleIdentifier']
        displayName = instance['surveyedLocaleDisplayName']
        submitter = instance['submitterName']
        device = instance['deviceIdentifier']
        date=instance['collectionDate']
        date=datetime.datetime.utcfromtimestamp(date/1000.0).replace(tzinfo=pytz.utc)
        answers = api.get_answers(instance['keyId'])
        akvowaarnemer = api.get_answer(answers,questionID='2050946')
        meetid = api.get_answer(answers,questionID='6040925')
        foto = api.get_answer(answers,questionID='8070919')
        geoloc = api.get_answer(answers,questionID='9070917')
        omschrijving = api.get_answer(answers,questionID='1040924')
        num_meetpunten += 1
        try:
            lat,lon,elev,code = geoloc.split('|')
            location = Point(float(lon),float(lat),srid=4326)
            location.transform(28992)
        except:
            logger.error('Probleem met coordinaten {loc}'.format(loc=geoloc))
            continue

        akvoname = akvowaarnemer or submitter
        waarnemer = get_or_create_waarnemer(akvoname)

        # change reference to photo from smartphone storage to amazon storage and download to this server
        if foto:
            foto = download_photo(os.path.join(akvo.storage,os.path.basename(foto)))

        if meetid:
            # Gebuik waarnemer naam + meetid
            meetName = '{name} - {id}'. format(name=akvoname, id=meetid)
        else:
            meetName = displayName
        try:
            meetpunt, created = waarnemer.meetpunt_set.get_or_create(identifier=identifier, defaults={
                'name': meetName, 
                'projectlocatie': projectlocatie, 
                'location': location, 
                'displayname': displayName, 
                'device': device,
                'photo_url': foto,
                'description': omschrijving})
        except Exception as e:
            # acacia.data.models.meetlocatie probably exists
            try:
                meetpunt = Meetpunt.objects.get(name=meetName, projectlocatie=projectlocatie)
                meetpunt.identifier = identifier
                meetpunt.displayname = displayName
                meetpunt.device = device
                meetpunt.identifier = identifier
                meetpunt.photo_url = foto
                meetpunt.save()
                meetpunten.add(meetpunt)
                created = True
            except:
                logger.exception('Probleem bij toevoegen meetpunt {mname} aan waarnemer {wname}'.format(mname=meetName, wname=unicode(waarnemer)))
                continue

        if created:
            logger.info('Meetpunt {id} aangemaakt voor waarnemer {name}'.format(id=meetName,name=unicode(waarnemer)))
            meetpunten.add(meetpunt)

        if device != 'IMPORTER':
            ec = api.get_answer(answers,questionID='3020916')
            diep = api.get_answer(answers,questionID='6060916')
            waarneming_naam = maak_naam('EC',diep)
    
            try:
                waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                                  defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
            except Exception as e:
                logger.exception('Probleem bij toevoegen waarneming {wname} aan meetpunt {mname}'.format(wname=waarneming_naam, mname=unicode(meetpunt)))
                continue
    
            if created:
                logger.debug('{id}, {date}, EC={ec}'.format(id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
                meetpunten.add(meetpunt)
    
            elif int(waarneming.waarde) != int(ec):
                waarneming.waarde = ec
                waarneming.save()
                meetpunten.add(meetpunt)
        
    logger.info('Aantal nieuwe meetpunten: {punt}'.format(punt=num_meetpunten))

    return meetpunten
   
def importAkvoMonitoring(api,akvo):
    meetpunten = set()
    num_waarnemingen = 0
    num_replaced = 0

    beginDate = as_timestamp(akvo.last_update)
    for surveyId in [f.strip() for f in akvo.monforms.split(',')]:
        survey = api.get_survey(surveyId)
        instances,meta = api.get_survey_instances(surveyId=surveyId,beginDate=beginDate)
        while instances:
            for instance in instances:
                submitter = instance['submitterName']
                waarnemer = get_or_create_waarnemer(submitter)
                
                #find related registration form (meetpunt)
                localeId = instance['surveyedLocaleIdentifier']
                try:
                    meetpunt = Meetpunt.objects.get(identifier=localeId)
                except Meetpunt.DoesNotExist:
                    logger.error('Meetpunt {locale} niet gevonden voor {submitter}'.format(locale=localeId, submitter=submitter))
                    continue
                
                device = instance['deviceIdentifier']
                date=instance['collectionDate']
                date=datetime.datetime.utcfromtimestamp(date/1000.0).replace(tzinfo=pytz.utc)

                answers = api.get_answers(instance['keyId'])
                ec=api.get_answer(answers,questionID='2060924')
                foto=api.get_answer(answers,questionID='5040929')
                diep=api.get_answer(answers,questionID='7080929')
                waarneming_naam = maak_naam('EC',diep)
                
                if foto:
                    foto = download_photo(os.path.join(akvo.storage,os.path.basename(foto)))
        
                if foto and not meetpunt.photo_url:
                    # update meetpunt along the way..
                    meetpunt.photo_url = foto
                    meetpunt.save(update_fields=['photo_url'])
                     
                waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                              defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
                if created:
                    logger.info('{locale}={mp}, {id}({date})={ec}'.format(locale=localeId, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
                    num_waarnemingen += 1
                    meetpunten.add(meetpunt)
                elif int(waarneming.waarde) != int(ec):
                    waarneming.waarde = ec
                    waarneming.save()
                    logger.info('{locale}={mp}, {id}({date})={ec}'.format(locale=localeId, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
                    num_replaced += 1
                    meetpunten.add(meetpunt)
            instances,meta = api.get_survey_instances(surveyId=surveyId, beginDate=beginDate, since=meta['since'])
    logger.info('Aantal nieuwe metingen: {meet}, bijgewerkt: {repl}'.format(meet=num_waarnemingen,repl=num_replaced))
    return meetpunten

class Command(BaseCommand):
    args = ''
    help = 'Importeer metingen vanuit akvo flow'
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
            make_option('--project',
                action='store',
                dest = 'proj',
                default = 1,
                help = 'id van project locatie'),
            make_option('--user',
                action='store',
                dest = 'user',
                default = 'akvo',
                help = 'user name'),
        )

    def handle(self, *args, **options):
        
        akvo = AkvoFlow.objects.get(pk=options.get('akvo'))
        api = FlowAPI(instance=akvo.instance, key=akvo.key, secret=akvo.secret)
        cartodb = CartoDb.objects.get(pk=options.get('cartodb'))
    
        project = ProjectLocatie.objects.get(pk=options.get('proj'))
        user = User.objects.get(username=options.get('user'))

        try:
            logger.debug('Meetpuntgegevens ophalen')
            mp = importAkvoRegistration(api, akvo, projectlocatie=project,user=user)
            logger.debug('Waarnemingen ophalen')
            mp.update(importAkvoMonitoring(api, akvo))
            
            if mp:
                logger.debug('Grafieken aanpassen')
                util.updateSeries(mp, user)
                logger.debug('Cartodb actualiseren')
                util.updateCartodb(cartodb, mp)
            
            akvo.last_update = timezone.now()
            akvo.save()        
        except Exception as e:
            logger.exception('Probleem met verwerken nieuwe EC metingen: %s',e)
        finally:
            pass
