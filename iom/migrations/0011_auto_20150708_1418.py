# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0010_userprofile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='waarnemer',
            options={'ordering': ['achternaam'], 'verbose_name_plural': 'Waarnemers'},
        ),
        migrations.RemoveField(
            model_name='waarnemer',
            name='adres',
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='chart',
            field=models.ImageField(default=1, help_text=b'Grafiek in popup op cartodb kaartje', verbose_name=b'grafiek', upload_to=b'charts'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='waarnemer',
            name='tussenvoegsel',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
