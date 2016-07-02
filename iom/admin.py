'''
Created on Jun 16, 2015

@author: theo
'''
from django.contrib import admin
from django import forms
from django.forms import Textarea
from django.contrib.gis.db import models
from .models import UserProfile, Adres, Waarnemer, Meetpunt, Organisatie, AkvoFlow, CartoDb, Waarneming, Phone
from acacia.data.models import DataPoint, ManualSeries
from acacia.data.events.models import Event

from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .util import maak_meetpunt_grafiek, zoek_tijdreeksen, exportCartodb, exportCartodb2

import re
from iom.models import Waarneming, Alias, Logo, RegisteredUser
from iom import util

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class DataPointInline(admin.TabularInline):
#class DataPointInline(nested_admin.TabularInline):
    model = DataPoint

class SeriesInline(admin.StackedInline):
#class SeriesInline(nested_admin.NestedStackedInline):
    model = ManualSeries
    fields = ('name',)
    inlines = (DataPointInline,)
    verbose_name = 'Tijdreeks'
    verbose_name_plural = 'Tijdreeksen'

def maak_grafiek(modeladmin, request, queryset):
    for m in queryset:
        maak_meetpunt_grafiek(m,request.user)
maak_grafiek.short_description = "Maak grafieken voor geselecteerde meetpunten"

def update_series(modeladmin, request, queryset):
    util.updateSeries(queryset, request.user)
update_series.short_description = 'Tijdreeksen actualiseren van geselecteerde meetpunten'

class WaarnemingInline(admin.TabularInline):
    model = Waarneming
    exclude = ('opmerking',)
    extra = 0

def update_cdb_meetpunten(modeladmin, request, queryset):
    util.updateSeries(queryset, request.user)
    util.updateCartodb(CartoDb.objects.get(pk=1), queryset)
update_cdb_meetpunten.short_description = 'cartodb en tijdreeksen actualiseren met waarnemingen van geselecteerde meetpunten'

def update_cdb_waarnemers(modeladmin, request, queryset):
    mps = []
    for w in queryset:
        mps.extend(w.meetpunt_set.all())
    util.updateSeries(mps, request.user)
    util.updateCartodb(CartoDb.objects.get(pk=1), mps)
update_cdb_waarnemers.short_description = 'cartodb en tijdreeksen actualiseren voor meetpunten van geselecteerde waarnemers'

def export_cdb_waarnemingen(modeladmin, request, queryset):
    util.exportCartodb2(CartoDb.objects.get(pk=1), queryset, 'allemetingen')
export_cdb_waarnemingen.short_description = 'geselecteerde waarnemingen exporteren naar cartodb'

def export_cdb_meetpunten(modeladmin, request, queryset):
    util.exportCartodb(CartoDb.objects.get(pk=1), queryset, 'allemetingen')
export_cdb_meetpunten.short_description = 'geselecteerde meetpunten exporteren naar cartodb'

class EventInline(admin.TabularInline):
    model = Event

def link_series1(modeladmin, request, queryset):
    for m in queryset:
        series = zoek_tijdreeksen(m.location,1)
        for s in series:
            if not s.mlocatie:
                s.mlocatie = m
                s.save()
link_series1.short_description = 'Koppel gerelateerde tijdreeksen aan geselecteerde meetpunten'

def link_series(modeladmin, request, queryset):
    for m in queryset:
        for cs in m.chart.series.all():
            for s in [cs.series, cs.series2]:
                if s and not s.mlocatie:
                    s.mlocatie = m
                    s.save()
link_series.short_description = 'Koppel gerelateerde tijdreeksen aan geselecteerde meetpunten'
    
@admin.register(Meetpunt)
class MeetpuntAdmin(admin.ModelAdmin):
#class MeetpuntAdmin(nested_admin.NestedAdmin):
    actions = [maak_grafiek,update_series,update_cdb_meetpunten,link_series,export_cdb_meetpunten]
    list_display = ('name', 'waarnemer', 'displayname', 'description', 'aantal_waarnemingen', 'photo')
    list_filter = ('waarnemer', )
    inlines = [WaarnemingInline,]
    search_fields = ('name', 'waarnemer__achternaam', )
    fields = ('name', 'waarnemer', 'location', 'photo_url', 'chart_thumbnail', 'description',)
    formfield_overrides = {models.PointField:{'widget': Textarea}}
    
class AdresForm(forms.ModelForm):
    model = Adres
    
    def clean_postcode(self):
        pattern = r'\d{4}\s*[A-Za-z]{2}'
        data = self.cleaned_data['postcode']
        if re.search(pattern, data) is None:
            raise ValidationError('Onjuiste postcode')
        return data

@admin.register(Adres)
class AdresAdmin(admin.ModelAdmin):
    form = AdresForm
    fieldsets = (
                  ('', {'fields': (('straat', 'huisnummer', 'toevoeging'),('postcode', 'plaats')),
                        'classes': ('grp-collapse grp-open',),
                       }
                  ),
                )
    
@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    list_display = ('alias', 'waarnemer')
    list_filter = ('waarnemer', )
    search_fields = ('alias', 'waarnemer', )

class AliasInline(admin.TabularInline):
    model = Alias
    extra = 0

@admin.register(Waarnemer)
class WaarnemerAdmin(admin.ModelAdmin):
    actions = [update_cdb_waarnemers,]        
    list_display = ('achternaam', 'tussenvoegsel', 'voornaam', 'organisatie', 'aantal_meetpunten', 'aantal_waarnemingen')
    list_filter = ('achternaam', 'organisatie', )
    search_fields = ('achternaam', 'voornaam', )
    ordering = ('achternaam', )
    inlines = [AliasInline]
    
@admin.register(Organisatie)
class OrganisatieAdmin(admin.ModelAdmin):        
    raw_id_fields = ('adres',)
    autocomplete_lookup_fields = {
        'fk': ['adres',],
    }
    
@admin.register(AkvoFlow)
class AkvoAdmin(admin.ModelAdmin):
    list_display = ('name', 'instance', 'description')
    list_filter = ('name', )
    search_fields = ('name', 'instance', )

@admin.register(CartoDb)
class CartodbAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'description')
    list_filter = ('name', )
    search_fields = ('name', 'url', )

@admin.register(Waarneming)
class WaarnemingAdmin(admin.ModelAdmin):
    list_display = ('naam', 'datum', 'waarnemer', 'locatie', 'device','waarde', 'eenheid', 'photo')
    list_filter = ('naam', 'waarnemer', 'locatie', 'device', 'datum' )
    actions = [export_cdb_waarnemingen,]

@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ('name','order','img')

@admin.register(RegisteredUser)
class RegisteredUserAdmin(admin.ModelAdmin):
    exclude = ('website', 'status', 'organisatie')
    fieldsets = (
                  ('Persoonsgegevens', {'fields': (('voornaam', 'tussenvoegsel', 'achternaam'),('email', 'telefoon')),
                        'classes': ('grp-collapse grp-open',),
                       }
                  ),
                  ('Telefoon', {'fields': ('akvo_name', 'device_id',),
                        'classes': ('grp-collapse grp-open',),
                       }
                  ),
                )
    
@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ('device_id','last_contact', 'latitude', 'longitude')
