'''
Created on Jun 25, 2015

@author: theo
'''

# id    waarnemer    x    y
# 1    8    4.8284954947    53.1364957490
# 2    8    4.8252883370    53.1325750819
# 3    8    4.8360491579    53.1315492421
# 4    8    4.8395597771    53.1351640550
# 5    8    4.8351892086    53.1267381890
# 6    7    4.7978405316    53.1112986931
# 7    7    4.8065604012    53.1111783663
# 8    7    4.8086651973    53.1030555252
# 9    7    4.8143782153    53.1075082355
# 10    7    4.8229978564    53.0952320800
# 11    7    4.8272074486    53.1004679277
# 12    7    4.8152802707    53.0984819915

import csv
from acacia.data.models import ProjectLocatie
from iom.models import Meetpunt, Waarnemer
from django.contrib.gis.geos import Point
def import_meetpunten(fname):
    Meetpunt.objects.all().delete()
    pl = ProjectLocatie.objects.get(pk=1)
    with open(fname, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id = int(row['id'])
            x = float(row['x'])
            y = float(row['y'])
            wid = int(row['waarnemer'])
            p = Point(x,y,srid=4326)
            p.transform(28992)
            w = Waarnemer.objects.get(pk=wid)
            w.meetpunt_set.create(projectlocatie=pl, name='MP%d.%d'%(wid,id), location=p)
            