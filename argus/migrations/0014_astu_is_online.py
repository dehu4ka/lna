# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-24 07:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus', '0013_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='astu',
            name='is_online',
            field=models.BooleanField(default=False),
        ),
    ]
