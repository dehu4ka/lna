# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 08:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0016_equipmentsuggestcredentials'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='script',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='net.Scripts'),
        ),
    ]
