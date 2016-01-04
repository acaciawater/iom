'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from optparse import make_option
from iom.models import Meetpunt 
import urllib,urllib2
import time

class Command(BaseCommand):
    args = ''
    help = 'Updates data in cartodb'
    option_list = BaseCommand.option_list + (
            make_option('--pk',
                action='store',
                type = 'int',
                dest = 'pk',
                default = None,
                help = 'update single meetpunt'),
        )
    url = 'https://tkleinen.cartodb.com/api/v2/sql'
    key = '6c962290788f1addce759c808ad7593f61524d90'

    def runsql(self,sql):
        data = urllib.urlencode({'q': sql, 'api_key': self.key})
        request = urllib2.Request(url=self.url, data=data)
        return urllib2.urlopen(request)
        
    def handle(self, *args, **options):
        values = None
        self.runsql('DELETE FROM waarnemers_2')
        for m in Meetpunt.objects.all():
            p = m.location
            p.transform(4326)
            series = m.get_series('EC')
            ec = None if series is None else series.laatste()
            series = m.get_series('Temp')
            temp = None if series is None else series.laatste()
            if ec is None:
                date = 'NULL'
                ec = 'NULL'
            else:
                date = time.mktime(ec.date.timetuple())
                ec = ec.value
            temp = 'NULL' if temp is None else temp.value

            url = m.chart_thumbnail.name
            url = 'NULL' if url is None else "'{url}'".format(url=url)
            diep = "'ondiep'" if m.name.endswith('o') else "'diep'"
            s = "(ST_SetSRID(ST_Point({x},{y}),4326), {diepondiep}, {charturl}, {sampleid}, '{waarnemer}', to_timestamp({date}), {ec}, {temp})".format(x=p.x,y=p.y,diepondiep=diep,charturl=url,sampleid=m.nummer,waarnemer=m.waarnemer.id,ec=ec,temp=temp,date=date)
            values = 'VALUES ' + s
            sql = 'INSERT INTO waarnemers_2 (the_geom,diepondiep,charturl,sampleid,waarnemer,datum,ec,temperatuur) ' + values
            print sql
            self.runsql(sql)
#             if values is None:
#                 values = 'VALUES ' + s
#             else:
#                 values += ',' + s
#         
#         sql = 'INSERT INTO waarnemers_2 (the_geom,charturl,sampleid,waarnemer,datum,ec,temperatuur) ' + values
#         print self.runsql(sql)
        