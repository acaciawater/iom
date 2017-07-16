'''
Created on Jul 15, 2017

@author: theo
'''
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authorization import DjangoAuthorization
from tastypie import fields
from tastypie.authentication import BasicAuthentication

from models import Waarnemer, Meetpunt, Waarneming
from tastypie.exceptions import InvalidFilterError
from django.contrib.gis.geos import Polygon

class WaarnemerResource(ModelResource):
    class Meta:
        queryset = Waarnemer.objects.all()
        resource_name = 'waarnemer'
        filtering = {'voornaam': ALL, 'achternaam': ALL}
        authentication = BasicAuthentication(realm='Texel Meet')
        authorization = DjangoAuthorization()
        excludes = ['email','telefoon']

def poly_from_bbox(bbox_val):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise InvalidFilterError("bbox must be in format 'left,bottom,right,top'")
    try:
        return Polygon.from_bbox( [float(p) for p in points])
    except ValueError:
        raise InvalidFilterError("bbox values must be floating point")

class MeetpuntResource(ModelResource):
    waarnemer = fields.ForeignKey(WaarnemerResource,'waarnemer')
    class Meta:
        queryset = Meetpunt.objects.all()
        resource_name = 'meetpunt'
        authentication = BasicAuthentication(realm='Texel Meet')
        authorization = DjangoAuthorization()
        excludes = ['chart_thumbnail', 'photo_url', 'image']
        filtering = {
            'name': ALL,
            'identifier': ALL,
            'device': ALL,
            'submitter': ALL,
            'waarnemer': ALL_WITH_RELATIONS,
            'location': ALL,
            'id': ALL,
            }

    def build_filters(self, filters=None):
        orm_filters = super(MeetpuntResource, self).build_filters(filters)
        if not filters:
            return orm_filters

        if 'bbox' in filters:
            orm_filters['location__within'] = poly_from_bbox(filters['bbox'])

        return orm_filters
        
class WaarnemingResource(ModelResource):
    
    waarnemer = fields.ForeignKey(WaarnemerResource,'waarnemer')
    meetpunt = fields.ForeignKey(MeetpuntResource,'locatie')

    class Meta:
        queryset = Waarneming.objects.all()
        resource_name = 'waarneming'
        authentication = BasicAuthentication(realm='Texel Meet')
        authorization = DjangoAuthorization()
        fields = ['datum','eenheid','waarde']
        filtering = {
            'naam': ALL,
            'waarnemer': ALL_WITH_RELATIONS,
            'meetpunt': ALL_WITH_RELATIONS,
            'device': ALL,
            'datum': ALL,
            'waarde': ALL,
            }
        