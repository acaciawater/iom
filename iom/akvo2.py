# -*- coding: utf-8 -*-
'''
Created on Feb 14, 2019

@author: theo
'''
import requests
import logging
from pytz import utc
from time import mktime
from dateutil.parser import parser as duparser
parser = duparser()
logger = logging.getLogger(__name__)

def as_timestamp(dt):
    ''' return utc timestamp for dt '''
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = utc.localize(dt)
    return int(mktime(dt.utctimetuple())*1000)

def find_key(array, key, value):
    ''' return key in dict of dict where key=value '''
    found = filter(lambda (k,v): v[key] == value, array.items())
    return found[0][0] if found else None

def find(array, key, value):
    ''' return item in array of dict where key=value '''
    if isinstance(array,dict):
        # array is dict of dict
        array = array.values()
    found = filter(lambda item: item[key] == value, array)
    return found[0] if found else None

class FlowAPI:
    '''
    Access to Akvo FLOW api v2 
    '''
    def __init__(self,**kwargs):
        self.username=kwargs.get('username')
        self.password=kwargs.get('password')
        self.auth={}
        self.url='https://api.akvo.org/flow/orgs/acacia/'

    def authenticate(self,**kwargs):
        '''
        Authenticate user by sending username/password to login endpoint and retrieve access_token
        '''
        data= {
            'client_id': 'curl',
#             'scope': 'openid',
            'scope': 'openid offline_access',
            'username': kwargs.get('username',self.username),
            'password': kwargs.get('password',self.password),
            'grant_type': 'password'
        }
        response = requests.post('https://login.akvo.org/auth/realms/akvo/protocol/openid-connect/token',data=data)
        response.raise_for_status()
        
        # update credentials
        self.username = data['username']
        self.password = data['password']
        self.auth = response.json()
        return self.auth

    def refresh_token(self):
        '''
        Refresh token (token expires after 300-1800 seconds)
        '''
        if not self.auth:
            # not previously authenticated
            return self.authenticate()
        data = {
            'client_id': 'curl',
            'scope': 'openid',
            'refresh_token': self.auth['refresh_token'],
            'grant_type': 'refresh_token'
        }
        response = requests.post('https://login.akvo.org/auth/realms/akvo/protocol/openid-connect/token',data=data)
        response.raise_for_status()
        self.auth=response.json()
        return self.auth
             
    def request(self, url, **kwargs):
        ''' send a GET request and convert the json response to a python dict '''
        token = self.auth.get('access_token')
        if not token:
            raise 'Not authenticated.'
        headers = {'User-Agent': 'curl/7.54.0',
                   'Accept': 'application/vnd.akvo.flow.v2+json',
                   'Authorization': 'Bearer '+token
        }
        response = requests.get(url,params=kwargs,headers=headers)
        logger.debug('{} {}: {}'.format(response.status_code, response.reason, response.content))
        if response.status_code in [401, 403]:
            logger.warning('WARNING: statuscode = {}. Refreshing token'.format(response.status_code))
            self.authenticate()
            response = requests.get(url,params=kwargs,headers=headers)
            logger.debug('{} {}: {}'.format(response.status_code, response.reason, response.content))
        response.raise_for_status()
        return response.json()

    def get(self, path, **kwargs):
        ''' send a GET request to the API '''
        return self.request(self.url + path, **kwargs)

    def get_folder(self, name):
        response = self.get('folders')
        for folder in response['folders']:
            if folder['name'] == name:
                return folder
        return None
    
    def get_survey(self, folder, name):
        response=self.request(folder['surveysUrl'])
        for survey in response['surveys']:
            if survey['name'] == name:
                return survey
        return None        
    
    def get_form_instances(self, survey_id, form_id, beginDate=None, endDate=None):
        response = self.get('form_instances',survey_id=survey_id,form_id=form_id)
        while True:
            for instance in response['formInstances']:
                if beginDate or endDate:
                    date = parser.parse(instance['modifiedAt'])
                    if beginDate and date < beginDate:
                        continue
                    if endDate and date > endDate:
                        continue
                yield instance
            nextPage = response.get('nextPageUrl')
            if nextPage:
                response = self.request(nextPage)
            else:
                break
            
    def get_questions(self,surveyid,formid=None):
        ''' build dictionary of questions for lookup by question id. Do this for a single form or all forms '''
        response = self.get('surveys/{}'.format(surveyid))
        forms = response['forms']
        questions = {}
        for form in forms:
            if formid and form['id'] != formid:
                continue
            for group in form['questionGroups']:
                for question in group['questions']:
                    questions[question['id']]=question
        return questions
    
    
    def get_answers(self, instance, questions):
        ''' get responses (answers) from a form instance '''
        answers = {}
        for key, response in instance['responses'].items():
            for item in response:
                for qid, answer in item.items():
                    if qid in questions:
                        answers[qid]=answer
        return answers
    
    def get_answer(self, answers, questions, **kwargs):
        ''' get formatted answer for a question '''
        qid = None
        if 'id' in kwargs:
            qid = kwargs['id']
        elif 'text' in kwargs:
            name = kwargs['text'].strip()
            for key in answers:
                question = questions[key]['name'].strip()
                if question == name:
                    qid = key
                    break
        else:
            raise 'No id nor text given.'
        if not qid:
            return None
             
        question = questions[qid]
        answer = answers[qid]
        qtype=question['type']
        if qtype == 'DATE':
            return parser.parse(answer).replace(tzinfo=utc)
        elif qtype == 'OPTION':
            items = answer
            return '|'.join([item['text'] for item in items])
        elif qtype == 'CADDISFLY':
            return answer
        elif qtype =='GEO':
            return (answer['long'],answer['lat'])
        elif qtype == 'CASCADE':
            items = answer
            return '|'.join([item['name'] for item in items])
        elif qtype == 'PHOTO':
            return answer['filename']
        elif qtype == 'VIDEO':
            return answer['filename']
        else:
            return answer

# if __name__ == '__main__':
#     api = FlowAPI()
#     api.authenticate(username=AKVO_USERNAME,password=AKVO_PASSWORD)
#     folder = api.get_folder('Texel Meet')
#     print (api.get_survey(folder, 'EC Meting'))
    