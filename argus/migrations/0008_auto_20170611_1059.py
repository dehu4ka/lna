# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-11 05:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('argus', '0007_auto_20170610_1403'),
    ]

    operations = [
        migrations.RenameField(
            model_name='argusadsl',
            old_name='xdsl_port',
            new_name='port',
        ),
        migrations.RenameField(
            model_name='argusadsl',
            old_name='xdsl_slot',
            new_name='slot',
        ),
    ]
