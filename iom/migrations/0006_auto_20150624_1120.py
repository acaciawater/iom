# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0005_auto_20150618_1618'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organisatie',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('naam', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('telefoon', phonenumber_field.modelfields.PhoneNumberField(max_length=128, blank=True)),
                ('adres', models.ForeignKey(blank=True, to='iom.Adres', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='eigenaar',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AddField(
            model_name='eigenaar',
            name='telefoon',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, blank=True),
        ),
        migrations.AlterField(
            model_name='eigenaar',
            name='adres',
            field=models.ForeignKey(blank=True, to='iom.Adres', null=True),
        ),
        migrations.AddField(
            model_name='eigenaar',
            name='organisatie',
            field=models.ForeignKey(blank=True, to='iom.Organisatie', null=True),
        ),
    ]
