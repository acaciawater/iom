'''
Created on Jun 14, 2015

@author: theo
'''
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from acacia.data.models import MeetLocatie, Chart, ProjectLocatie

from django.contrib.gis.db import models as geo

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    image = models.ImageField(upload_to='images',blank=True,null=True)

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
phone_regex = RegexValidator(regex=r'^(?:\+)?[0-9\-]{10,11}$', message="Ongeldig telefoonnummer")

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
    initialen=models.CharField(max_length=6,null=True,blank=True)
    voornaam=models.CharField(max_length=20,null=True,blank=True)
    tussenvoegsel=models.CharField(max_length=10,null=True,blank=True)
    achternaam=models.CharField(max_length=40)

    telefoon = models.CharField(max_length=16, validators=[phone_regex], blank=True)
    email=models.EmailField(blank=True)
    organisatie = models.ForeignKey(Organisatie, blank=True, null=True)

    @property
    def alias(self):
        return ','.join([a.alias for a in self.alias_set.all()])
    
    def get_absolute_url(self):
        return reverse('waarnemer-detail', args=[self.id])
    
    class Meta:
        verbose_name_plural = 'Waarnemers'
        ordering = ['achternaam']
        
    def __unicode__(self):
        s = ''
        if self.initialen and len(self.initialen) > 0:
            s = self.initialen
            if s[-1] != '.':
                s += '.'
            s += ' '
        if self.tussenvoegsel and len(self.tussenvoegsel) > 0:
            s += self.tussenvoegsel + ' '
        return s + self.achternaam
    
    def fullname(self):
        s = ''
        if self.voornaam and len(self.voornaam) > 0:
            s = self.voornaam + ' '
        if self.tussenvoegsel and len(self.tussenvoegsel) > 0:
            s += self.tussenvoegsel + ' '
        return s + self.achternaam
        
    def aantal_meetpunten(self):
        return self.meetpunt_set.count()
    
    def aantal_waarnemingen(self):
        return self.waarneming_set.count()
    
    def laatste_waarneming(self):
        try:
            return self.waarneming_set.latest('datum')
        except:
            return None

    def projectlocaties(self):
        # alle projectlocaties waar deze waar=nemenr gemeten heeft
        return ','.join(set([mp.projectlocatie.name for mp in self.meetpunt_set.all()]))
    
class Alias(models.Model):        
    ''' alias voor Waarnemer (wordt gebruikt in Akvo Flow) '''
    alias = models.CharField(max_length=50)
    waarnemer = models.ForeignKey(Waarnemer)
    
    def __unicode__(self):
        return self.alias
    
    class Meta:
        verbose_name_plural = 'Aliassen'
        
class Meetpunt(MeetLocatie):
    from akvo import uuid
    # Akvo flow meetpunt gegevens
    identifier=models.CharField(max_length=50,default=uuid())
    displayname = models.CharField(max_length=100)
    submitter=models.CharField(max_length=50)
    device=models.CharField(max_length=50)
    photo_url=models.CharField(max_length=200,null=True,blank=True)
    #photo_orient = models.IntegerField(default=1) # exif orientation
    waarnemer=models.ForeignKey(Waarnemer)
    chart_thumbnail = models.ImageField(upload_to='thumbnails/charts', blank=True, null=True, verbose_name='voorbeeld', help_text='Grafiek in popup op cartodb kaartje')
    chart = models.ForeignKey(Chart, verbose_name='grafiek', help_text='Interactive grafiek',null=True,blank=True)
    
    def __unicode__(self):
        return self.name

    def chart_url(self):
        try:
            return self.chart.get_dash_url()
        except:
            return '#'
        
    def latlng(self):
        p = self.latlon()
        return [p.y,p.x]
    
    class Meta:        
        verbose_name_plural = 'Meetpunten'
                
    def get_series(self, name='EC'):
        series = [s for s in self.series() if s.name.startswith(name)]
        return series[0] if len(series)>0 else None

    def aantal_waarnemingen(self):
        return self.waarneming_set.count()
    
    def laatste_waarneming(self):
        try:
            waarnemingen = self.waarneming_set.all().order_by('-datum')
            return waarnemingen[0]
        except:
            return None
        
    def photo(self):
        return '<a href="{url}"><img src="{url}" height="60px"/></a>'.format(url=self.photo_url) if self.photo_url else ''
    photo.allow_tags=True

    def get_events(self):
        return [e for s in self.series() for e in s.event_set.all() ]
        
