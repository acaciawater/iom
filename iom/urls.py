"""iom URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url, patterns
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from iom.views import HomeView, WaarnemerDetailView, MeetpuntDetailView

urlpatterns = [
    url(r'^$',HomeView.as_view(),name='home'),
    url(r'^home$',HomeView.as_view(),name='home'),
    url(r'^waarnemer/(?P<pk>\d+)$',WaarnemerDetailView.as_view(),name='waarnemer-detail'),
    url(r'^get/series/(?P<pk>\d+)/$', 'acacia.data.views.SeriesToDict'),
    url(r'^meetpunt/(?P<pk>\d+)$',MeetpuntDetailView.as_view(),name='meetpunt-detail'),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),    
    url(r'^data/', include('acacia.data.urls',namespace='acacia')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

