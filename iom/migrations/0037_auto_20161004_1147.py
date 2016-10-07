# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0009_auto_20160928_2352'),
        ('iom', '0036_auto_20160621_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='akvoflow',
            name='projectlocatie',
            field=models.OneToOneField(default=1, to='data.ProjectLocatie'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cartodb',
            name='projectlocatie',
            field=models.OneToOneField(default=1, to='data.ProjectLocatie'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cartodb',
            name='viz',
            field=models.CharField(max_length=100, verbose_name=b'Visualisatie'),
        ),
    ]
