'''
Created on Jun 12, 2015

@author: theo
'''
from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.views.generic.edit import UpdateView
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from models import Waarnemer, Meetpunt, Waarneming, CartoDb, AkvoFlow, Waarneming, Logo
from acacia.data.models import Project, Datasource
import json
import pandas as pd
import locale
import datetime, pytz

from django.core import serializers
from django.db.models.aggregates import Max
from operator import pos

def JsonResponse(request, objects):
    params = request.REQUEST # cant use GET here: values are lists
    queryset = objects.filter(**params) if params else objects.all() if hasattr(objects,'all') else objects
    return HttpResponse(serializers.serialize('json', queryset), content_type='application/json')

def get_waarnemers(request):
    return JsonResponse(request, Waarnemer.objects)

def get_meetpunten(request):
    return JsonResponse(request, Meetpunt.objects)

def get_waarnemingen(request):
    return JsonResponse(request, Waarneming.objects)

def WaarnemingenToDict(request, pk):
    ''' dict for use in waarnemingen detail view '''
    tz = timezone.get_current_timezone()
    locale.setlocale(locale.LC_ALL,'nl_NL.utf8')
    
    mp = get_object_or_404(Meetpunt,pk=pk)
    waarnemingen = mp.waarneming_set.all()

    def diep(w):
        if w.naam.endswith('ndiep'):
            return 'ondiep'
        elif w.naam.endswith('iep'):
            return 'diep'
        else:
            return '&nbsp;'

    dct = [{'date': w.datum, 'EC': '%.2f' % (w.waarde/1000), 'diep': diep(w),'foto': '<a href="{f}"><img class="foto" src="{f}"/></a>'.format(f=w.foto_url) if w.foto_url else '-' } for w in waarnemingen]
    dct.sort(key=lambda x: x['date'],reverse=True)
    #j = json.dumps(dct, default=lambda x: x.astimezone(tz).strftime('%c'))
    j = json.dumps(dct, default=lambda x: x.astimezone(tz).strftime('%a %d %b %Y %H:%M'))
    return HttpResponse(j, content_type='application/json')

def DatapointsToDict(request, pk):
    ''' dict for use in external detail view '''
    tz = timezone.get_current_timezone()
    locale.setlocale(locale.LC_ALL,'nl_NL.utf8')
    
    mp = get_object_or_404(Meetpunt,pk=pk)
    dct = []
    for s in mp.series_set.all():
        for p in s.datapoints.all():
            dct.append({'date': p.date, 'EC': p.value, 'unit': s.unit})
    dct.sort(key=lambda x: x['date'],reverse=True)
    j = json.dumps(dct, default=lambda x: x.astimezone(tz).strftime('%c'))
    return HttpResponse(j, content_type='application/json')
    
class ContextMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['logos'] = Logo.objects.all()
        context['cartodb'] = get_object_or_404(CartoDb, pk=settings.CARTODB_ID)
        context['akvo'] = get_object_or_404(AkvoFlow, pk=settings.AKVOFLOW_ID)
        context['project'] = get_object_or_404(Project,pk=1)

        # get last measurement
        w = Waarneming.objects.all().order_by('-datum')
        context['laatste'] = w[0] if w else None

        # get layer number and date filter from query params
        if hasattr(self, 'request'):
            context['layer'] = self.request.GET.get('layer', 0) # layer 1 = changes, layer 0 = measurements
            context['start'] = self.request.GET.get('start', None)
            context['stop'] = self.request.GET.get('stop', None)
            context['search'] = self.request.GET.get('search', None)
        return context

from django.db.models import Count

