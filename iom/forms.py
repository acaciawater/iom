'''
Created on Jul 5, 2015

@author: theo
'''
from django.forms import ModelForm
from acacia.data.models import DataPoint
from iom.models import Meetpunt

class DatapointForm(ModelForm):
    model = DataPoint
    
class UploadPhotoForm(ModelForm):
    model = Meetpunt
    fields = ['photo',]

    