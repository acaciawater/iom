# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0027_meetpunt_displayname'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('alias', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='waarnemer',
            name='akvoname',
        ),
        migrations.AddField(
            model_name='alias',
            name='waarnemer',
            field=models.ForeignKey(to='iom.Waarnemer'),
        ),
    ]
