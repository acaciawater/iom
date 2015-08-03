# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0003_auto_20150618_1424'),
    ]

    operations = [
        migrations.CreateModel(
            name='Watergang',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gml_id', models.CharField(max_length=254)),
                ('identifica', models.CharField(max_length=20)),
                ('brontype', models.CharField(max_length=11)),
                ('bronbeschr', models.CharField(max_length=139)),
                ('bronactual', models.CharField(max_length=10)),
                ('bronnauwke', models.FloatField()),
                ('dimensie', models.CharField(max_length=2)),
                ('objectbegi', models.CharField(max_length=23)),
                ('versiebegi', models.CharField(max_length=23)),
                ('visualisat', models.IntegerField()),
                ('tdncode', models.IntegerField()),
                ('breedtekla', models.CharField(max_length=13)),
                ('functie', models.CharField(max_length=14)),
                ('hoofdafwat', models.CharField(max_length=3)),
                ('hoogtenive', models.IntegerField()),
                ('status', models.CharField(max_length=10)),
                ('typeinfras', models.CharField(max_length=18)),
                ('typewater', models.CharField(max_length=23)),
                ('voorkomenw', models.CharField(max_length=8)),
                ('naamnl', models.CharField(max_length=24)),
                ('fysiekvoor', models.CharField(max_length=21)),
                ('sluisnaam', models.CharField(max_length=22)),
                ('geom', django.contrib.gis.db.models.fields.LineStringField(srid=28992)),
            ],
        ),
        migrations.AlterField(
            model_name='eigenaar',
            name='voornaam',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='begin',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='watergang',
            field=models.ForeignKey(default=1, to='iom.Watergang'),
            preserve_default=False,
        ),
    ]
