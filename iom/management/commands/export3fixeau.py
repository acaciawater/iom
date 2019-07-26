# -*- coding: utf-8 -*-
import os
import re
import json
import logging
import string

from django.conf import settings
from django.core.management.base import BaseCommand
import requests
from requests.exceptions import HTTPError

from acacia.data.models import Project
from iom.models import Waarnemer, Meetpunt, Waarneming
import decimal
from math import isnan

logger = logging.getLogger(__name__)

def genstring(charset, length):
    ''' generate a string of length characters selected randomly from charset '''
    import random
    return ''.join([random.choice(charset) for _ in range(length)])

def genpasswd(length=8):
    ''' generate a password of length characters '''
    charset = string.ascii_letters + string.digits# + '!@#$*?'
    # remove difficult-to-read characters
    charset = charset.translate(None,'oO0l1iI')
    return genstring(charset,length)

def truncate(string, maxlength, ellipsis='..', position='begin'):
    ''' truncate a string to maxlength characters and insert placeholder in truncated string. 
    position can be begin, end or middle '''
    
    length = len(string)
    if length <= maxlength:
        return string

    # remove trailing whitespace
    string = string.strip()
    length = len(string)
    if length <= maxlength:
        return string

    # remove all other whitespace    
    string = re.sub(r'\s','',string)
    length = len(string)
    if length <= maxlength:
        return string
    
    length2 = maxlength - len(ellipsis)
    if position == 'end':
        return string[:length2] + ellipsis
    if position == 'begin':
        return ellipsis + string[-length2:]
    left = length2/2
    right = length2-left
    return string[:left] + ellipsis + string[-right:]
    
class Api:
    ''' Interface to api with JWT authorization '''

    def __init__(self, url):
        self.url = url
        self.headers = {}
        
    def post(self, path, data, **kwargs):
        url = self.url + path
        return requests.post(url, json=data, headers=self.headers, **kwargs)

    def put(self, path, data):
        url = self.url + path 
        return requests.put(url, json=data, headers=self.headers)

    def patch(self, path, data):
        url = self.url + path
        return requests.patch(url, json=data, headers=self.headers)

    def get(self, path, params=None):
        # prepend self.url to path if required
        url = path if path.startswith('http') else self.url + path
        return requests.get(url, params=params, headers=self.headers)

    def login(self, username, password):
        response = requests.post(self.url+'/token/',{
            'username': username,
            'password': password
        })
        response.raise_for_status()
        json = response.json()
        self.token = json.get('token')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization':'JWT '+self.token
        }
        return self.token

