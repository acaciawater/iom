'''
Created on Oct 22, 2015

@author: theo
'''
# -*- coding: utf-8 -*-

# Copyright (C) 2014 Stichting Akvo (Akvo Foundation)
#
# This file is part of Akvo FLOW.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import binascii
import calendar
import hmac
import urllib
import urllib2
import json
import csv
import platform

from datetime import datetime
from pytz import utc
from time import mktime
from hashlib import sha1

windows = platform.system() == 'Windows'

def unix_timestamp():
    now = datetime.utcnow()
    return calendar.timegm(now.timetuple())

def as_timestamp(dt):
    ''' return utc timestamp for dt '''
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = utc.localize(dt)
    return int(mktime(dt.utctimetuple())*1000)

def as_datetime(timestamp,timezone=None):
    ''' convert unix timestamp to datetime with timezone '''
    return datetime.fromtimestamp(timestamp,timezone) if timestamp else None

def utf8(d):
    ''' encode dict or list as utf-8 (needed for windows) '''
    if isinstance(d,list):
        return [unicode(a).encode('utf-8') for a in d]
    else:
        return {unicode(k).encode('utf-8'):unicode(v).encode('utf-8') for k,v in d.items()}

class FlowAPI:


    def __init__(self,instance,key,secret):
        self.key=str(key)
        self.secret=str(secret)
        self.instance=instance
        self.api = '/api/v1'
        
    def signature(self, path):
        timestamp = unix_timestamp()
        payload = 'GET\n{timestamp}\n{path}'.format(timestamp=timestamp, path=path)
        signature = hmac.new(self.secret, payload, sha1)
        return timestamp, binascii.b2a_base64(signature.digest()).rstrip('\n')
    
    def api_call_path(self,url):
        start = url.find(self.api)
        end = url.find('?')
        assert start >= 0, "Mis-configured URL, can't find '{api}'".format(api=self.api)
        if end < 0:
            return url[start:]
        else:
            return url[start:end]

    def get_response(self, url, key=None):
        ''' send a request to the API and convert the json response to a python dict '''
        path = self.api_call_path(url)
        timestamp, base64_signature = self.signature(path)
        auth_header = "{}:{}".format(self.key, base64_signature)
        request = urllib2.Request(url, headers={"Date": timestamp, "Authorization": auth_header})
        for i in range(4):
            try:
                contents = urllib2.urlopen(request).read()
                contents = json.loads(contents)
                return contents.get(key,contents) if key else contents
            except urllib2.URLError as e:
                if hasattr(e,'code') and e.code == 400:  # bad request
                    raise e
                if i == 3: # Too many tries
                    print '\n{error}, Giving up...'.format(error=e)
                    raise e
                print '\n{error}, Trying again...'.format(error=e)

    def base_url(self):
        return self.instance + self.api
    
    def format_url(self, resource, **query_params):
        url = self.base_url()
        if not url.endswith('/'):
            url += '/'
        url += resource
        if query_params:
            url += '?'
            url += urllib.urlencode(query_params)
        return url
    
    def get_devices(self):
        url = self.format_url('devices')
        return self.get_response(url,'devices')

    def get_device(self,device_id):
        url = self.format_url('devices/{id}'.format(id=device_id))
        return self.get_response(url,'device')
    
    def get_survey_groups(self):
        '''Retrieves a list of all survey groups'''
        url = self.format_url('survey_groups')
        return self.get_response(url,'survey_groups')

    def get_survey_group(self,group_id):
        '''Retrieve survey group by id'''
        url = self.format_url('survey_groups/{id}'.format(id=group_id))
        return self.get_response(url,'survey_group')

    def get_surveys(self):
        '''Retrieves a list of all surveys'''
        url = self.format_url('surveys')
        return self.get_response(url,'surveys')

    def get_survey(self,survey_id):
        '''Retrieve survey by id'''
        url = self.format_url('surveys/{id}'.format(id=survey_id))
        return self.get_response(url,'survey')

    def get_surveyed_locales(self,surveyGroupId):
        '''Retrieves a list of surveyed locales'''
        url = self.format_url('surveyed_locales?surveyGroupId={id}'.format(id=surveyGroupId))
        return self.get_response(url,'surveyed_locales')
        
    def get_survey_instances(self,**kwargs):
        '''
        query parameters:
        surveyId=<id>         Retrieves a list of survey instances based on survey id
        deviceId=<id>         Retrieves a list of survey instances based on device id
        beginDate=<timestamp> Retrieves a list of survey instances submitted after <timestamp>
        endDate=<timestamp>   Retrieves a list of survey instances submitted before <timestamp>
        since=<cursor-id>     Retrieves a list of survey instances skipping the instances before <cursor-id>. 
                              If a response contains more than 20 instances you can get the next 20 by using the value of meta.since as the since query parameter.
        '''
        url = self.format_url('survey_instances',**kwargs)
        response = self.get_response(url)
        return (response['survey_instances'],response['meta'])

    def get_registration_instances(self, surveyId, key='surveyedLocaleIdentifier', beginDate=None, endDate = None):
        '''Retrieve dict of survey instances, indexed by key for use as lookup table'''
        instances = {}
        kwargs = {'surveyId': surveyId }
        if beginDate:
            kwargs['beginDate'] = beginDate
        if endDate:
            kwargs['endDate'] = endDate
        reg, meta = self.get_survey_instances(**kwargs)
        while reg:
            instances.update({r[key]: r for r in reg})
            kwargs['since'] = meta['since']
            reg, meta = self.get_survey_instances(**kwargs)
        return instances

    def get_registration_instances_with_answers(self, surveyId, key='surveyedLocaleIdentifier'):
        '''Retrieve dict of survey instances with answers, indexed by key for use as lookup table'''
        instances = {}
        reg, meta = self.get_survey_instances(surveyId=surveyId)
        while reg:
            for r in reg:
                answers = {a['questionText']:a['value'] for a in self.get_answers(r['keyId'])}
                instances.update({r[key]: {'instance': r, 'answers': answers}})
            reg, meta = self.get_survey_instances(surveyId=surveyId,since=meta['since'])
        return instances
            
    def get_questions(self,survey_id):
        '''Retrieve a list of questions for a survey'''
        url = self.format_url('questions?surveyId={id}'.format(id=survey_id))
        return self.get_response(url,'questions')

    def get_question(self,question_id):
        '''Retrieve a question by id'''
        url = self.format_url('questions/{id}'.format(id=question_id))
        return self.get_response(url,'question')

    def get_question_groups(self,surveyId=None):
        ''' Retrieves a list of all question groups, optionally filtered by survey id '''
        if surveyId:
            url = self.format_url('question_groups',surveyId=surveyId)
        else:
            url = self.format_url('question_groups')
        return self.get_response(url,'question_groups')

    def datefilter(self,answers):
        for a in answers:
            if a['type'] == 'DATE':
                a['value'] =  datetime.utcfromtimestamp(int(a['value'])/1000)
        return answers
    
    def get_answers(self, survey_instance_id):
        '''Retrieve answers for a survey instance'''
        url = self.format_url('question_answers?surveyInstanceId={id}'.format(id=survey_instance_id))
        return self.datefilter(self.get_response(url,'question_answers'))
    
    def get_answer(self, answers, **kwargs):
        key,value = kwargs.popitem()
        for a in answers:
            if a[key] == value:
                return a['value']
        return None
    
    def to_csv(self, surveyId, destination, callback=None, registrationId = None, registrationFields = {}):
        ''' downloads all answers for a survey and exports to destination in csv format
            the optional boolean callback function is called with current survey instance as argument during export to monitor progress or abort the download
            if the optional registration info is supplied, the export will contain additional fields from the related registration form
            registrationId: survey id of the registration forms
            registrationFields: dict {display_name: registration_fieldname} - fields to include in the export '''
        
        # fields from survey instance to use for export
        survey_fields = {'deviceId': 'deviceIdentifier', 'userId': 'userID', 'submitter': 'submitterName', 'date': 'collectionDate', 'duration': 'surveyalTime'}
        
        # column headers (fieldnames)
        fieldnames = survey_fields.keys()

        # retrieve questions and build field names (column headers)
        questions = self.get_questions(surveyId)
        fieldnames.extend(['%s|%s'% (q['keyId'],q['displayName']) for q in questions])

        registrationData = None        

        if registrationFields and registrationId:
            # fetch registration instances
            registrationData = self.get_registration_instances(registrationId)
            # insert registration fields into the column headers
            fieldnames[:0]= registrationFields.keys()

        # create a csv writer and write out the column headers
        writer = csv.DictWriter(destination, fieldnames=fieldnames)        
        writer.writeheader()
        
        # get all survey instances
        instances,meta = self.get_survey_instances(surveyId=surveyId)
        while instances:
            for instance in instances:
                if callback:
                    # report progress
                    if not callback(instance):
                        print 'aborted'
                        return
                    
                # get standard values from survey instance
                row = {k:instance[v] for k,v in survey_fields.items()}
                
                # get the answers for this survey instance
                answers = self.get_answers(instance['keyId'])
                row.update({'%s|%s' % (a['questionID'],a['questionText']):a['value'] for a in answers})
                
                if registrationData:
                    # add related registration form info to the row
                    localeId = instance['surveyedLocaleIdentifier']
                    regdata = registrationData.get(localeId, None)
                    if regdata:
                        fields = {displayname:regdata[fieldname] for displayname,fieldname in registrationFields.items()}
                        row.update(fields)
                try:
                    # convert unix timestamp to human readable form
                    row['date'] = datetime.utcfromtimestamp(int(row['date'])/1000)
                    if windows:
                        row = utf8(row)
                    writer.writerow(row)
                except Exception as e:
                    # some error occurred while writing the row
                    print row, e

            # get next bunch of survey instances 
            instances,meta = self.get_survey_instances(surveyId=surveyId,since=meta['since'])

KEY=r'B3+dye342B4HpLuJ+Ked3GCyjjTVA5/4fv1ZT0SEKi0='
SECRET=r'fBA5XsXAtSXzbOs4acpg5l2S+ptPPZhiKKzMSwYTfqQ='
INSTANCE=r'http://acacia.akvoflow.org/'

if __name__ == '__main__':
    now1 = datetime.now()
    tsnow1 = as_timestamp(now1)
    tsnow2 = unix_timestamp()
    now2 = as_datetime(tsnow2)
    
    api = FlowAPI(instance=INSTANCE, key=KEY, secret=SECRET)
    devs = api.get_devices()
    print devs
