# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0004_auto_20150618_1537'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='watergang',
            options={'verbose_name_plural': 'Watergangen'},
        ),
        migrations.RemoveField(
            model_name='watergang',
            name='sluisnaam',
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='watergang',
            field=models.ForeignKey(blank=True, to='iom.Watergang', null=True),
        ),
        migrations.AlterField(
            model_name='watergang',
            name='breedtekla',
            field=models.CharField(max_length=13, verbose_name=b'breedteklasse'),
        ),
        migrations.AlterField(
            model_name='watergang',
            name='hoofdafwat',
            field=models.CharField(max_length=3, verbose_name=b'hoofdafwatering'),
        ),
        migrations.AlterField(
            model_name='watergang',
            name='identifica',
            field=models.CharField(max_length=20, verbose_name=b'identificatie'),
        ),
        migrations.AlterField(
            model_name='watergang',
            name='naamnl',
            field=models.CharField(max_length=24, verbose_name=b'naam'),
        ),
        migrations.AlterField(
            model_name='watergang',
            name='typewater',
            field=models.CharField(max_length=23, verbose_name=b'type watergang'),
        ),
    ]
