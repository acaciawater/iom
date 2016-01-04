# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iom', '0014_auto_20150919_1017'),
    ]

    operations = [
        migrations.CreateModel(
            name='AkvoFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(null=True, blank=True)),
                ('instance', models.CharField(max_length=100)),
                ('key', models.CharField(max_length=100)),
                ('secret', models.CharField(max_length=100)),
                ('storage', models.CharField(max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='begin',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='einde',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='nummer',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='photo',
        ),
        migrations.RemoveField(
            model_name='meetpunt',
            name='watergang',
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='device',
            field=models.CharField(default='default', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='identifier',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetpunt',
            name='submitter',
            field=models.CharField(default='admin', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='meetpunt',
            name='chart_thumbnail',
            field=models.ImageField(help_text=b'Grafiek in popup op cartodb kaartje', upload_to=b'thumbnails/charts', null=True, verbose_name=b'voorbeeld', blank=True),
        ),
        migrations.DeleteModel(
            name='Watergang',
        ),
    ]
