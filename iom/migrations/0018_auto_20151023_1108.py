# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0017_auto_20151022_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='waarnemer',
            name='akvoname',
            field=models.CharField(default='akvo', max_length=40, verbose_name=b'Gebruikersnaam op Akvo systeem'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='waarnemer',
            name='initialen',
            field=models.CharField(max_length=6, null=True, blank=True),
        ),
    ]
