# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0015_auto_20151022_1409'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='akvoflow',
            options={'verbose_name': 'Akvoflow API toegang', 'verbose_name_plural': 'Akvoflow API toegang'},
        ),
        migrations.AddField(
            model_name='akvoflow',
            name='monforms',
            field=models.TextField(help_text=b'Survey id van monitoringformulier', null=True, verbose_name=b'Monitoringformulier', blank=True),
        ),
        migrations.AddField(
            model_name='akvoflow',
            name='regform',
            field=models.TextField(help_text=b'Survey id van registratieformulier', null=True, verbose_name=b'Registratieformulier', blank=True),
        ),
#         migrations.AlterField(
#             model_name='meetpunt',
#             name='identifier',
#             field=models.CharField(unique=True, max_length=50),
#         ),
    ]
