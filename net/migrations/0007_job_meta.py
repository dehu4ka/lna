# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-26 08:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0006_auto_20170626_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='meta',
            field=models.CharField(default='', max_length=1024),
        ),
    ]
