# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0018_auto_20151023_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='photo_url',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='waarnemer',
            name='akvoname',
            field=models.CharField(max_length=40, null=True, verbose_name=b'Akvo-Id', blank=True),
        ),
    ]
