# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0025_auto_20151103_2348'),
    ]

    operations = [
        migrations.AddField(
            model_name='akvoflow',
            name='last_update',
            field=models.DateTimeField(null=True),
        ),
    ]
