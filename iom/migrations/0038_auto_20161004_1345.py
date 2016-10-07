# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0037_auto_20161004_1147'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartodb',
            name='layer_sql',
        ),
    ]
