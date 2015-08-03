'''
Created on Jun 14, 2015

@author: theo
'''
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from acacia.data.models import MeetLocatie, Chart

# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models as geo

class Watergang(geo.Model):
    gml_id = models.CharField(max_length=254)
    identifica = models.CharField(max_length=20,verbose_name = 'identificatie')
    brontype = models.CharField(max_length=11)
    bronbeschr = models.CharField(max_length=139)
    bronactual = models.CharField(max_length=10)
    bronnauwke = models.FloatField()
    dimensie = models.CharField(max_length=2)
    objectbegi = models.CharField(max_length=23)
    versiebegi = models.CharField(max_length=23)
    visualisat = models.IntegerField()
    tdncode = models.IntegerField()
    breedtekla = models.CharField(max_length=13, verbose_name = 'breedteklasse')
    functie = models.CharField(max_length=14)
    hoofdafwat = models.CharField(max_length=3, verbose_name='hoofdafwatering')
    hoogtenive = models.IntegerField()
    status = models.CharField(max_length=10)
    typeinfras = models.CharField(max_length=18)
    typewater = models.CharField(max_length=23, verbose_name = 'type watergang')
    voorkomenw = models.CharField(max_length=8)
    naamnl = models.CharField(max_length=24,verbose_name = 'naam')
    fysiekvoor = models.CharField(max_length=21)
    #sluisnaam = models.CharField(max_length=22)
    geom = geo.LineStringField(srid=28992)
    objects = geo.GeoManager()
    
    @staticmethod
    def autocomplete_search_fields():
        return ("identifica__icontains", "naamnl__icontains")

    def __unicode__(self):
        return self.identifica
    
    class Meta:
        verbose_name_plural = 'Watergangen'
        
# Auto-generated `LayerMapping` dictionary for Watergang model
watergang_mapping = {
    'gml_id' : 'gml_id',
    'identifica' : 'identifica',
    'brontype' : 'brontype',
    'bronbeschr' : 'bronbeschr',
    'bronactual' : 'bronactual',
    'bronnauwke' : 'bronnauwke',
    'dimensie' : 'dimensie',
    'objectbegi' : 'objectBegi',
    'versiebegi' : 'versieBegi',
    'visualisat' : 'visualisat',
    'tdncode' : 'tdnCode',
    'breedtekla' : 'breedtekla',
    'functie' : 'functie',
    'hoofdafwat' : 'hoofdafwat',
    'hoogtenive' : 'hoogtenive',
    'status' : 'status',
    'typeinfras' : 'typeInfras',
    'typewater' : 'typeWater',
    'voorkomenw' : 'voorkomenW',
    'naamnl' : 'naamNL',
    'fysiekvoor' : 'fysiekVoor',
#    'sluisnaam' : 'sluisnaam',
    'geom' : 'LINESTRING',
}

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    image = models.ImageField(upload_to='images')

from django.db.models.signals import post_save

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
    
class Adres(models.Model):
    postcode = models.CharField(max_length=7)
    huisnummer = models.IntegerField()
    toevoeging = models.CharField(max_length=20,blank=True,null=True)
    straat = models.CharField(max_length=100)
    plaats = models.CharField(max_length=100)
    
    def __unicode__(self):
        return '%s %d%s, %s'% (self.straat, self.huisnummer, self.toevoeging or '', self.plaats)

    @staticmethod
    def autocomplete_search_fields():
        return ("plaats__icontains", "straat__icontains",)

    class Meta:
        verbose_name_plural = 'Adressen'

from django.core.validators import RegexValidator
phone_regex = RegexValidator(regex=r'^(?:\+)?[0-9\-]{10,11}$',
                             message="Ongeldig telefoonnummer")

class Organisatie(models.Model):
    naam = models.CharField(max_length=50)
    omschrijving = models.TextField(blank=True,null=True)
    website=models.URLField(blank=True)
    email = models.EmailField(blank=True)
    telefoon = models.CharField(max_length=16, validators=[phone_regex], blank=True)
    adres = models.ForeignKey(Adres, null=True, blank=True)

    def __unicode__(self):
        return self.naam

class Waarnemer(models.Model):
    initialen=models.CharField(max_length=6)
    voornaam=models.CharField(max_length=20,null=True,blank=True)
    tussenvoegsel=models.CharField(max_length=10,null=True,blank=True)
    achternaam=models.CharField(max_length=40)

    telefoon = models.CharField(max_length=16, validators=[phone_regex], blank=True)
    email=models.EmailField(blank=True)
    organisatie = models.ForeignKey(Organisatie, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('waarnemer-detail', args=[self.id])
    
    class Meta:
        verbose_name_plural = 'Waarnemers'
        ordering = ['achternaam']
        
    def __unicode__(self):
        if self.tussenvoegsel is None or self.tussenvoegsel == '':
            return '%s %s' % (self.initialen, self.achternaam)
        else:
            return '%s %s %s' % (self.initialen, self.tussenvoegsel, self.achternaam)

    def waarnemingen(self):
        w = sum([m.waarnemingen() for m in self.meetpunt_set.all()])
        return w
        
from django.db.models import Sum
    
class Meetpunt(MeetLocatie):
    nummer=models.IntegerField()
    waarnemer=models.ForeignKey(Waarnemer)
    begin=models.DateTimeField(null=True, blank=True)
    einde=models.DateTimeField(null=True, blank=True)
    watergang = models.ForeignKey(Watergang,null=True, blank=True)
    chart = models.ImageField(upload_to='charts', verbose_name='grafiek', help_text='Grafiek in popup op cartodb kaartje')
    
    class Meta:
        verbose_name_plural = 'Meetpunten'
                
    def get_series(self, name='EC'):
        series = [s for s in self.series() if s.name == name]
        return series[0] if len(series)>0 else None

    def waarnemingen(self):
        return sum([d.rows() for d in self.datasources.all()])
