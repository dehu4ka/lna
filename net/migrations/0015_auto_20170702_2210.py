# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-02 17:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0014_auto_20170701_1539'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='credentials',
            options={'ordering': ('id',)},
        ),
    ]
