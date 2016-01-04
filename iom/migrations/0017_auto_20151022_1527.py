# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0016_auto_20151022_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='akvoflow',
            name='monforms',
            field=models.CharField(help_text=b'Survey id van monitoringformulier', max_length=100, null=True, verbose_name=b'Monitoringformulier', blank=True),
        ),
        migrations.AlterField(
            model_name='akvoflow',
            name='regform',
            field=models.CharField(help_text=b'Survey id van registratieformulier', max_length=100, null=True, verbose_name=b'Registratieformulier', blank=True),
        ),
    ]
