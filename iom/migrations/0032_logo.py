# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0031_auto_20160311_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='Logo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(null=True, upload_to=b'logos', blank=True)),
                ('website', models.URLField(null=True, blank=True)),
                ('display', models.BooleanField(default=True)),
            ],
        ),
    ]
