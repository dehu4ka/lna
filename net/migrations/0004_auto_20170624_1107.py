# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-24 06:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0003_onlinestatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onlinestatus',
            name='astu',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='online_status', serialize=False, to='argus.ASTU'),
        ),
    ]
