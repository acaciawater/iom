# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0033_auto_20160502_0957'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegisteredUser',
            fields=[
                ('waarnemer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='iom.Waarnemer')),
                ('website', models.CharField(max_length=100)),
                ('akvo_name', models.CharField(max_length=100)),
                ('device_id', models.CharField(max_length=100)),
                ('status', models.CharField(max_length=1, choices=[(b'O', b'geopend'), (b'V', b'aangevraagd'), (b'P', b'in behandeling'), (b'E', b'fout geconstateerd'), (b'R', b'geweigerd'), (b'A', b'geaccepteerd')])),
            ],
            bases=('iom.waarnemer',),
        ),
    ]
