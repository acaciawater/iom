'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings
import os,pytz,datetime
import logging

from acacia.data.models import ProjectLocatie
from iom import util
from iom.akvo2 import FlowAPI, parser
from iom.models import Meetpunt, Waarnemer, Alias
from iom.exif import Exif

logger = logging.getLogger(__name__)

#default number of days back for API requests
DAYSBACK = 7

def maak_naam(parameter,diep):
    if diep and not diep.endswith('iep'):
        diep = None
    return parameter + '_' + diep if diep else parameter

def get_or_create_waarnemer(akvoname):
    try:
        # is deze alias al geregistreerd?
        alias = Alias.objects.get(alias=akvoname)
        waarnemer = alias.waarnemer
        logger.debug(u'Waarnemer {name} gevonden met alias {alias}'.format(name=unicode(waarnemer),alias=alias))
    except Alias.DoesNotExist:
        # Bestaat er al een waarnemer met deze naam?
        words = akvoname.split()
        if len(words) > 1:
            voornaam = words[0].title()
            initialen = voornaam[0]
            achternaam = words[-1].title()
            if len(words) > 2:
                tussenvoegsel = ' '.join(words[1:-1])
            else:
                tussenvoegsel = ''
            waarnemer, created = Waarnemer.objects.get_or_create(initialen=initialen, voornaam=voornaam, tussenvoegsel=tussenvoegsel, achternaam=achternaam)
        else:
            waarnemer, created = Waarnemer.objects.get_or_create(achternaam=akvoname)
        if created:
            logger.info(u'Waarnemer {} aangemaakt'.format(unicode(waarnemer)))
        # alias toevoegen aan waarnemer
        alias = waarnemer.alias_set.create(alias=akvoname)
        logger.info(u'alias {alias} toegevoegd aan waarnemer {name}'.format(alias=unicode(alias),name=unicode(waarnemer)))
    return waarnemer

def download_photo(url):
    # copy photo to local storage and rotate if necessary
    try:
        filename = os.path.basename(url)
        Exif.copyImage(url, os.path.join(settings.PHOTO_DIR,filename))
        return os.path.join(settings.PHOTO_URL,filename)
    except:
        return url
                
def importAkvoRegistration(api,akvo,projectlocatie,user,days):
    meetpunten=set()
    waarnemingen=set()
    if not akvo.surveyid:
        logger.warning(u'No survey id for akvo configuration {}'.format(akvo))
        return meetpunten, waarnemingen 
    if not akvo.regform:
        logger.warning(u'No registration form for akvo configuration {}'.format(akvo))
        return meetpunten, waarnemingen
    questions = api.get_questions(akvo.surveyid,akvo.regform) 
    num_meetpunten = 0
    beginDate=akvo.last_update + datetime.timedelta(days=-days) if days else None
    instances = api.get_form_instances(akvo.surveyid, akvo.regform, beginDate=beginDate)
    for instance in instances:
        identifier=instance['identifier']
        displayName = instance['displayName']
        submitter = instance['submitter']
        device = instance['deviceIdentifier']
        date=instance['submissionDate']
        date=parser.parse(date).replace(tzinfo=pytz.utc)
        answers = api.get_answers(instance, questions)
        akvowaarnemer = api.get_answer(answers,questions,text='Waarnemer')
        meetid = api.get_answer(answers,questions,text='Meetpunt ID')
        foto = api.get_answer(answers,questions,text='Maak een foto van het meetgebied')
        geoloc = api.get_answer(answers,questions,text='Geolocatie')
        omschrijving = api.get_answer(answers,questions,text='Meetpunt omschrijving')
        num_meetpunten += 1
        try:
            lon,lat=geoloc
            location = Point(float(lon),float(lat),srid=4326)
            location.transform(28992)
        except:
            logger.error(u'Probleem met coordinaten {loc}. waarnemer = {waar}, meetpunt = {mp}'.format(loc=geoloc, waar = akvowaarnemer or submitter, mp=meetid))
            continue

        akvoname = akvowaarnemer or submitter
        waarnemer = get_or_create_waarnemer(akvoname)

        # change reference to photo from smartphone storage to amazon storage and download to this server
        if foto:
