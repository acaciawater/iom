# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0030_cartodb_datatable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meetpunt',
            name='displayname',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='waarneming',
            name='naam',
            field=models.CharField(max_length=100),
        ),
    ]
