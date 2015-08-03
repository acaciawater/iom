# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import string

def apply_numbers(apps, schema_editor):
    Meetpunt = apps.get_model("iom", "Meetpunt")
    for m in Meetpunt.objects.all():
        try:
            # nunmber is after last dot
            pos = string.rfind(m.name,'.')
            m.nummer = int(m.name[pos+1:])
            m.save()
        except:
            pass
        
class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0011_auto_20150708_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='nummer',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.RunPython(apply_numbers)
    ]
