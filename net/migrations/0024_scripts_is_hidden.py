# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-06 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0023_auto_20170706_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='scripts',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
    ]
