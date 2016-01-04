# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0013_meetpunt_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='chart_thumbnail',
            field=models.ImageField(help_text=b'Grafiek in popup op cartodb kaartje', upload_to=b'charts', null=True, verbose_name=b'voorbeeld', blank=True),
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='chart',
            field=models.ForeignKey(blank=True, to='data.Chart', help_text=b'Interactive grafiek', null=True, verbose_name=b'grafiek'),
        ),
    ]
