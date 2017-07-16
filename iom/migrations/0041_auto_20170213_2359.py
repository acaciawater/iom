# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0040_auto_20170213_2342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meetpunt',
            name='ahn',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=1, blank=True),
        ),
    ]
