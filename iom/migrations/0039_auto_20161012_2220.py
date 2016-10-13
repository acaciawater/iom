# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0038_auto_20161004_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='akvoflow',
            name='projectlocatie',
            field=models.ForeignKey(to='data.ProjectLocatie'),
        ),
    ]
