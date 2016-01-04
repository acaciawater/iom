# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0020_auto_20151023_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='waarneming',
            name='device',
            field=models.CharField(default='akvo', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='waarneming',
            name='naam',
            field=models.CharField(max_length=40),
        ),
    ]
