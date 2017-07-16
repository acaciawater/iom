# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0039_auto_20161012_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='ahn',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='identifier',
            field=models.CharField(default=uuid.uuid4, max_length=50),
        ),
    ]
