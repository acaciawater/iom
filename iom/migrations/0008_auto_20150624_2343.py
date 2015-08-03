# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0007_auto_20150624_1254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisatie',
            name='website',
            field=models.URLField(blank=True),
        ),
    ]