class Command(BaseCommand):
    args = ''
    help = 'Exporteer data naar fixeau.com '
    
    def add_arguments(self, parser):
        
        parser.add_argument('-u','--url',
                action='store',
                dest = 'url',
                default = 'https://test.fixeau.com/api/v1',
                help = 'API url')

        parser.add_argument('-f','--folder',
                action='store',
                dest = 'folder',
                default = 7, #RijnlandMeet
                help = 'Folder id for data sources and time series')
        
    def findObjects(self, path, query):
        ''' returns generator that iterates over all objects satisfying query '''
        response = self.api.get(path, params=query)
        next = True
        while next:
            response.raise_for_status()
            json = response.json()
            results = json.get('results')
            if not results:
                break
            for result in results:
                yield result
            next = json.get('next')
            if next:
                response = self.api.get(next)

    def findFirstObject(self, path, query):
        ''' returns json of first object that satisfies query '''
        results = self.findObjects(path, query)
        return next(results,None)

    def getObject(self, path, pk):
        ''' get object by primary key. Path must end with a slash '''
        response = self.api.get(path+pk)
        if response.ok:
            return response.json()
                
        if response.status_code != 404:
            # raise exception (not for 'not found' errors)
            response.raise_for_status()
            
        return None 

    def findGroup(self, name):
        ''' finds a group by name. returns json of group or None when not found '''
        return self.findFirstObject('/group/', {'name': name})
    
    def createGroup(self, name):
        ''' Create a group with name. Returns json of created group '''
        response = self.api.post('/group/', {'name': name})
        response.raise_for_status()
        return response.json()
    
    def makeUsername(self,waarnemer):
        username = str(waarnemer).lower().replace(' ', '').replace('.','')
        return username
    
    def findUser(self, waarnemer):
        ''' find a user corresponding to a waarnemer or None when not found '''
        username = self.makeUsername(waarnemer)
        return self.findFirstObject('/user/', {'username': username})

    def setPassword(self, user, password):
        response = self.api.patch('/user/{}/'.format(user['id']), {'password': password})
        response.raise_for_status()
        return password
    
    def createUser(self, waarnemer, group):
        ''' create user for waarnemer, add index number (max 10) if user already exists. Returns json of created user '''
        username = self.makeUsername(waarnemer)
        # generate a password, reset later
        password = genpasswd(8)

        payload = {
                'username': username, 
                'password': password,
                'email': waarnemer.email,
                'groups': [group],
                'is_active': False,
                'details': {
                    'phone_number': waarnemer.telefoon
                }
        }
        
        # set first or last name only when not null
        first_name = waarnemer.voornaam or waarnemer.initialen
        if first_name:
            payload['first_name'] = first_name

        last_name = waarnemer.tussenvoegsel + ' ' + waarnemer.achternaam if waarnemer.tussenvoegsel else waarnemer.achternaam
        if last_name:
            payload['last_name'] = last_name

        for index in range(1,10):
            response = self.api.post('/user/', payload)
            if response.ok:
                break
            
            # find out what the problem is..
            reason = response.json()
            if 'username' in reason:
                problems = reason['username']
                if 'A user with that username already exists.' in problems:
                    # try again with new username
                    payload['username'] = username + str(index)
                    continue
                    
            response.raise_for_status()
            
        user = response.json()
        user['password'] = password
        return user

    def addPhoto(self, photo):
        ''' copy image from server to fixeau.com '''
        filename = os.path.basename(photo)
        headers = {}
        try:
            with open(photo,'rb') as f:
                url = self.api.url
                headers.update(self.api.headers)
                # remove content-type from header (content is not json)
                headers.pop('Content-Type')
                payload = {'name': filename}
                files = {'image':(filename, f)}
                response = requests.post(url+'/photo/', data = payload, headers = headers, files = files)
                response.raise_for_status()
                photo = response.json()
                logger.debug('Added photo {}: {}'.format(photo['id'],photo['name']))
                return response.json()
        except HTTPError as error:
            response = error.response
            logger.error('ERROR uploading photo {}: {}'.format(photo, response.json()))
        except Exception as error:
            logger.error('ERROR uploading photo {}: {}'.format(photo, error))
        return None
    
    def cleanDeviceName(self, device):
        ''' clean device name so that it is fully alphanumeric '''
        return re.sub(r'[^A-Za-z0-9]','',device)

    def getSource(self, device):
        ''' return datasource object for device '''
        sourceid = self.cleanDeviceName(device)
        return self.getObject('/source/', sourceid)
        
    def createSource(self, device, users, group, folder=None):
        ''' create a datasource for a device. First add source_type AkvoMobile to database
        device: akvo phone device identifier
        users: list of user names that use the device
        group: group id for device
        '''
        sourceid = self.cleanDeviceName(device)
        response = self.api.post('/source/', {
            'id': sourceid,
            'name': device,
            'description': 'Akvo phone '+device,
            'source_type': 'AkvoMobile',
            'folder': folder,
            'group': group,
            'users': users 
        })
        response.raise_for_status()
        return response.json()
    
    def makeSeriesName(self, meetpunt, category, maxlength=24):
        name = meetpunt.name.strip()
        if len(name) > maxlength:
            # remove everything up to 'achternaam - ' 
            tag = '{} - '.format(meetpunt.waarnemer.achternaam).lower()
            pos = name.lower().find(tag)
            if pos >= 0:
                name = name[pos+len(tag):]
                
        if category:
            postfix=':'+category[0].lower()
            name = truncate(name, maxlength-2) + postfix
        else:
            name = truncate(name, maxlength)
        return name
    
    def findSeries(self, meetpunt, category):
        ''' find EC time series for a meetpunt and category combination '''
        name = self.makeSeriesName(meetpunt, category)
        sourceid = self.cleanDeviceName(meetpunt.device)
        return self.findFirstObject('/series/', {
            'name': name,
            'source': sourceid,
            'parameter': 'EC',
            'category': category
            })

    def createSeries(self, meetpunt, category, folder = None):
        ''' create timeseries for a meetpunt, category combination '''
        location = meetpunt.latlng()
        name = self.makeSeriesName(meetpunt, category)
        sourceid = self.cleanDeviceName(meetpunt.device)
        meta = {'identifier': meetpunt.identifier}
        photo = self.addPhoto(settings.BASE_DIR + meetpunt.photo_url) if meetpunt.photo_url else None
        if photo:
            meta['imageUrl'] = photo['image']
            meta['image_id'] = photo['id']
        response = self.api.post('/series/', {
            'name': name,
            'description': meetpunt.displayname,
            'location': {
                'coordinates': [
                    location[1],
                    location[0]
                ],
                'type': 'Point'
            },
            'meta': meta,
            'folder': folder,
            'source': sourceid,
            'parameter': 'EC',
            'category': category,
            'unit': 'mS/cm'      
        })
        response.raise_for_status()
        return response.json()

    def getMeasurements(self, series):
        ''' get all measurements for a time series '''
        return self.findObjects('/measurement/',{'series': series})
        
    def addWaarnemingen(self, meetpunt, queryset, target):
        ''' add all measurements for meetpunt to target time series using waarneming queryset '''
        location = meetpunt.latlng()
        sourceid = self.cleanDeviceName(meetpunt.device)

        def waarneming2measurement(waarneming, target):
            ''' convert waarneming to measurement and set series to target '''
            photo = self.addPhoto(settings.BASE_DIR + waarneming.foto_url) if waarneming.foto_url else None
            meta = {'imageUrl': photo['image'], 'image_id': photo['id']} if photo else None
            waarde = None if isnan(waarneming.waarde) else waarneming.waarde
            return {
                'time': waarneming.datum.isoformat(),
                # assume units is μS/cm when EC > 50
                'value': waarde/1000.0 if waarde > 50 else waarde,
                'location': {
                    'coordinates': [
                        location[1],
                        location[0]
                    ],
                    'type': 'Point'
                },
                'meta': meta,
                'source': sourceid,
                'parameter': 'EC',
                'unit': 'mS/cm',
                'series': target} 
        # exclude nan values (json encoder in acaciadb api does not like them)
        # MySQL does not recognize nan
        #measurements = [waarneming2measurement(waarneming,target) for waarneming in queryset.exclude(waarde=decimal.Decimal('NaN')).order_by('datum')]
        measurements = [waarneming2measurement(waarneming,target) for waarneming in queryset.order_by('datum')]
        response = self.api.post('/measurement/',measurements)
        response.raise_for_status()
        return response

    def cycle(self,array):
        while True:
            for elem in array:
                yield elem

    def test_series_names(self):
        cat = self.cycle(['o','d'])
        for meetpunt in Meetpunt.objects.all():
            name = self.makeSeriesName(meetpunt,next(cat),24)
            if name != meetpunt.name:
                print (meetpunt.name, '=>', name)
                
    def handle(self, *args, **options):

        #self.test_series_names()
    
        url = options.get('url')
        folder = options.get('folder')        
        project = Project.objects.first()
        
        self.api = Api(url)
        logger.info('Logging in, url={}'.format(url))
        self.api.login(settings.FIXEAU_USERNAME,settings.FIXEAU_PASSWORD)
        
        # get or create project group
        groupName = project.name
        group = self.findGroup(groupName)
        if not group:
            logger.info('Creating group {}'.format(groupName))
            group = self.createGroup(groupName)
        groupId = group['id']
              
        # get or create users
        logger.info('Creating users')
        users = {}
        for w in Waarnemer.objects.all():
            if not w.waarneming_set.exists():
                # skip waarnemers without measurements
                continue
            try:
                user = self.findUser(w)
                if user:
                    password = genpasswd(8)
                    self.setPassword(user, password)
                    logger.debug('{},{},{},"{}"'.format(w, user['id'], user['username'], password))
                    pass
                else:
                    user = self.createUser(w,groupId)
                    logger.info('Created user {} with username {} with password {} for {}'.format(user['id'], user['username'], user['password'], w))
                users[w] = user
                            
            except HTTPError as error:
                response = error.response
                print('ERROR creating user {}: {}'.format(w,response.json()))
                    
        # build dictionary of devices with set of waarnemers that have used the device
        logger.info('Querying unique devices in '+project.name)
        devices = {}    
        for w in Waarneming.objects.all():
            if w.device in devices:
                devices[w.device].add(w.waarnemer)
            else:
                devices[w.device] = set([w.waarnemer])
        logger.debug('{} devices found'.format(len(devices)))
        for device, waarnemers in devices.items():
            logger.debug('device: {}, used by: {}'.format(device, ','.join(map(str,waarnemers))))
                         
        # add devices (create data sources)
        logger.info('Creating data sources')
        for device, waarnemers in devices.items():
            usernames = [users[w]['username'] for w in waarnemers if w in users] 
            try:
                source = self.getSource(device)
                if source:
                    logger.debug('Found existing data source {} for {}'.format(source['name'],','.join(usernames)))
                else:
                    source = self.createSource(device, usernames, groupId, folder=folder)
                    logger.debug('Created data source {} for {}'.format(device,','.join(usernames)))
            except HTTPError as error:
                response = error.response
                print('ERROR creating data source {}: {}'.format(device,response.json()))
   
        logger.info('Creating time series')
        deep = 'Deep' if 'test.fixeau.com' in url else 'Diep'
        shallow = 'Shallow' if 'test.fixeau.com' in url else 'Ondiep'
        for m in Meetpunt.objects.all():
            try:
                # create dict of categories and related querysets    
                cats = {
                    shallow: m.waarneming_set.filter(naam__iexact="ec_ondiep"),
                    deep: m.waarneming_set.filter(naam__iexact="ec_diep"),
                    '': m.waarneming_set.filter(naam__iexact="ec")
                }
                for category, queryset in cats.items():
                    if not queryset:
                        # no data for this category
                        continue
                    target = self.findSeries(m, category)
                    if target:
                        logger.debug('Found existing time series {}: {}'.format(target['id'], target['name']))
                        measurements = self.getMeasurements(target['id'])
                        if next(measurements,None):
                            # series already has measurements
                            logger.debug('Time series already contains measurements')
                            continue
                    else:
                        target = self.createSeries(m, category, folder=folder)
                        logger.debug('Created time series {} for {}'.format(target['id'], target['name']))
                    response = self.addWaarnemingen(m, queryset, target['id'])
                    if response:
                        resp = response.json()
                        logger.debug('Added {} measurements'.format(resp.get('count')))
                        
            except HTTPError as error:
                response = error.response
                print('ERROR creating time series {} ({}): {}'.format(m,category,response.json()))
                break # abort
            
