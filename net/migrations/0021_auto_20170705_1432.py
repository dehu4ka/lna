# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-05 09:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus', '0014_astu_is_online'),
        ('net', '0020_job_ne_ids'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='ne',
        ),
        migrations.RemoveField(
            model_name='job',
            name='ne_ids',
        ),
        migrations.AddField(
            model_name='job',
            name='ne_ids',
            field=models.ManyToManyField(to='argus.ASTU'),
        ),
    ]