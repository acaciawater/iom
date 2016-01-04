# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0022_auto_20151023_1651'),
    ]

    operations = [
        migrations.CreateModel(
            name='CartoDb',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('url', models.CharField(max_length=100, verbose_name=b'Account')),
                ('viz', models.CharField(max_length=100, verbose_name=b'Visualisatie')),
                ('key', models.CharField(max_length=100, verbose_name=b'API key')),
                ('sql_url', models.CharField(max_length=100, verbose_name=b'SQL url')),
            ],
            options={
                'verbose_name': 'Cartodb config',
            },
        ),
        migrations.AlterModelOptions(
            name='akvoflow',
            options={'verbose_name': 'Akvoflow config'},
        ),
        migrations.AlterModelOptions(
            name='waarneming',
            options={'verbose_name_plural': 'Waarnemingen'},
        ),
        migrations.AlterField(
            model_name='akvoflow',
            name='name',
            field=models.CharField(unique=True, max_length=100),
        ),
    ]
