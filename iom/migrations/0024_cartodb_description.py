# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0023_auto_20151025_1104'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartodb',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
    ]
