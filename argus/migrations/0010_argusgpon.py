# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-12 13:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus', '0009_argusfttx'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArgusGPON',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(default='N/A', max_length=512)),
                ('hostname', models.CharField(default='None', max_length=512)),
                ('ne_ip', models.GenericIPAddressField(default='0.0.0.0', protocol='IPv4')),
                ('tel_num', models.CharField(db_index=True, default='', max_length=16)),
                ('address', models.CharField(default='N/A', max_length=512)),
                ('fio', models.CharField(default='N/A', max_length=512)),
                ('room', models.CharField(default='N/A', max_length=512)),
                ('iptv_login', models.CharField(db_index=True, max_length=512)),
                ('inet_login', models.CharField(db_index=True, max_length=512)),
                ('slot', models.CharField(default='N/A', max_length=512)),
                ('port', models.CharField(default='N/A', max_length=512)),
                ('lira', models.CharField(default='N/A', max_length=32)),
            ],
        ),
    ]
