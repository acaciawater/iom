# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0008_auto_20150624_2343'),
    ]

    operations = [
        migrations.CreateModel(
            name='Waarnemer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('initialen', models.CharField(max_length=6)),
                ('voornaam', models.CharField(max_length=20, null=True, blank=True)),
                ('achternaam', models.CharField(max_length=40)),
                ('telefoon', models.CharField(blank=True, max_length=16, validators=[django.core.validators.RegexValidator(regex=b'^(?:\\+)?[0-9\\-]{10,11}$', message=b'Ongeldig telefoonnummer')])),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('adres', models.ForeignKey(blank=True, to='iom.Adres', null=True)),
                ('organisatie', models.ForeignKey(blank=True, to='iom.Organisatie', null=True)),
            ],
            options={
                'verbose_name_plural': 'Waarnemers',
            },
        ),
        migrations.RemoveField(
            model_name='eigenaar',
            name='adres',
        ),
        migrations.RemoveField(
            model_name='eigenaar',
            name='organisatie',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='eigenaar',
        ),
        migrations.DeleteModel(
            name='Eigenaar',
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='waarnemer',
            field=models.ForeignKey(default=1, to='iom.Waarnemer'),
            preserve_default=False,
        ),
    ]
