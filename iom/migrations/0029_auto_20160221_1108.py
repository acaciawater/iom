# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0028_auto_20151204_1407'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='alias',
            options={'verbose_name_plural': 'Aliassen'},
        ),
    ]