class HomeView(ContextMixin,TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # build iterable for waarnemers with at least 1 measurement and sort descending by number of measurements
        if 'search' in self.request.GET:
            term = self.request.GET['search']
            waarnemers = Waarnemer.objects.filter(Q(achternaam__icontains=term) | Q(voornaam__icontains=term) | Q(meetpunt__displayname__contains=term))\
                .annotate(wcount=Count('waarneming'))\
                .filter(wcount__gt=0).order_by('-wcount')
        else:
            waarnemers = Waarnemer.objects.annotate(wcount=Count('waarneming'),wlast=Max('waarneming__datum')).filter(wcount__gt=0).order_by('-wlast')
        context['waarnemers'] = waarnemers
        context['sources'] = Datasource.objects.all()
        context['maptype'] = 'ROADMAP'
        return context

class ExternalSourcesView(HomeView):
    template_name = 'external.html'
    
    def get_context_data(self, **kwargs):
        context = super(ExternalSourcesView, self).get_context_data(**kwargs)
        context['sources'] = Datasource.objects.all()
        return context

class WaarnemerDetailView(ContextMixin,DetailView):
    template_name = 'waarnemer-detail.html'
    model = Waarnemer    

    def get_context_data(self, **kwargs):
        context = super(WaarnemerDetailView, self).get_context_data(**kwargs)
        waarnemer = self.get_object();
        # get list of unique measuring locations where this waarnemer has taken measurements
        if 'search' in self.request.GET:
            term = self.request.GET['search']
            mps = list(set([w.locatie for w in waarnemer.waarneming_set.filter(Q(locatie__name__icontains=term)|
                                                                      Q(locatie__displayname__icontains=term))]))
        else:
            mps = list(set([w.locatie for w in waarnemer.waarneming_set.all()]))
        def _dosort(w):
            laatste = w.laatste_waarneming()
            return laatste.datum if laatste else datetime.datetime.now(pytz.UTC)
        mps.sort(key = _dosort, reverse = True)
        context['meetpunten'] = mps

        # get bounding box
        if mps:
            import numpy as np
            coords = np.array([m.latlng() for m in mps])
            nw = np.amin(coords,axis=0)
            se = np.amax(coords,axis=0)
            context['bounds'] = [[nw[0],nw[1]],[se[0],se[1]]]
        return context

class DatasourceDetailView(ContextMixin,DetailView):
    template_name = 'external-detail.html'
    model = Datasource    

    def get_context_data(self, **kwargs):
        context = ContextMixin.get_context_data(self, **kwargs)
        source = self.get_object();
        # get list of unique measuring locations
        if 'search' in self.request.GET:
            term = self.request.GET['search']
            mps = [loc.meetpunt for loc in source.locations.filter(Q(name__icontains=term) | Q(description__icontains=term)) ]
        else:
            mps = [loc.meetpunt for loc in source.locations.all()]
        
        for m in mps:
            m.laatste = m.datum_laatste_waarneming() or datetime.datetime(1900,1,1,1,0,0,tzinfo=pytz.utc)
            
        context['meetpunten'] = sorted(mps, key=lambda x: x.laatste,reverse=True)
        return context

class MeetpuntDetailView(ContextMixin,DetailView):
    template_name = 'meetpunt-grafiek.html'
    model = Meetpunt    

    def get_context_data(self, **kwargs):
        context = super(MeetpuntDetailView, self).get_context_data(**kwargs)
        meetpunt = self.get_object();
        latlon = meetpunt.latlon()
        context['location'] = latlon
        context['zoom'] = 16
        context['maptype'] = 'SATELLITE'
        context['apikey'] = settings.GOOGLE_MAPS_API_KEY
        return context

class ExternalSeriesView(MeetpuntDetailView):
    template_name = 'external-grafiek.html'

class UploadPhotoView(UpdateView):
    model = Meetpunt
    fields = ['photo',]
    template_name_suffix = '_photo_form'

def MeetpuntFromCarto(request, id):
    ''' Show meetpunt using cartodb id '''
    for cartodb in CartoDb.objects.all():
        sql = 'select * from {table} where cartodb_id={id}'.format(table=cartodb.datatable,id=id)
        try:
            result = json.loads(cartodb.runsql(sql).read())
            row = result['rows'][0]
            mp = row['meetpunt']
            regio = row['regio']
            mp = get_object_or_404(Meetpunt,name=mp,projectlocatie__name=regio)
            return redirect('meetpunt-detail',mp.pk)
        except:
            pass
        break
    
# from .tasks import import_Akvo
# 
# @login_required
# def importAkvo(request):
#     nextpage = request.GET['next']
#     import_Akvo(request.user.username)
#     return redirect(nextpage)

def phones(request):
    pass
