# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0032_logo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='logo',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='logo',
            name='order',
            field=models.IntegerField(default=1),
        ),
    ]
