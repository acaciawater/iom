# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0012_meetpunt_nummer'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetpunt',
            name='photo',
            field=models.ImageField(help_text=b'Foto van meetpunt', upload_to=b'images', null=True, verbose_name=b'foto', blank=True),
        ),
    ]
