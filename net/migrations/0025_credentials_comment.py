# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-08 06:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0024_scripts_is_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='credentials',
            name='comment',
            field=models.CharField(default='', max_length=512),
        ),
    ]
