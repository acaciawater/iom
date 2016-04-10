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
from .models import Waarnemer, Meetpunt, CartoDb
from acacia.data.models import Project
import json
import pandas as pd
import locale
from iom.models import AkvoFlow, Waarneming

def WaarnemingenToDict(request, pk):
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
    dct.sort(key=lambda x: x['date'])
    j = json.dumps(dct, default=lambda x: x.astimezone(tz).strftime('%c'))
    return HttpResponse(j, content_type='application/json')

class ContextMixin(object):
    ''' adds cartodb and akvo config to context '''
    def get_context_data(self, **kwargs):
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['cartodb'] = get_object_or_404(CartoDb, pk=settings.CARTODB_ID)
        context['akvo'] = get_object_or_404(AkvoFlow, pk=settings.AKVOFLOW_ID)
        context['project'] = get_object_or_404(Project,pk=1)
        w = Waarneming.objects.all().order_by('-datum')
        context['laatste'] = w[0] if w else None
        return context

class HomeView(ContextMixin,TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        content = []
        meetpunten = Meetpunt.objects.all() 
        for mp in meetpunten:
            pos = mp.latlon()
            content.append({'meetpunt': mp.pk,
                            'name': mp.name,
                            'lat': pos.y,
                            'lon': pos.x,
                            'url': ''#reverse('meetpunt-info', args=[mp.id]),
                            })
        waarnemers = list(Waarnemer.objects.all())
        waarnemers.sort(key = lambda x: -x.aantal_waarnemingen())
        actief = [w for w in waarnemers if w.waarneming_set]
        context['waarnemers'] = waarnemers
        context['actief'] = actief
        context['meetpunten'] = meetpunten
        context['content'] = json.dumps(content)
        context['maptype'] = 'ROADMAP'
        return context

class WaarnemerDetailView(ContextMixin,DetailView):
    template_name = 'waarnemer-detail.html'
    model = Waarnemer    

    def get_context_data(self, **kwargs):
        context = super(WaarnemerDetailView, self).get_context_data(**kwargs)
        waarnemer = self.get_object();
        context['meetpunten'] = waarnemer.meetpunt_set.all()
        return context

class MeetpuntDetailView(ContextMixin,DetailView):
    template_name = 'meetpunt-grafiek.html'
    model = Meetpunt    

    def get_context_data(self, **kwargs):
        context = super(MeetpuntDetailView, self).get_context_data(**kwargs)
        meetpunt = self.get_object();
        latlon = meetpunt.latlon()
        context['location'] = latlon
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