#             foto = download_photo(os.path.join(akvo.storage,os.path.basename(foto)))
            foto = download_photo(foto)

        if meetid:
            # Gebuik waarnemer naam + meetid
            meetName = '{name} - {id}'. format(name=akvoname, id=meetid)
        else:
            meetName = displayName
        name = meetName
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
                logger.error(u'Dubbel meetpunt {mname} voor waarnemer {wname}. Error={error}'.format(mname=name, wname=unicode(waarnemer), error=e))
                name = '{} ({})'.format(meetName, dup+1) 
                continue
        if not meetpunt:
            raise Exception(u'Te veel dubbele meetpunten met naam {name}'.format(name=meetName))

        if created:
            logger.info(u'Meetpunt {id} aangemaakt voor waarnemer {name}'.format(id=meetName,name=unicode(waarnemer)))
            meetpunten.add(meetpunt)

        #if device != 'IMPORTER':
        ec = api.get_answer(answers,questions,text='Meet EC waarde - ECOND') 
        diep = api.get_answer(answers,questions,text='Diep of ondiep gemeten?')
        waarneming_naam = maak_naam('EC',diep)

        try:
            waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                              defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
        except Exception as e:
            logger.exception(u'Probleem bij toevoegen waarneming {wname} aan meetpunt {mname}'.format(wname=waarneming_naam, mname=unicode(meetpunt)))
            continue

        if created:
            logger.debug(u'{id}, {date}, EC={ec}'.format(id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)

        else:#if waarneming.waarde != ec:
            waarneming.waarde = ec
            waarneming.save()
            waarnemingen.add(waarneming)
            meetpunten.add(meetpunt)
        #endif
        
    logger.info(u'Aantal meetpunten: {aantal}, nieuwe meetpunten: {new}'.format(aantal=num_meetpunten, new=len(meetpunten)))

    return meetpunten, waarnemingen
   
def importAkvoMonitoring(api,akvo,days):
    meetpunten = set()
    waarnemingen = set()
    num_waarnemingen = 0
    num_replaced = 0

    if not akvo.surveyid:
        logger.warning(u'No survey id for akvo configuration {}'.format(akvo))
        return meetpunten, waarnemingen 
    if not akvo.regform:
        logger.warning(u'No registration form for akvo configuration {}'.format(akvo))
        return meetpunten, waarnemingen
    if not akvo.monforms:
        logger.warning(u'No monitoring forms for akvo configuration {}'.format(akvo))
        return meetpunten, waarnemingen

    beginDate=akvo.last_update + datetime.timedelta(days=-days) if days else None
    for formid in [f.strip() for f in akvo.monforms.split(',')]:
        questions = api.get_questions(akvo.surveyid,formid) 
        instances = api.get_form_instances(akvo.surveyid, formid, beginDate=beginDate)
        for instance in instances:

            identifier=instance['identifier']
            displayName = instance['displayName']
            submitter = instance['submitter']
            device = instance['deviceIdentifier']
            date=instance['submissionDate']
            date=parser.parse(date).replace(tzinfo=pytz.utc)
            answers = api.get_answers(instance, questions)

            waarnemer = get_or_create_waarnemer(submitter)
            
            #find related registration form (meetpunt)
            try:
                meetpunt = Meetpunt.objects.get(identifier=identifier)
            except Meetpunt.DoesNotExist:
                logger.error(u'Meetpunt {locale} niet gevonden voor {submitter}'.format(locale=identifier, submitter=submitter))
                continue
            
            foto=api.get_answer(answers,questions,text='Maak een foto van het meetgebied')
            diep=api.get_answer(answers,questions,text='Diep of ondiep')
            waarneming_naam = maak_naam('EC',diep)
            
            if foto:
                foto = download_photo(foto)
    
            if foto:
                # update meetpunt photo along the way..
                meetpunt.photo_url = foto
                meetpunt.save(update_fields=['photo_url'])
            try:
                answer=api.get_answer(answers,questions,text='EC waarde - ECOND')
                ec = answer
                if isinstance(answer, dict):
                    if 'result' in answer:
                        for result in answer['result']:
                            if u'Electrical Conductivity' in result['name']:
                                ec = result['value']
                                break
                
                waarneming, created = meetpunt.waarneming_set.get_or_create(naam=waarneming_naam, waarnemer=waarnemer, datum=date, 
                                          defaults = {'waarde': ec, 'device': device, 'opmerking': '', 'foto_url': foto, 'eenheid': 'uS/cm'})
            except Exception as ex:
                logger.exception(u'Probleem met toevoegen van waarneming {waar} met waarde {waarde} aan meetpunt {meetpunt}'.format(waar=waarneming_naam, waarde=ec, meetpunt=meetpunt))
                continue
            
            if created:
                logger.debug(u'created {locale}={mp}, {id}({date})={ec}'.format(locale=identifier, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
                num_waarnemingen += 1
                waarnemingen.add(waarneming)
                meetpunten.add(meetpunt)
            elif waarneming.waarde != ec:
                waarneming.waarde = ec
                waarneming.save()
                logger.debug(u'updated {locale}={mp}, {id}({date})={ec}'.format(locale=identifier, mp=unicode(meetpunt), id=waarneming.naam, date=waarneming.datum, ec=waarneming.waarde))
                num_replaced += 1
                waarnemingen.add(waarneming)
                meetpunten.add(meetpunt)
    logger.info(u'Aantal nieuwe metingen: {meet}, bijgewerkt: {repl}'.format(meet=num_waarnemingen,repl=num_replaced))
    return meetpunten, waarnemingen

class Command(BaseCommand):
    args = ''
    help = 'Importeer metingen vanuit akvo flow'
    
    def add_arguments(self, parser):
        
        parser.add_argument('-p','--project',
                action='store',
                dest = 'proj',
                default = None,
                help = 'id van project locatie')
        
        parser.add_argument('-u','--user',
                action='store',
                dest = 'user',
                default = 'akvo',
                help = 'user name')

        parser.add_argument('-a','--all',
                action='store_true',
                dest = 'all',
                default = False,
                help = 'user name')

    def handle(self, *args, **options):
        
        user = User.objects.get(username=options.get('user'))
        pk=options.get('proj')
        if pk:
            locaties = ProjectLocatie.objects.filter(pk=pk)
        else:
            locaties = ProjectLocatie.objects.all()
            
        _all = options.get('all')
        days = None if _all else DAYSBACK
        for locatie in locaties:
            cartodb = locatie.cartodb
            for akvo in locatie.akvoflow_set.all():
#                 api = FlowAPI(instance=akvo.instance, key=akvo.key, secret=akvo.secret)
                api = FlowAPI()
                api.authenticate(username=settings.AKVO_USERNAME, password=settings.AKVO_PASSWORD)
                try:
                    logger.info(u'Meetpuntgegevens ophalen voor {}'.format(locatie))
                    m1,w1 = importAkvoRegistration(api, akvo, projectlocatie=locatie,user=user,days=days)
                    logger.info(u'Waarnemingen ophalen voor {}'.format(locatie))
                    m2,w2=importAkvoMonitoring(api, akvo, days)
                    mp = m1|m2
                    wn = w1|w2
                    if mp:
                        logger.info(u'Grafieken aanpassen')
                        util.updateSeries(mp, user)
                        #logger.info('Cartodb actualiseren')
                        util.exportCartodb(cartodb, mp)
                    akvo.last_update = timezone.now()
                    akvo.save()        
                except Exception as e:
                    logger.exception(u'Probleem met verwerken nieuwe EC metingen: %s',e)
                finally:
                    pass
