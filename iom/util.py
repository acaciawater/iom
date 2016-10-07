# -*- coding: utf-8 -*-
'''
Created on Sep 4, 2015

@author: theo
'''

import os,math,time,logging
from django.utils.text import slugify
from django.conf import settings
from iom.models import Meetpunt
from acacia.data.models import Chart

logger = logging.getLogger(__name__)
def distance(obj, pnt):
    dx = obj.location.x - pnt.x
    dy = obj.location.y - pnt.y
    return math.sqrt(dx*dx+dy*dy)

def closest_object(query,target):
    closest = None
    dist = 1e99
    for obj in query:
        d = distance(obj, target)
        if d < dist:
            closest = obj
            dist = d
    return closest

def sort_objects(query,target):
    objs = []
    for obj in query:
        obj.distance = distance(obj, target)
        objs.append(obj)
    return sorted(objs, key=lambda x: x.distance)

def zoek_meetpunten(target, tolerance=1.0):
    mps = sort_objects(Meetpunt.objects.all(), target)
    return [m for m in mps if m.distance < tolerance]

def zoek_tijdreeksen(target,tolerance=1.0):
    ''' haal alle tijdreeksen op rond een locatie '''
    mps = zoek_meetpunten(target, tolerance)
    series = []
    for mp in mps:
        series.extend(mp.series())
    return series

import matplotlib.pyplot as plt
import pandas as pd

def maak_meetpunt_thumbnail(meetpunt):
    
    imagefile = os.path.join(meetpunt.chart_thumbnail.field.upload_to,slugify(unicode(meetpunt.identifier))+'.png')
    imagepath = os.path.join(settings.MEDIA_ROOT,imagefile)
    imagedir = os.path.dirname(imagepath)
    if not os.path.exists(imagedir):
        os.makedirs(imagedir)
    
    meetpunt.chart_thumbnail.name = imagefile
    
    plt.figure(figsize=(9,3))
    options = {'grid': False, 'legend': True, 'title': 'Meetpunt {num}'.format(num=meetpunt)}
    # TODO: alle tijdreeksen laten zien rondom een meetpunt!
    mps = zoek_meetpunten(meetpunt.location, 1)
    for mp in mps:
        s = mp.get_series('EC')
        if s:
            s =s.to_pandas()
            s.name = 'ondiep' if s.name.endswith('o') else 'diep'
            ax=s.plot(**options)
            ax.set_ylabel('EC')

    try:
        plt.savefig(imagepath)
    except:
        logger.exception('Error saving thumbnail for %s' % meetpunt)
    plt.close()
    
    meetpunt.save()

def maak_meetpunt_grafiek(meetpunt,user):
    try:
        chart = meetpunt.chart
    except Exception as e:
        chart = None

    if chart is None:
        name = unicode(meetpunt)
        chart, created = Chart.objects.get_or_create(name = name, defaults = {
                                                             'user': user, 
                                                             'title': name, 
                                                             'percount': 0,
                                                             'description': unicode(meetpunt.description)})
        meetpunt.chart=chart
        meetpunt.save()
                                                             
    series = zoek_tijdreeksen(meetpunt.location,1)
    for s in series:
        pos, ax = ('l', 1) if s.name.startswith('EC') else ('r', 2)
        cs, created = chart.series.get_or_create(series=s, defaults={'name': s.name, 'axis': ax, 'axislr': pos, 'type': s.type})
        if s.type != cs.type:
            cs.type = s.type
            cs.save()
    chart.save()
    
    maak_meetpunt_thumbnail(meetpunt)
    
