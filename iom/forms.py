'''
Created on Jul 5, 2015

@author: theo
'''
from django.forms import ModelForm
from acacia.data.models import DataPoint

class DatapointForm(ModelForm):
    model = DataPoint

    