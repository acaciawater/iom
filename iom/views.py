'''
Created on Jun 12, 2015

@author: theo
'''
from django.views.generic import TemplateView, DetailView
from .models import Waarnemer, Meetpunt
import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse

class HomeView(TemplateView):
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
        
        context['waarnemers'] = Waarnemer.objects.all()
        context['meetpunten'] = meetpunten
        context['content'] = json.dumps(content)
        context['maptype'] = 'ROADMAP'
        return context

class WaarnemerDetailView(DetailView):
    template_name = 'waarnemer-detail.html'
    model = Waarnemer    

    def get_context_data(self, **kwargs):
        context = super(WaarnemerDetailView, self).get_context_data(**kwargs)
        waarnemer = self.get_object();
        context['meetpunten'] = waarnemer.meetpunt_set.all()
        return context

class MeetpuntDetailView(DetailView):
    template_name = 'meetpunt-detail.html'
    model = Meetpunt    

    def get_context_data(self, **kwargs):
        context = super(MeetpuntDetailView, self).get_context_data(**kwargs)
        meetpunt = self.get_object();
        latlon = meetpunt.latlon()
        context['location'] = latlon

        series = meetpunt.get_series('EC')
        if series is not None:
            paginator = Paginator(series.datapoints.all(),14)
            page = self.request.GET.get('page')
            try:
                points = paginator.page(page)
            except PageNotAnInteger:
                points = paginator.page(1)
            except EmptyPage:
                points = paginator.page(paginator.num_pages)
            context['points'] = points
            context['series'] = series
        return context