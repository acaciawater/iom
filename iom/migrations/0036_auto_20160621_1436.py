# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0035_auto_20160607_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartodb',
            name='viz',
            field=models.CharField(max_length=100, verbose_name=b'Visualisatie metingen'),
        ),
    ]
