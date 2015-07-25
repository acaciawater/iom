# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0006_auto_20150624_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisatie',
            name='omschrijving',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='organisatie',
            name='website',
            field=models.URLField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='eigenaar',
            name='telefoon',
            field=models.CharField(blank=True, max_length=16, validators=[django.core.validators.RegexValidator(regex=b'^(?:\\+)?[0-9\\-]{10,11}$', message=b'Ongeldig telefoonnummer')]),
        ),
        migrations.AlterField(
            model_name='organisatie',
            name='telefoon',
            field=models.CharField(blank=True, max_length=16, validators=[django.core.validators.RegexValidator(regex=b'^(?:\\+)?[0-9\\-]{10,11}$', message=b'Ongeldig telefoonnummer')]),
        ),
    ]
