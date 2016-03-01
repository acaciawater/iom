# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0029_auto_20160221_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartodb',
            name='datatable',
            field=models.CharField(default='waarnemingen', max_length=50, verbose_name=b'tabelnaam'),
            preserve_default=False,
        ),
    ]