def updateSeries(mps, user):    
    '''update timeseries using meetpunten in  mps'''
    allseries = set()
    for mp in mps:
        loc = mp.projectlocatie
        for w in mp.waarneming_set.all():
            waarde = w.waarde
            series, created = mp.series_set.get_or_create(name=w.naam,defaults={'user': user, 'type': 'scatter', 'unit': 'mS/cm'})
            if created:
                logger.info('Tijdreeks {name} aangemaakt voor meetpunt {locatie}'.format(name=series.name,locatie=unicode(mp)))  
            dp, created = series.datapoints.get_or_create(date=w.datum, defaults={'value': waarde})
            updated = created
            if not created and dp.value != waarde:
                dp.value=waarde
                dp.save(update_fields=['value'])
                updated = True
                logger.debug('{name}, {date}, EC={ec}'.format(name=series, date=dp.date, ec=dp.value))
            if created or updated:
                allseries.add(series)

    logger.info('Thumbnails tijdreeksen aanpassen')
    for series in allseries:
        series.getproperties().update()
        lineType = 'scatter' if series.aantal < 2 else 'line'
        if series.type != lineType:
            series.type = lineType
            series.save()
        series.make_thumbnail()

    logger.info('Grafieken aanpassen')
    for mp in mps:
        maak_meetpunt_grafiek(mp, user)

def maak_naam(parameter,diep):
    if diep and not diep.endswith('iep'):
        diep = None
    return parameter + '_' + diep if diep else parameter
        
def escape(string):
    ''' double single quotes '''
    return string.replace("'", "''")

def updateCartodb(cartodb, mps):
    for m in mps:
        p = m.location
        p.transform(4326)
        
        waarnemingen = m.waarneming_set.all().order_by('-datum')
        if waarnemingen.exists():
            last = waarnemingen[0]
            ec = last.waarde
            date = last.datum
            diep = "'ondiep'" if last.naam.endswith('ndiep') else "'diep'" if last.naam.endswith('diep') else "''"
        else:
            ec = None
            date = None
            diep = ''
        if ec is None or date is None:
            date = 'NULL'
            ec = 'NULL'
        else:
            date = time.mktime(date.timetuple())

        url = m.chart_thumbnail.name
        url = 'NULL' if url is None else "'{url}'".format(url=url)
        s = "(ST_SetSRID(ST_Point({x},{y}),4326), {diep}, {charturl}, '{meetpunt}', '{waarnemer}', to_timestamp({date}), {ec})".format(x=p.x,y=p.y,diep=diep,charturl=url,meetpunt=escape(m.name),waarnemer=unicode(m.waarnemer),ec=ec,date=date)
        values = 'VALUES ' + s
        
        logger.debug('Actualiseren cartodb meetpunt {meetpunt}, waarnemer {waarnemer}'.format(meetpunt=m,waarnemer=m.waarnemer))
        sql = "DELETE FROM {table} WHERE waarnemer='{waarnemer}' AND meetpunt='{meetpunt}'".format(table=cartodb.datatable, waarnemer=unicode(m.waarnemer), meetpunt=escape(m.name))
        cartodb.runsql(sql)
        
        sql = 'INSERT INTO {table} (the_geom,diepondiep,charturl,meetpunt,waarnemer,datum,ec) '.format(table=cartodb.datatable) + values
        cartodb.runsql(sql)

from itertools import groupby

# this version replaces ALL measurements of a meetpunt
def exportCartodb(cartodb, mps, table):

    for m in mps:
        print m
        
        waarnemingen = m.waarneming_set.order_by('naam', 'datum')
        if not waarnemingen:
            logger.warning('Geen waarnemingen voor meetpunt {meetpunt}, waarnemer {waarnemer}'.format(meetpunt=m,waarnemer=m.waarnemer))
            continue

        regio = m.projectlocatie.name
        meetpunt = m.name.replace("'", "''")
        p = m.location
        p.transform(4326)

        logger.debug('Actualiseren cartodb meetpunt {meetpunt}, waarnemer {waarnemer}'.format(meetpunt=m,waarnemer=m.waarnemer))
        sql = "DELETE FROM {table} WHERE waarnemer='{waarnemer}' AND meetpunt='{meetpunt}'".format(table=table, waarnemer=unicode(m.waarnemer), meetpunt=meetpunt)
        cartodb.runsql(sql)

        # group waarnemingen by name (diep/ondiep, ...)
        for key,items in groupby(waarnemingen,lambda w: w.naam):
            values = ''
            ec2 = None
            wnid = 0
            for item in items:
                w = item
                wnid += 1
                ec1 = ec2
                ec2 = w.waarde
                delta = ec2-ec1 if ec1 and ec2 else 0
                date = w.datum
                if w.naam.find('_'):
                    words = w.naam.split('_')
                    diep = "'"+words[-1]+"'"
                else:
                    diep = 'NULL'
                
                print date, ec2
                date = time.mktime(date.timetuple())
                url = m.chart_thumbnail.name
                url = 'NULL' if url is None else "'{url}'".format(url=url)
                s = "(ST_SetSRID(ST_Point({x},{y}),4326), {diep}, {charturl}, '{meetpunt}', '{waarnemer}', '{regio}', {wnid}, to_timestamp({date}), {ec}, {delta})"\
                    .format(x=p.x,y=p.y,diep=diep,charturl=url,meetpunt=meetpunt,waarnemer=unicode(m.waarnemer),wnid=wnid,ec=ec2,delta=delta,date=date,regio=regio)
                if values:
                    values += ','
                values += s
            if values:
                sql = 'INSERT INTO {table} (the_geom,diepondiep,charturl,meetpunt,waarnemer,regio,wnid,datum,ec,ec_toename) VALUES '.format(table=table) + values
                ok = cartodb.runsql(sql)

