# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Adres',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('postcode', models.CharField(max_length=6)),
                ('huisnummer', models.IntegerField()),
                ('plaats', models.CharField(max_length=100)),
                ('straat', models.CharField(max_length=100)),
                ('toevoeging', models.CharField(max_length=20, null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Adressen',
            },
        ),
        migrations.CreateModel(
            name='Eigenaar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('initialen', models.CharField(max_length=6)),
                ('voornaam', models.CharField(max_length=20)),
                ('achternaam', models.CharField(max_length=40)),
                ('adres', models.ForeignKey(to='iom.Adres')),
            ],
            options={
                'verbose_name_plural': 'Eigenaren',
            },
        ),
        migrations.CreateModel(
            name='Meetpunt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ident', models.CharField(max_length=20)),
                ('locatie', django.contrib.gis.db.models.fields.PointField(help_text=b'Locatie meetpunt in Rijksdriehoekstelsel coordinaten', srid=28992)),
                ('begin', models.DateTimeField(auto_now=True)),
                ('einde', models.DateTimeField(null=True, blank=True)),
                ('eigenaar', models.ForeignKey(to='iom.Eigenaar')),
            ],
            options={
                'verbose_name_plural': 'Meetpunten',
            },
        ),
    ]
