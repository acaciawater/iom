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
from .models import Waarnemer, Meetpunt, Waarneming, CartoDb, AkvoFlow, Waarneming, Logo
from acacia.data.models import Project
import json
import pandas as pd
import locale
import datetime, pytz

from django.core import serializers

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

    dct = [{'date': w.datum, 'EC': w.waarde, 'diep': diep(w),'foto': '<a href="{f}"><img class="foto" src="{f}"/></a>'.format(f=w.foto_url) if w.foto_url else '-' } for w in waarnemingen]
    dct.sort(key=lambda x: x['date'],reverse=True)
    j = json.dumps(dct, default=lambda x: x.astimezone(tz).strftime('%c'))
    return HttpResponse(j, content_type='application/json')
    
class ContextMixin(object):
    ''' adds cartodb and akvo config to context '''
    def get_context_data(self, **kwargs):
        context = super(ContextMixin, self).get_context_data(**kwargs)
        
        context['cartodb'] = get_object_or_404(CartoDb, pk=settings.CARTODB_ID)
        context['akvo'] = get_object_or_404(AkvoFlow, pk=settings.AKVOFLOW_ID)
        context['project'] = get_object_or_404(Project,pk=1)
        context['logos'] = Logo.objects.all()
 
        # get last measurement
        w = Waarneming.objects.all().order_by('-datum')
        context['laatste'] = w[0] if w else None

        # get layer number and date filter from query params
        if hasattr(self, 'request'):
            context['layer'] = self.request.GET.get('layer', 1) # layer 0 = changes, layer 1 = measurements
            context['start'] = self.request.GET.get('start', None)
            context['stop'] = self.request.GET.get('stop', None)
        
        return context

from django.db.models import Count

class HomeView(ContextMixin,TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # build iterable for waarnemers with at least 1 measurement and sort descending by number of measurements
        waarnemers = Waarnemer.objects.annotate(wcount=Count('waarneming')).filter(wcount__gt=0).order_by('-wcount')
        context['waarnemers'] = waarnemers
        context['maptype'] = 'ROADMAP'
        return context

class WaarnemerDetailView(ContextMixin,DetailView):
    template_name = 'waarnemer-detail.html'
    model = Waarnemer    

    def get_context_data(self, **kwargs):
        context = super(WaarnemerDetailView, self).get_context_data(**kwargs)
        waarnemer = self.get_object();
        # get list of unique measuring locations where this waarnemer has taken measurments
        mps = list(set([w.locatie for w in waarnemer.waarneming_set.all()]))
        def _dosort(w):
            laatste = w.laatste_waarneming()
            return laatste.datum if laatste else datetime.datetime.now(pytz.UTC)
        mps.sort(key = _dosort, reverse = True)
        context['meetpunten'] = mps 
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
    
class UploadPhotoView(UpdateView):
    model = Meetpunt
    fields = ['photo',]
    template_name_suffix = '_photo_form'

from .tasks import import_Akvo

@login_required
def importAkvo(request):
    nextpage = request.GET['next']
    import_Akvo(request.user.username)
    return redirect(nextpage)

def phones(request):
    pass
