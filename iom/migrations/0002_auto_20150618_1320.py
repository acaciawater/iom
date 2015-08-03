# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '__first__'),
        ('iom', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meetpunt',
            name='id',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='ident',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='locatie',
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='meetlocatie_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default=1, serialize=False, to='data.MeetLocatie'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='begin',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
