'''
Created on Jun 16, 2015

@author: theo
'''
from django.contrib import admin
from django import forms
from django.forms import Textarea
from django.contrib.gis.db import models
from .models import UserProfile, Adres, Waarnemer, Meetpunt, Watergang, Organisatie
from acacia.data.models import Series, DataPoint

from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

import re

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Watergang)
class WatergangAdmin(admin.ModelAdmin):
    list_display = ('identifica', 'naamnl', 'typewater', 'breedtekla', 'hoofdafwat')
    search_fields = ('identifica', 'naamnl', )
    list_filter = ('hoofdafwat', 'breedtekla', 'typewater')

class DataPointInline(admin.TabularInline):
    model = DataPoint

class SeriesInline(admin.TabularInline):
    model = Series
    inlines = (DataPointInline,)
            
@admin.register(Meetpunt)
class MeetpuntAdmin(admin.ModelAdmin):
    list_display = ('name', 'nummer', 'waarnemer')
    list_filter = ('waarnemer', )
    search_fields = ('name', 'nummer', 'waarnemer', )
    fields = ('waarnemer','nummer', 'location', 'watergang','description', )
    formfield_overrides = {models.PointField:{'widget': Textarea}}
    raw_id_fields = ('watergang',)
    autocomplete_lookup_fields = {
        'fk': ['watergang',],
    }
    
    def save_model(self,request,obj,form,change):
        obj.name = 'MP%d.%d' % (obj.waarnemer.id, obj.nummer)
        obj.save()

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
    
@admin.register(Waarnemer)
class WaarnemerAdmin(admin.ModelAdmin):        
    list_display = ('achternaam', 'tussenvoegsel', 'voornaam', 'organisatie')
    list_filter = ('achternaam', 'organisatie')
    search_fields = ('achternaam', 'voornaam', )
    ordering = ('achternaam', )

@admin.register(Organisatie)
class OrganisatieAdmin(admin.ModelAdmin):        
    raw_id_fields = ('adres',)
    autocomplete_lookup_fields = {
        'fk': ['adres',],
    }