class Waarneming(models.Model):
    naam = models.CharField(max_length=100)
    waarnemer = models.ForeignKey(Waarnemer)
    locatie = models.ForeignKey(Meetpunt)
    device = models.CharField(max_length=50)
    datum = models.DateTimeField()
    eenheid = models.CharField(max_length=20)
    waarde = models.FloatField()
    foto_url = models.CharField(max_length=200,blank=True,null=True)
    #foto_orient = models.IntegerField(default=1) # exif orientation
    opmerking = models.TextField(blank=True,null=True)

    def photo(self):
        return '<a href="{url}"><img src="{url}" height="60px"/></a>'.format(url=self.foto_url) if self.foto_url else ''
    photo.allow_tags=True

    class Meta:
        verbose_name_plural = 'Waarnemingen'
        
class AkvoFlow(models.Model):
    ''' Akvo Flow configuratie '''
    projectlocatie = models.ForeignKey(ProjectLocatie)
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True, null=True)
    instance = models.CharField(max_length=100)
    key = models.CharField(max_length=100)    
    secret = models.CharField(max_length=100)
    storage = models.CharField(max_length=100) 
    regform = models.CharField(max_length=100,blank=True, null=True, verbose_name = 'Registratieformulier',help_text='Survey id van registratieformulier')
    monforms = models.CharField(max_length=100,blank=True, null=True, verbose_name = 'Monitoringformulier',help_text='Survey id van monitoringformulier')
    last_update = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'Akvoflow configuratie'        
        
    def __unicode__(self):
        return self.name
    
import urllib,urllib2

class CartoDb(models.Model):
    ''' Cartodb configuratie '''
    projectlocatie = models.OneToOneField(ProjectLocatie)
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=100,verbose_name='Account')
    viz = models.CharField(max_length=100,verbose_name='Visualisatie')    
    key = models.CharField(max_length=100,verbose_name='API key')
    sql_url = models.CharField(max_length=100,verbose_name='SQL url',help_text='URL voor Cartodb SQL queries')
    datatable = models.CharField(max_length=50,verbose_name='tabelnaam') # notused

    class Meta:
        verbose_name = 'Cartodb configuratie'        
        
    def __unicode__(self):
        return self.name
    
    @property
    def sql(self):
        from django.utils.safestring import mark_safe
        import re
        sql_string = re.sub(r'[\r\n]+',' ',self.layer_sql)
        safestring = mark_safe(sql_string)
        return safestring
    
    def runsql(self,sql):
        data = urllib.urlencode({'q': sql, 'api_key': self.key})
        request = urllib2.Request(url=self.sql_url, data=data)
        for i in range(3):
            try:
                return urllib2.urlopen(request)
            except urllib2.URLError as e:
                print e
            
class Phone(models.Model):
    imei = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    device_id = models.CharField(max_length=20)
    last_contact = models.DateTimeField(null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    accuracy = models.IntegerField(null=True)

    def __unicode__(self):
        return self.device_id
    
class Logo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank = True)
    logo = models.ImageField(upload_to='logos',blank= True, null=True)
    order = models.IntegerField(default=1)
    website = models.URLField(null=True,blank=True)
    display = models.BooleanField(default=True)

    def img(self):
        return '<a href="{url}"><img src="{img}" height="60px"/></a>'.format(url=self.logo.url, img=self.logo.url)
    img.allow_tags = True
        
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ('order',)

STATUS_CHOICES = (
                  ('O', 'geopend'),
                  ('V', 'aangevraagd'),
                  ('P', 'in behandeling'),
                  ('E', 'fout geconstateerd'),
                  ('R', 'geweigerd'),
                  ('A', 'geaccepteerd')
                  )
class RegisteredUser(Waarnemer):
    ''' user that is to be registered by an administrator '''
    website = models.CharField(max_length=100)
    akvo_name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100)
    status = models.CharField(max_length=1,choices = STATUS_CHOICES)
