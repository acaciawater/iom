# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0002_auto_20150618_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adres',
            name='postcode',
            field=models.CharField(max_length=7),
        ),
    ]
