'''
Created on Jul 5, 2015

@author: theo
'''
from django.forms import ModelForm
from django.forms import forms 
from acacia.data.models import DataPoint
from iom.models import Meetpunt

class DatapointForm(ModelForm):
    model = DataPoint
    
class UploadPhotoForm(ModelForm):
    model = Meetpunt
    fields = ['photo',]

    
class RegUserForm(forms.Form):
    # akvo data
    gebied = forms.CharField(max_length=100)
    naam = forms.CharField(max_length=100)
    deviceid = forms.CharField(max_length=100)
    
    #acacia data
    voornaam = forms.CharField(label='voornaam',max_length=100)
    tussenvoegsel = forms.CharField(label='tussenvoegsel',max_length=100)
    achternaam = forms.CharField(label='achternaam',max_length=100)
    email = forms.EmailField()
    telefoon = forms.CharField()
