# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-21 06:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('net', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.TextField(max_length=10000)),
            ],
        ),
        migrations.CreateModel(
            name='Scripts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(max_length=10000)),
                ('class_name', models.CharField(max_length=255)),
                ('possible_vendor', models.CharField(max_length=255)),
                ('possible_model', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='job',
            name='ne_ip',
            field=models.GenericIPAddressField(default='0.0.0.0', protocol='IPv4'),
        ),
        migrations.AddField(
            model_name='job',
            name='script_name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='jobresult',
            name='job_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='net.Job'),
        ),
    ]