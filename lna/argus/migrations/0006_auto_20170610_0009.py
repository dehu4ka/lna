# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-09 19:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus', '0005_auto_20170609_2353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='argusadsl',
            name='xdsl_port',
            field=models.CharField(default='N/A', max_length=512),
        ),
    ]
