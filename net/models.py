from django.db import models
from django.utils import timezone
from argus.models import ASTU
from django.contrib.postgres.fields import JSONField


# Create your models here.

class Scripts(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=10000)
    class_name = models.CharField(max_length=255)
    possible_vendor = models.CharField(max_length=255)
    possible_model = models.CharField(max_length=255)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ('name', )


class Job(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True)
    celery_id = models.CharField(max_length=255)
    script = models.ForeignKey(Scripts, on_delete=models.CASCADE, null=True)
    ne_ids = models.ManyToManyField(ASTU)
    meta = JSONField(default='')

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        return self.name


class JobResult(models.Model):
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)
    result = models.TextField(max_length=10000)


# Login/Pass/Enable credentials
class Credentials(models.Model):
    login = models.CharField(max_length=512, default='')
    passw = models.CharField(max_length=512, default='')
    enable_password = models.CharField(max_length=512, default='')
    snmp_community = models.CharField(max_length=512, default='')
    comment = models.CharField(max_length=512, default='')

    class Meta:
        ordering = ('id', )

    def __str__(self):
        return "Credentials: " + self.login + " / " + self.passw


# proven-info model class
class Equipment(models.Model):
    hostname = models.CharField(max_length=512, default='', null=True)
    vendor = models.CharField(max_length=512, default='', null=True)
    model = models.CharField(max_length=512, default='', null=True)
    ne_ip = models.GenericIPAddressField(protocol='IPv4', db_index=True, unique=True)
    credentials = models.ForeignKey(Credentials, on_delete=models.CASCADE, null=True)


class EquipmentSuggestCredentials(models.Model):
    equipment_id = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)  # Equipment foreign key
    credentials_id = models.ForeignKey(Credentials, on_delete=models.CASCADE, null=True)  # Credentials FK
    # True if was unsuccessful attempt to login equipment with provided credentials
    was_checked = models.BooleanField(default=False)

    class Meta:
        ordering = ('equipment_id', )

