'''
Created on Jun 18, 2015

@author: theo
'''
import os
from django.contrib.gis.utils import LayerMapping
from models import Watergang, watergang_mapping

shp = '/media/sf_F_DRIVE/projdirs/iom/waterdeel_09W.shp'

def run(shp=shp,verbose=True):
    lm = LayerMapping(Watergang, shp, watergang_mapping,
                      transform=False, encoding='iso-8859-1')

    lm.save(strict=True, verbose=verbose)