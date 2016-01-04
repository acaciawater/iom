# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0024_cartodb_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Phone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('imei', models.CharField(max_length=20)),
                ('phone_number', models.CharField(max_length=20)),
                ('device_id', models.CharField(max_length=20)),
                ('last_contact', models.DateTimeField(null=True)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
                ('accuracy', models.IntegerField(null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='akvoflow',
            options={'verbose_name': 'Akvoflow configuratie'},
        ),
        migrations.AlterModelOptions(
            name='cartodb',
            options={'verbose_name': 'Cartodb configuratie'},
        ),
    ]
