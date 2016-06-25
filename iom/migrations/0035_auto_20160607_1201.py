# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0034_registereduser'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartodb',
            name='layer_sql',
            field=models.TextField(null=True, verbose_name=b'Aangepaste SQL voor kaartlaag', blank=True),
        ),
        migrations.AlterField(
            model_name='cartodb',
            name='sql_url',
            field=models.CharField(help_text=b'URL voor Cartodb SQL queries', max_length=100, verbose_name=b'SQL url'),
        ),
    ]
