# -*- coding: utf-8 -*-
'''
Created on Sep 4, 2015

@author: theo
'''

import os,math,time,logging
from django.utils.text import slugify
from django.conf import settings
from models import Meetpunt
from acacia.data.models import Chart
from django.core.exceptions import ObjectDoesNotExist
from akvo import uuid

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

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import MonthLocator, YearLocator, AutoDateLocator, AutoDateFormatter,\
    DayLocator
import datetime
    

def divide_timedelta(td1, td2):
    divtdi = datetime.timedelta.__div__
    if isinstance(td2, (int, long)):
        return divtdi(td1, td2)
    us1 = td1.microseconds + 1000000 * (td1.seconds + 86400 * td1.days)
    us2 = td2.microseconds + 1000000 * (td2.seconds + 86400 * td2.days)
    return us1 / us2 # this does integer division, use float(us1) / us2 for fp division

def maak_meetpunt_thumbnail(meetpunt):
    
    imagefile = os.path.join(meetpunt.chart_thumbnail.field.upload_to,slugify(unicode(meetpunt.identifier))+'.png')
    imagepath = os.path.join(settings.MEDIA_ROOT,imagefile)
    imagedir = os.path.dirname(imagepath)
    if not os.path.exists(imagedir):
        os.makedirs(imagedir)
    
    meetpunt.chart_thumbnail.name = imagefile
    
    matplotlib.rc('axes', labelsize=18)
    matplotlib.rc('axes', titlesize=22)
    matplotlib.rc('xtick', labelsize=20)
    matplotlib.rc('ytick', labelsize=22)
    
    plt.figure(figsize=(9,3))
    options = {'grid': False, 'legend': True, 'title': 'Meetpunt {num}'.format(num=meetpunt)}
    for s in meetpunt.series_set.all():
        s = s.to_pandas()
        if not s.empty:
            s.plot(**options)

    plt.locator_params(axis='y',nbins=2)
    halfway = divide_timedelta((s.last_valid_index()-s.first_valid_index()),2)
    x=[s.first_valid_index(),s.first_valid_index()+halfway,s.last_valid_index()]
    plt.xticks(x, rotation = 'horizontal')
    ax = plt.gca();
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_horizontalalignment('center')
    ax.tick_params(axis='x',pad=20)
   
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
                                                             
    series = meetpunt.series_set.all()
    #chart.series.delete()
    for s in series:
        #pos, ax = ('l', 1) if s.name.startswith('EC') else ('r', 2)
        pos='l'
        ax = 1
        cs, created = chart.series.get_or_create(series=s, defaults={'name': s.name, 'axis': ax, 'axislr': pos, 'type': s.type})
        if s.type != cs.type:
            cs.type = s.type
            cs.save()
    chart.save()
    
    maak_meetpunt_thumbnail(meetpunt)
    
def updateSeries(mps, user):    
    '''update timeseries using meetpunten in mps'''
    allseries = set()
    for mp in mps:
        loc = mp.projectlocatie
        for w in mp.waarneming_set.all():
            waarde = w.waarde
            series, created = mp.series_set.get_or_create(name=w.naam,defaults={'user': user, 'type': 'scatter', 'scale': 0.001, 'unit': u'mS/cm'})
            if created:
                logger.info(u'Tijdreeks {name} aangemaakt voor meetpunt {locatie}'.format(name=series.name.encode('utf-8'),locatie=mp.displayname.encode('utf-8')))  
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

def importMeetpunt(meetlocatie,waarnemer):
    ''' import meetlocatie as meetpunt '''
    try:
        meetpunt = meetlocatie.meetpunt
        logger.debug('Meetpunt found: '+ unicode(meetpunt))
    except ObjectDoesNotExist:
        # create meetpunt using  existing meetlocatie
        meetpunt = Meetpunt(meetlocatie_ptr_id = meetlocatie.pk,
            identifier = uuid(),
            displayname=meetlocatie.name,
            device='default',
            submitter=unicode(waarnemer),
            waarnemer=waarnemer)
        # copy meetlocatie properties to meetpunt 
        meetpunt.__dict__.update(meetlocatie.__dict__)
        meetpunt.save()
        logger.debug('Meetpunt created: ' + unicode(meetpunt))
    return meetpunt

def importSeries(series,waarnemer):
    ''' import timeseries as meetpunt/waarnemingen '''
    meetpunt = importMeetpunt(series.meetlocatie(), waarnemer)
    device = 'default'
    unit = series.unit
    try:
        name = series.parameter.name
    except:
        name = series.name
    numCreated = 0
    for dp in series.datapoints.all():
        try:
            w = meetpunt.waarneming_set.get(naam=name, waarnemer=waarnemer, datum=dp.date)
            if w.waarde != dp.value:
                w.waarde = dp.pvalue
                w.save()
        except:
            w = meetpunt.waarneming_set.create(naam=name, waarnemer=waarnemer, datum=dp.date, waarde=dp.value, device=device, eenheid=unit)
            numCreated += 1
    return numCreated


# from models import Waarnemer
# from acacia.data.models import Series
# 
# w = Waarnemer.objects.get(achternaam='Test')
# s = Series.objects.get(pk=2823)
# importSeries(s,w)
        
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

# updates coordinates of all measurements on cartodb
def updateCartodbLocation(cartodb, mps, table = None):
    if not table:
        table = cartodb.datatable
    for m in mps:
        print m
        
        regio = m.projectlocatie.name
        meetpunt = m.name.replace("'", "''")
        p = m.location
        p.transform(4326)

        logger.debug('Actualiseren cartodb meetpuntlocatie {meetpunt}'.format(meetpunt=m))
        sql = "UPDATE {table} SET the_geom = CDB_LatLng({y},{x}) WHERE regio='{regio}' AND meetpunt='{meetpunt}'"\
            .format(table=table, x=p.x,y=p.y,meetpunt=meetpunt,regio=regio)
        logger.debug(sql)
        ok = cartodb.runsql(sql)
        sql = "UPDATE {table} SET the_geom_webmercator = ST_Transform(CDB_LatLng({y},{x}),3875) WHERE regio='{regio}' AND meetpunt='{meetpunt}'"\
            .format(table=table, x=p.x,y=p.y,meetpunt=meetpunt,regio=regio)
        logger.debug(sql)
        ok = cartodb.runsql(sql)

# this version replaces ALL measurements of a meetpunt
def exportCartodb(cartodb, mps, table = None):
    if not table:
        table = cartodb.datatable
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
        # TODO: add regio to where clause
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
def exportCartodb2(cartodb, waarnemingen, table = None):
    if not table:
        table = cartodb.datatable
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
            # TODO: add region to where clause
            sql = "DELETE FROM {table} WHERE waarnemer='{waarnemer}' AND meetpunt='{meetpunt}' AND datum in ({dates})".format(table=table, waarnemer=unicode(m.waarnemer), meetpunt=meetpunt, dates=datums)
            cartodb.runsql(sql)
            sql = 'INSERT INTO {table} (the_geom,diepondiep,charturl,meetpunt,waarnemer,regio,datum,ec) VALUES '.format(table=table) + values
            cartodb.runsql(sql)
                
def processTriggers(mps):
    
    from acacia.data.events.messenger import Messenger
    
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
                msg = 'No alarms triggered for trigger {name} since {date}'.format(date=start, name=e.trigger.name)
            logger.debug(msg)
