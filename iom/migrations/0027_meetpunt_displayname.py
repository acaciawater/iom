# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0026_akvoflow_last_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='displayname',
            field=models.CharField(default='displayname', max_length=50),
            preserve_default=False,
        ),
    ]