# this version replaces only selected measurements
def exportCartodb2(cartodb, waarnemingen, table):
    # group waarnemingen by meetpunt
    group = groupby(waarnemingen,lambda w: w.locatie)
    for m,waarnemingen in group:
        print m
        regio = m.projectlocatie.name
        p = m.location
        p.transform(4326)
        values = ''
        dates = []
        meetpunt = m.name.replace("'", "''")
        for w in waarnemingen:
            ec = w.waarde
            date = w.datum
            if w.naam.find('_'):
                words = w.naam.split('_')
                diep = "'"+words[-1]+"'"
            else:
                diep = 'NULL'
            
            date = time.mktime(date.timetuple())
            url = m.chart_thumbnail.name
            url = 'NULL' if url is None else "'{url}'".format(url=url)
            s = "(ST_SetSRID(ST_Point({x},{y}),4326), {diep}, {charturl}, '{meetpunt}', '{waarnemer}', '{regio}', to_timestamp({date}), {ec})" \
                .format(x=p.x,y=p.y,diep=diep,charturl=url,meetpunt=meetpunt,waarnemer=unicode(m.waarnemer),ec=ec,date=date,regio=regio)
            if values:
                values += ','
            values += s
            dates.append(time.mktime(w.datum.timetuple()))
            
        if values:
            logger.debug('Actualiseren cartodb meetpunt {meetpunt}, waarnemer {waarnemer}'.format(meetpunt=m,waarnemer=m.waarnemer))
            datums = ','.join(['to_timestamp({})'.format(d) for d in dates])
            # delete all waarnemingen with matching meetpunt, waarnemer and date
            sql = "DELETE FROM {table} WHERE waarnemer='{waarnemer}' AND meetpunt='{meetpunt}' AND datum in ({dates})".format(table=table, waarnemer=unicode(m.waarnemer), meetpunt=meetpunt, dates=datums)
            cartodb.runsql(sql)
            sql = 'INSERT INTO {table} (the_geom,diepondiep,charturl,meetpunt,waarnemer,regio,datum,ec) VALUES '.format(table=table) + values
            cartodb.runsql(sql)
            
def processTriggers(mps):
    
    for mp in mps:
        for e in mp.get_events():
            history = e.history_set.filter(sent=True).order_by('-date')
            start = history[0].date if history else None
            data = e.trigger.select(start=start)
            num = data.count()
            if num > 0:
                with Messenger(e) as m:
                    # add message for every event
                    for date,value in data.iteritems():
                        if start and date <= start:
                            # dont send message twice
                            continue
                        m.add('Meetpunt {mp}: {msg}'.format(mp=mp,msg=e.format_message(date,value)))
                    msg = 'Event {name} was triggered {count} times for {mp} since {date}'.format(name=e.trigger.name, count=num, mp=mp,date=start)
            else:
                msg = 'No alarms triggered for trigger {name} since {date}'.format(date=start, name=t.name)
            logger.debug(msg)
