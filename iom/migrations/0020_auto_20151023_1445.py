# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0019_auto_20151023_1141'),
    ]

    operations = [
        migrations.CreateModel(
            name='Waarneming',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datum', models.DateTimeField()),
                ('naam', models.CharField(max_length=20)),
                ('eenheid', models.CharField(max_length=20)),
                ('waarde', models.FloatField()),
                ('foto_url', models.CharField(max_length=200, null=True, blank=True)),
                ('opmerking', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='akvoflow',
            options={'verbose_name': 'Akvoflow API', 'verbose_name_plural': 'Akvoflow API'},
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='photo_url',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='waarneming',
            name='locatie',
            field=models.ForeignKey(to='iom.Meetpunt'),
        ),
        migrations.AddField(
            model_name='waarneming',
            name='waarnemer',
            field=models.ForeignKey(to='iom.Waarnemer'),
        ),
    ]
